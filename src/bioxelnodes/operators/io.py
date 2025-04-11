import math
import bpy
import shutil
import threading
import numpy as np
from pathlib import Path


from ..exceptions import CancelledByUser
from ..props import BIOXELNODES_Series
from ..bioxelutils.node import add_node_to_graph
from ..bioxelutils.common import (get_all_layer_objs, get_container_obj,
                                  get_layer_obj, get_nodes_by_type, get_output_node, is_incompatible, move_node_to_node)
from ..bioxelutils.container import (Container,
                                     add_layers,
                                     container_to_obj)
from ..bioxel.layer import Layer
from ..bioxel.parse import (DICOM_EXTS, SUPPORT_EXTS,
                            get_ext, parse_volumetric_data)

from ..utils import (get_cache_dir, get_use_link,
                     progress_update, progress_bar,
                     select_object)

# 3rd-party
import SimpleITK as sitk
import transforms3d


def get_layer_shape(bioxel_size: float, orig_shape: tuple, orig_spacing: tuple):
    shape = (int(orig_shape[0] / bioxel_size * orig_spacing[0]),
             int(orig_shape[1] / bioxel_size * orig_spacing[1]),
             int(orig_shape[2] / bioxel_size * orig_spacing[2]))

    return (shape[0] if shape[0] > 0 else 1,
            shape[1] if shape[1] > 0 else 1,
            shape[2] if shape[2] > 0 else 1)


def get_layer_size(shape: tuple, bioxel_size: float, scale: float = 1.0):
    size = (float(shape[0] * bioxel_size * scale),
            float(shape[1] * bioxel_size * scale),
            float(shape[2] * bioxel_size * scale))

    return size


"""
ImportVolumetricData
                        -> ParseVolumetricData -> ImportVolumetricDataDialog
FH_ImportVolumetricData

 start import                  parse data               execute import
"""


class ImportVolumetricData():
    bl_options = {'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # type: ignore

    read_as = "SCALAR"

    def execute(self, context):
        data_path = Path(self.filepath).resolve()
        ext = get_ext(data_path)
        if ext not in SUPPORT_EXTS:
            self.report({"WARNING"}, "Not supported format.")
            return {'CANCELLED'}

        bpy.ops.bioxelnodes.parse_volumetric_data('INVOKE_DEFAULT',
                                                  filepath=self.filepath,
                                                  skip_read_as=True,
                                                  read_as=self.read_as)

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class ImportAsScalar(bpy.types.Operator, ImportVolumetricData):
    bl_idname = "bioxelnodes.import_as_scalar"
    bl_label = "Import as Scalar"
    bl_description = "Import Volumetric Data to Container as Scalar"
    bl_icon = "EVENT_S"
    read_as = "SCALAR"


class ImportAsLabel(bpy.types.Operator, ImportVolumetricData):
    bl_idname = "bioxelnodes.import_as_label"
    bl_label = "Import as Label"
    bl_description = "Import Volumetric Data to Container as Label"
    bl_icon = "EVENT_L"
    read_as = "LABEL"


class ImportAsColor(bpy.types.Operator, ImportVolumetricData):
    bl_idname = "bioxelnodes.import_as_color"
    bl_label = "Import as Color"
    bl_description = "Import Volumetric Data to Container as Color"
    bl_icon = "EVENT_C"
    read_as = "COLOR"


class BIOXELNODES_FH_ImportVolumetricData(bpy.types.FileHandler):
    bl_idname = "BIOXELNODES_FH_ImportVolumetricData"
    bl_label = "File handler for dicom import"
    bl_import_operator = "bioxelnodes.parse_volumetric_data"
    bl_file_extensions = ";".join(SUPPORT_EXTS)

    @classmethod
    def poll_drop(cls, context):
        if not context.area:
            return False

        if context.area.type == 'VIEW_3D':
            return True
        elif context.area.type == 'NODE_EDITOR':
            container_obj = get_container_obj(context.object)
            return container_obj is not None
        else:
            return False


def get_series_ids(self, context):
    items = []
    for index, series_id in enumerate(self.series_ids):
        items.append((
            series_id.id,
            series_id.label,
            "",
            index
        ))

    return items


class ParseVolumetricData(bpy.types.Operator):
    bl_idname = "bioxelnodes.parse_volumetric_data"
    bl_label = "Import Volumetric Data (BioxelNodes)"
    bl_description = "Import Volumetric Data as Layer"
    bl_options = {'UNDO'}

    meta = None
    label_count = 0
    dtype = None
    thread = None
    _timer = None

    progress: bpy.props.FloatProperty(name="Progress",
                                      options={"SKIP_SAVE"},
                                      default=1)  # type: ignore

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # type: ignore

    skip_read_as: bpy.props.BoolProperty(name="Skip Read As",
                                         default=False,
                                         options={"SKIP_SAVE"})  # type: ignore

    skip_series_select: bpy.props.BoolProperty(name="Skip Sries Select",
                                               default=True,
                                               options={"SKIP_SAVE"})  # type: ignore

    read_as: bpy.props.EnumProperty(name="Read as",
                                    default="SCALAR",
                                    items=[("SCALAR", "Scalar", ""),
                                           ("LABEL", "Label", ""),
                                           ("COLOR", "Color", "")])  # type: ignore

    series_id: bpy.props.EnumProperty(name="Select Series",
                                      items=get_series_ids)  # type: ignore

    series_ids: bpy.props.CollectionProperty(
        type=BIOXELNODES_Series)  # type: ignore

    def execute(self, context):
        if is_incompatible():
            self.report({"ERROR"},
                        "Current addon verison is not compatible to this file. If you insist on editing this file please keep the same addon version")
            return {'CANCELLED'}

        if not self.filepath:
            self.report({"WARNING"}, "No file selected.")
            return {'CANCELLED'}

        data_path = Path(self.filepath).resolve()
        ext = get_ext(data_path)
        if ext not in SUPPORT_EXTS:
            self.report({"WARNING"}, "Not supported format.")
            return {'CANCELLED'}

        print("Collecting Meta Data...")

        def parse_volumetric_data_func(self, context, cancel):
            def progress_callback(factor, text):
                if cancel():
                    raise CancelledByUser
                progress_update(context, factor, text)

            try:
                series_id = self.series_id if self.series_id != "empty" else ""
                data, meta = parse_volumetric_data(data_file=self.filepath,
                                                   series_id=series_id,
                                                   progress_callback=progress_callback)
            except CancelledByUser:
                return
            except Exception as e:
                self.has_error = e
                return

            if cancel():
                return

            self.meta = meta
            self.label_count = int(np.max(data))
            self.dtype = data.dtype

        # Init cancel flag
        self.is_cancelled = False
        self.has_error = None

        # Create the thread
        self.thread = threading.Thread(target=parse_volumetric_data_func,
                                       args=(self, context, lambda: self.is_cancelled))

        # Start the thread
        self.thread.start()
        # Add a timmer for modal
        self._timer = context.window_manager.event_timer_add(time_step=0.1,
                                                             window=context.window)
        # Append progress bar to status bar
        bpy.types.STATUSBAR_HT_header.append(progress_bar)

        # Start modal handler
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        # Check if user press 'ESC'
        if event.type == 'ESC':
            self.is_cancelled = True
            progress_update(context, 0.0, "Canceling...")
            return {'PASS_THROUGH'}

        # Check if is the timer time
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        # Force update status bar
        bpy.context.workspace.status_text_set_internal(None)

        # Check if thread is still running
        if self.thread.is_alive():
            return {'PASS_THROUGH'}

        # Release the thread
        self.thread.join()
        # Remove the timer
        context.window_manager.event_timer_remove(self._timer)
        # Remove the progress bar from status bar
        bpy.types.STATUSBAR_HT_header.remove(progress_bar)
        progress_update(context, 1.0)

        # Check if thread is cancelled by user
        if self.is_cancelled:
            self.report({"WARNING"}, "Canncelled by user.")
            return {'CANCELLED'}

        # Check if thread is cancelled by user
        if self.has_error:
            raise self.has_error

        # Check if has return
        if self.meta is None:
            self.report({"ERROR"}, "Some thing went wrong.")
            return {'CANCELLED'}

        # If not canncelled...
        for key, value in self.meta.items():
            print(f"{key}: {value}")

        if self.read_as == "LABEL":
            if self.label_count > 100 or self.dtype.kind not in ["i", "u"]:
                self.report({"ERROR"}, "Invaild label data.")
                return {'CANCELLED'}

            if self.label_count == 0:
                self.report({"ERROR"}, "Get no label.")
                return {'CANCELLED'}

        orig_shape = self.meta['xyz_shape']
        orig_spacing = self.meta['spacing']

        min_log10 = math.floor(math.log10(min(*orig_spacing)))
        max_log10 = math.floor(math.log10(max(*orig_spacing)))
        # min_space = min(*orig_spacing)
        # max_space = max(*orig_spacing)

        if orig_spacing[2] == 1 and min_log10 < -1:
            orig_spacing = (orig_spacing[0] * math.pow(10, -min_log10-2),
                            orig_spacing[1] * math.pow(10, -min_log10-2),
                            1)
        elif min_log10 > 0:
            orig_spacing = (orig_spacing[0] * math.pow(10, -min_log10-1),
                            orig_spacing[1] * math.pow(10, -min_log10-1),
                            orig_spacing[2] * math.pow(10, -min_log10-1))
        elif max_log10 < 0:
            orig_spacing = (orig_spacing[0] * math.pow(10, -max_log10-1),
                            orig_spacing[1] * math.pow(10, -max_log10-1),
                            orig_spacing[2] * math.pow(10, -max_log10-1))

        bioxel_size = max(min(*orig_spacing), 1.0)

        layer_shape = get_layer_shape(bioxel_size,
                                      orig_shape,
                                      orig_spacing)
        layer_size = get_layer_size(layer_shape,
                                    bioxel_size,
                                    0.01)
        min_log10 = math.floor(math.log10(min(*layer_size)))
        max_log10 = math.floor(math.log10(max(*layer_size)))

        if min_log10 > 0:
            scene_scale = math.pow(10, -min_log10-2)
        elif max_log10 < 0:
            scene_scale = math.pow(10, -max_log10-2)
        else:
            scene_scale = 0.01

        if context.area.type == "NODE_EDITOR":
            container_obj = context.object
            container_name = container_obj.name
            container_obj_name = container_name
        else:
            container_name = self.meta['name']
            container_obj_name = ""

        series_id = self.series_id if self.series_id != "empty" else ""
        bpy.ops.bioxelnodes.import_volumetric_data_dialog(
            'INVOKE_DEFAULT',
            filepath=self.filepath,
            container_name=container_name,
            layer_name=self.meta['description'],
            orig_shape=orig_shape,
            orig_spacing=orig_spacing,
            bioxel_size=bioxel_size,
            series_id=series_id,
            frame_count=self.meta['frame_count'],
            channel_count=self.meta['channel_count'],
            container_obj_name=container_obj_name,
            read_as=self.read_as,
            label_count=self.label_count,
            scene_scale=scene_scale
        )

        self.report({"INFO"}, "Successfully Readed.")
        return {'FINISHED'}

    def invoke(self, context, event):
        # why not report in execute?
        # If this operator is executing, a new execute will when pre-one done.
        if context.window_manager.bioxelnodes_progress_factor < 1:
            print("A process is executing, please wait for it to finish.")
            return {'CANCELLED'}

        if not self.filepath:
            return self.execute(context)

        data_path = Path(self.filepath).resolve()
        ext = get_ext(data_path)

        if context.area.type == "NODE_EDITOR":
            title = f"Add to **{context.object.name}**"
        else:
            title = "Init a Container"

        # Series Selection
        if ext in DICOM_EXTS:
            data_dirpath = data_path.parent
            reader = sitk.ImageSeriesReader()
            reader.MetaDataDictionaryArrayUpdateOn()
            reader.LoadPrivateTagsOn()

            series_ids = reader.GetGDCMSeriesIDs(str(data_dirpath))
            series_items = {}

            for series_id in series_ids:
                series_files = reader.GetGDCMSeriesFileNames(
                    str(data_dirpath), series_id)
                single = sitk.ImageFileReader()
                single.SetFileName(series_files[0])
                single.LoadPrivateTagsOn()
                single.ReadImageInformation()

                def get_meta(key):
                    try:
                        stirng = single.GetMetaData(key).removesuffix(" ")
                        stirng.encode('utf-8')
                        if stirng in ["No study description",
                                      "No series description",
                                      ""]:
                            return "Unknown"
                        else:
                            return stirng
                    except:
                        return "Unknown"

                study_description = get_meta("0008|1030")
                series_description = get_meta("0008|103e")
                series_modality = get_meta("0008|0060")
                size_x = get_meta("0028|0011")
                size_y = get_meta("0028|0010")
                count = get_meta("0020|0013")
                count = count if count != "Unknown" else 1

                # some series image count = 0 ????
                if int(count) == 0:
                    continue

                # series_id cannot be "" in blender selection
                if series_id == "":
                    series_id = "empty"

                label = "{:<20} {:>1}".format(f"{study_description}>{series_description}({series_modality})",
                                              f"({size_x}x{size_y})x{count}")

                series_items[series_id] = label

            for series_id, label in series_items.items():
                series_item = self.series_ids.add()
                series_item.id = series_id
                series_item.label = label

            if len(series_items.keys()) > 1:
                self.skip_series_select = False
                context.window_manager.invoke_props_dialog(self,
                                                           width=400,
                                                           title=title)
                return {'RUNNING_MODAL'}
            elif len(series_items.keys()) == 1:
                self.series_id = list(series_items.keys())[0]
            else:
                self.report({"ERROR"}, "Get no vaild series.")
                return {'CANCELLED'}

        if self.skip_read_as:
            return self.execute(context)
        else:
            context.window_manager.invoke_props_dialog(self,
                                                       width=400,
                                                       title=title)
            return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        if not self.skip_read_as:
            layout.label(
                text='What kind is the data read as?')
            layout.prop(self, "read_as")
        if not self.skip_series_select:
            layout.label(text='Which series to import?')
            layout.prop(self, "series_id")


def get_frame_sources(self, context):
    items = [("-1", "First Frame (1 frame)", "")]
    orig_shape = tuple(self.orig_shape)
    if self.frame_count > 1:
        items.append(("0", f"Frames ({self.frame_count} frames)", ""))
    elif self.frame_count == 1 and self.channel_count > 1:
        items.append(("4", f"Channels ({self.channel_count} frames)", ""))
    elif self.frame_count == 1 and self.channel_count == 1:
        items.append(("1", f"X-axis ({orig_shape[0]} frames)", ""))
        items.append(("2", f"Y-axis ({orig_shape[1]} frames)", ""))
        items.append(("3", f"Z-axis ({orig_shape[2]} frames)", ""))

    return items


class ImportVolumetricDataDialog(bpy.types.Operator):
    bl_idname = "bioxelnodes.import_volumetric_data_dialog"
    bl_label = "Import Volumetric Data"
    bl_description = "Import Volumetric Data as Layer"
    bl_options = {'UNDO'}

    layers = None
    thread = None
    _timer = None

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # type: ignore

    container_name: bpy.props.StringProperty(
        name="Container Name")   # type: ignore

    layer_name: bpy.props.StringProperty(name="Layer Name")   # type: ignore

    series_id: bpy.props.StringProperty()   # type: ignore

    container_obj_name: bpy.props.StringProperty()   # type: ignore

    frame_count: bpy.props.IntProperty()  # type: ignore

    channel_count: bpy.props.IntProperty()  # type: ignore

    label_count: bpy.props.IntProperty()  # type: ignore

    smooth: bpy.props.IntProperty(name="Smooth Size (Larger takes longer time)",
                                  default=0)  # type: ignore

    read_as: bpy.props.EnumProperty(name="Read as",
                                    default="SCALAR",
                                    items=[("SCALAR", "Scalar", ""),
                                           ("LABEL", "Label", ""),
                                           ("COLOR", "Color", "")])  # type: ignore

    bioxel_size: bpy.props.FloatProperty(name="Bioxel Size (Larger size means small resolution)",
                                         soft_min=0.1, soft_max=10.0,
                                         min=0.1, max=1e2,
                                         default=1)  # type: ignore

    orig_spacing: bpy.props.FloatVectorProperty(name="Original Spacing",
                                                default=(1, 1, 1))  # type: ignore

    orig_shape: bpy.props.IntVectorProperty(name="Original Shape",
                                            default=(100, 100, 100))  # type: ignore

    scene_scale: bpy.props.FloatProperty(name="Scene Scale (Bioxel Unit pre Blender Unit)",
                                         soft_min=0.0001, soft_max=10.0,
                                         min=1e-6, max=1e6,
                                         default=0.01)  # type: ignore

    remap: bpy.props.BoolProperty(name="Remap to 0~1",
                                  default=False)  # type: ignore

    split_channel: bpy.props.BoolProperty(name="Split Channels",
                                          default=False)  # type: ignore

    frame_source: bpy.props.EnumProperty(name="Frame From",
                                         items=get_frame_sources)  # type: ignore

    def execute(self, context):
        def import_volumetric_data_func(self, context, cancel):
            progress_update(context, 0.0, "Parsing Volumetirc Data...")

            def progress_callback(factor, text):
                if cancel():
                    raise CancelledByUser
                progress_update(context, factor*0.2, text)

            try:
                data, meta = parse_volumetric_data(data_file=self.filepath,
                                                   series_id=self.series_id,
                                                   progress_callback=progress_callback)
            except CancelledByUser:
                return
            except Exception as e:
                self.has_error = e
                return

            if cancel():
                return

            shape = get_layer_shape(self.bioxel_size,
                                    self.orig_shape,
                                    self.orig_spacing)

            mat_scale = transforms3d.zooms.zfdir2aff(self.bioxel_size)
            affine = np.dot(meta['affine'], mat_scale)
            kind = self.read_as.lower()

            if cancel():
                return

            # change shape as sequence or not
            if self.frame_source == "-1":
                data = data[0:1, :, :, :, :]
            elif self.frame_source == "0":
                # frame as frame
                pass
            elif self.frame_source == "1":
                # X as frame
                data = data.transpose(1, 0, 2, 3, 4)
                shape = (1, shape[1], shape[2])
            elif self.frame_source == "2":
                # Y as frame
                data = data.transpose(2, 1, 0, 3, 4)
                shape = (shape[0], 1, shape[2])
            elif self.frame_source == "3":
                # Z as frame
                data = data.transpose(3, 1, 2, 0, 4)
                shape = (shape[0], shape[1], 1)
            else:
                # channel as frame
                data = data.transpose(4, 1, 2, 3, 0)

            def progress_callback_factory(layer_name, progress, progress_step):
                def progress_callback(frame, total):
                    if cancel():
                        raise CancelledByUser
                    sub_progress_step = progress_step/total
                    sub_progress = progress + frame * sub_progress_step
                    progress_update(context, sub_progress,
                                    f"Processing {layer_name} Frame {frame+1}...")
                    print(f"Processing {layer_name} Frame {frame+1}...")
                return progress_callback

            layers = []
            if kind == "label":
                name = self.layer_name or "Label"
                data = data.astype(int)
                label_count = int(np.max(data))
                progress_step = 0.7/label_count

                for i in range(label_count):
                    if cancel():
                        return

                    name_i = f"{name}_{i+1}"
                    progress = 0.2+i*progress_step
                    progress_update(context, progress,
                                    f"Processing {name_i}...")

                    progress_callback = progress_callback_factory(name_i,
                                                                  progress,
                                                                  progress_step)
                    label_data = data == np.full_like(data, i+1)
                    # label_data = label_data.astype(np.float32)
                    try:
                        layer = Layer(data=label_data,
                                      name=name_i,
                                      kind=kind)

                        layer.resize(shape=shape,
                                     smooth=self.smooth,
                                     progress_callback=progress_callback)

                        layer.affine = affine

                        layers.append(layer)
                    except CancelledByUser:
                        return
                    except Exception as e:
                        self.has_error = e
                        return

            if kind == "color":
                if np.issubdtype(np.uint8, data.dtype):
                    data = np.multiply(data, 1.0 / 256,
                                       dtype=np.float32)
                elif data.dtype.kind in ['u', 'i']:
                    # Convert the normalized array to float dtype
                    data = data.astype(np.float32)

                    min_val = data.min()
                    max_val = data.max()
                    # Avoid division by zero if all values are the same
                    if max_val != min_val:
                        # Normalize the array to the range (0,1)
                        data = (data - min_val) / (max_val - min_val)
                    else:
                        # If all values are the same, the normalized array will be all zeros
                        data = np.zeros_like(data, dtype=np.float32)

                else:
                    data = data.astype(np.float32)

                # Gamma Correct
                # data = data ** 2.2

                name = self.layer_name or "Color"
                if data.shape[4] == 1:
                    data = np.repeat(data, repeats=3, axis=4)
                elif data.shape[4] == 2:
                    d_shape = list(data.shape)
                    d_shape = d_shape[:4] + [1]
                    zore = np.zeros(tuple(d_shape), dtype=np.float32)
                    data = np.concatenate((data, zore), axis=-1)
                elif data.shape[4] > 3:
                    data = data[:, :, :, :, :3]

                if cancel():
                    return

                progress_update(context, 0.2,
                                f"Processing {name}...")
                progress_callback = progress_callback_factory(name,
                                                              0.2,
                                                              0.7)

                try:
                    layer = Layer(data=data,
                                  name=name,
                                  kind=kind)

                    layer.resize(shape=shape,
                                 progress_callback=progress_callback)

                    layer.affine = affine

                    layers.append(layer)
                except CancelledByUser:
                    return
                except Exception as e:
                    self.has_error = e
                    return

            elif kind == "scalar":
                name = self.layer_name or "Scalar"

                if self.remap:
                    # Convert the normalized array to float dtype
                    data = data.astype(np.float32)

                    min_val = data.min()
                    max_val = data.max()
                    # Avoid division by zero if all values are the same
                    if max_val != min_val:
                        # Normalize the array to the range (0,1)
                        data = (data - min_val) / (max_val - min_val)
                    else:
                        # If all values are the same, the normalized array will be all zeros
                        data = np.zeros_like(data, dtype=np.float32)

                if self.split_channel:
                    progress_step = 0.7/self.channel_count

                    for i in range(self.channel_count):
                        if cancel():
                            return

                        name_i = f"{name}_{i+1}"
                        progress = 0.2 + i*progress_step
                        progress_update(context, progress,
                                        f"Processing {name_i}...")
                        progress_callback = progress_callback_factory(name_i,
                                                                      progress,
                                                                      progress_step)
                        try:
                            layer = Layer(data=data[:, :, :, :, i:i+1],
                                          name=name_i,
                                          kind=kind)

                            layer.resize(shape=shape,
                                         progress_callback=progress_callback)

                            layer.affine = affine

                            layers.append(layer)
                        except CancelledByUser:
                            return
                        except Exception as e:
                            self.has_error = e
                            return
                else:
                    if cancel():
                        return

                    progress_update(context, 0.2,
                                    f"Processing {name}...")
                    progress_callback = progress_callback_factory(name,
                                                                  0.2,
                                                                  0.7)

                    try:
                        layer = Layer(data=data,
                                      name=name,
                                      kind=kind)

                        layer.resize(shape=shape,
                                     progress_callback=progress_callback)

                        layer.affine = affine

                        layers.append(layer)
                    except CancelledByUser:
                        return
                    except Exception as e:
                        self.has_error = e
                        return

            if cancel():
                return

            self.layers = layers
            progress_update(context, 0.9, "Creating Layers...")

        self.is_cancelled = False
        self.has_error = None

        self.thread = threading.Thread(target=import_volumetric_data_func,
                                       args=(self, context, lambda: self.is_cancelled))

        self.thread.start()
        self._timer = context.window_manager.event_timer_add(time_step=0.1,
                                                             window=context.window)
        bpy.types.STATUSBAR_HT_header.append(progress_bar)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'ESC':
            self.is_cancelled = True
            progress_update(context, 0.0, "Canceling...")
            return {'PASS_THROUGH'}

        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        bpy.context.workspace.status_text_set_internal(None)
        if self.thread.is_alive():
            return {'PASS_THROUGH'}

        self.thread.join()
        context.window_manager.event_timer_remove(self._timer)
        bpy.types.STATUSBAR_HT_header.remove(progress_bar)
        progress_update(context, 1.0)

        if self.is_cancelled:
            self.report({"WARNING"}, "Canncelled by user.")
            return {'CANCELLED'}

        # Check if thread is cancelled by user
        if self.has_error:
            raise self.has_error

        # Check if has return
        if self.layers is None:
            self.report({"ERROR"}, "Some thing went wrong.")
            return {'CANCELLED'}

        is_first_import = len(get_all_layer_objs()) == 0

        if self.container_obj_name:
            container_obj = bpy.data.objects.get(self.container_obj_name)
            if container_obj is None:
                raise Exception("Could not find target container")

            container_obj = add_layers(self.layers,
                                       container_obj=container_obj,
                                       cache_dir=get_cache_dir())
        else:
            name = self.container_name or "Container"
            container = Container(name=name,
                                  layers=self.layers)

            step_size = container.layers[0].bioxel_size[0]*10
            container_obj = container_to_obj(container,
                                             scene_scale=self.scene_scale,
                                             step_size=step_size,
                                             cache_dir=get_cache_dir())

        select_object(container_obj)

        # Change render setting for better result
        if is_first_import:
            try:

                node_group = container_obj.modifiers[0].node_group
                layer_node = get_nodes_by_type(
                    node_group, "BioxelNodes_FetchLayer")[0]
                center_node = add_node_to_graph("ReCenter",
                                                node_group,
                                                use_link=get_use_link())

                output_node = get_output_node(node_group)

                node_group.links.new(layer_node.outputs[0],
                                     center_node.inputs[0])
                node_group.links.new(center_node.outputs[0],
                                     output_node.inputs[0])

                move_node_to_node(center_node, layer_node, (300, 0))
                bpy.ops.bioxelnodes.add_slicer('EXEC_DEFAULT')
            except:
                self.report({"WARNING"}, "Fail to create slicer.")

            try:
                bpy.ops.bioxelnodes.render_setting_preset('EXEC_DEFAULT',
                                                          preset="balance")
                bpy.ops.bioxelnodes.add_eevee_env('EXEC_DEFAULT')
                bpy.context.scene.eevee.use_taa_reprojection = False
                bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'

                view_3d = None
                if context.area.type == 'VIEW_3D':
                    view_3d = context.area
                else:
                    for area in context.screen.areas:
                        if area.type == 'VIEW_3D':
                            view_3d = area
                            break
                if view_3d:
                    view_3d.spaces[0].shading.type = 'RENDERED'
            except:
                self.report({"WARNING"}, "Fail to change render setting.")

        self.report({"INFO"}, "Successfully Imported")
        return {'FINISHED'}

    def invoke(self, context, event):
        layer_kind = self.read_as.capitalize()
        title = f"Add to **{self.container_obj_name}**, As {layer_kind}" \
            if self.container_obj_name != "" else f"Init a Container, As {layer_kind}"
        context.window_manager.invoke_props_dialog(self,
                                                   width=500,
                                                   title=title)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layer_shape = get_layer_shape(self.bioxel_size,
                                      self.orig_shape,
                                      self.orig_spacing)

        orig_shape = tuple(self.orig_shape)

        # change shape as sequence or not
        channel_count = self.channel_count
        frame_count = self.frame_count
        if self.frame_source == "-1":
            frame_count = 1
            pass
        elif self.frame_source == "0":
            # frame as frame
            pass
        elif self.frame_source == "1":
            frame_count = orig_shape[0]
            layer_shape = (1, layer_shape[1], layer_shape[2])
        elif self.frame_source == "2":
            frame_count = orig_shape[1]
            layer_shape = (layer_shape[0], 1, layer_shape[2])
        elif self.frame_source == "3":
            frame_count = orig_shape[2]
            layer_shape = (layer_shape[0], layer_shape[1], 1)
        else:
            channel_count = 1

        if self.read_as == "SCALAR":
            layer_count = channel_count if self.split_channel else 1
            channel_count = 1
        elif self.read_as == "LABEL":
            layer_count = self.label_count
            channel_count = 1
        else:
            layer_count = 1
            channel_count = 3

        bioxel_count = layer_shape[0] * layer_shape[1] * layer_shape[2]
        orig_shape_text = f"[{self.frame_count}, ({orig_shape[0]},{orig_shape[1]},{orig_shape[2]}), {self.channel_count}]"
        layer_shape_text = f"{layer_count} x [{frame_count}, ({layer_shape[0]},{layer_shape[1]},{layer_shape[2]}), {channel_count}]"

        if bioxel_count > 100000000:
            layer_shape_text += "**TOO LARGE!**"

        layer_size = get_layer_size(layer_shape,
                                    self.bioxel_size,
                                    self.scene_scale)
        layer_size_text = f"Size will be: ({layer_size[0]:.2f}, {layer_size[1]:.2f}, {layer_size[2]:.2f}) m"

        layout = self.layout
        if self.container_obj_name == "":
            panel = layout.box()
            panel.prop(self, "container_name")
            panel.prop(self, "scene_scale")
            panel.label(text=layer_size_text)

        panel = layout.box()
        panel.prop(self, "layer_name")
        panel.prop(self, "bioxel_size")
        row = panel.row()
        row.prop(self, "orig_spacing")
        panel.prop(self, "frame_source")

        if self.read_as == "SCALAR":
            panel.prop(self, "split_channel",
                       text=f"Split Channel as Multi Layer")
        elif self.read_as == "LABEL":
            panel.prop(self, "smooth")

        panel.label(
            text="Dimension Order: [Frame, (X-axis,Y-axis,Z-axis), Channel]")
        panel.label(
            text=f"Shape from {orig_shape_text} to {layer_shape_text}")


class ExportVolumetricData(bpy.types.Operator):
    bl_idname = "bioxelnodes.export_volumetric_data"
    bl_label = "Export Layer as VDB"
    bl_description = "Export Layer as VDB"
    bl_options = {'UNDO'}

    filepath: bpy.props.StringProperty(
        subtype="FILE_PATH"
    )  # type: ignore

    filename_ext = ".vdb"

    @classmethod
    def poll(cls, context):
        layer_obj = get_layer_obj(bpy.context.active_object)
        return True if layer_obj else False

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        layer_obj = get_layer_obj(bpy.context.active_object)

        filepath = f"{self.filepath.split('.')[0]}.vdb"
        # "//"
        source_dir = bpy.path.abspath(layer_obj.data.filepath)

        output_path: Path = Path(filepath).resolve()
        source_path: Path = Path(source_dir).resolve()
        # print('output_path', output_path)
        # print('source_path', source_path)
        shutil.copy(source_path, output_path)

        self.report({"INFO"}, f"Successfully exported to {output_path}")

        return {'FINISHED'}
