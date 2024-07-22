import math
import bpy
import shutil
import threading


from bpy_extras.io_utils import axis_conversion
import pyopenvdb as vdb
import numpy as np
from pathlib import Path
import mathutils
import random

from . import skimage as ski
from .nodes import custom_nodes
from .exceptions import CancelledByUser
from .props import BIOXELNODES_Series
from .parse import DICOM_EXTS, FH_EXTS, SUPPORT_EXTS, get_ext, parse_volumetric_data
from .utils import (calc_bbox_verts, get_all_layers, get_container_from_selection, get_layer,
                    get_nodes_by_type, hide_in_ray, lock_transform, move_node_between_nodes, move_node_to_node, progress_update, progress_bar, save_vdb, save_vdbs, select_object)


try:
    import SimpleITK as sitk
except:
    ...


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
    directory: bpy.props.StringProperty(subtype='DIR_PATH')  # type: ignore

    read_as = "scalar"

    def execute(self, context):
        containers = get_container_from_selection()

        if len(containers) > 0:
            bpy.ops.bioxelnodes.parse_volumetric_data('INVOKE_DEFAULT',
                                                      filepath=self.filepath,
                                                      directory=self.directory,
                                                      container=containers[0].name,
                                                      read_as=self.read_as)
        else:
            bpy.ops.bioxelnodes.parse_volumetric_data('INVOKE_DEFAULT',
                                                      filepath=self.filepath,
                                                      directory=self.directory,
                                                      read_as=self.read_as)

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class ImportAsScalarLayer(bpy.types.Operator, ImportVolumetricData):
    bl_idname = "bioxelnodes.import_as_scalar_layer"
    bl_label = "Import as Scalar"
    bl_description = "Import Volumetric Data to Container as Scalar"
    read_as = "scalar"


class ImportAsLabelLayer(bpy.types.Operator, ImportVolumetricData):
    bl_idname = "bioxelnodes.import_as_label_layer"
    bl_label = "Import as Label"
    bl_description = "Import Volumetric Data to Container as Label"
    read_as = "label"


try:
    class BIOXELNODES_FH_ImportVolumetricData(bpy.types.FileHandler):
        bl_idname = "BIOXELNODES_FH_ImportVolumetricData"
        bl_label = "File handler for dicom import"
        bl_import_operator = "bioxelnodes.parse_volumetric_data"
        bl_file_extensions = ";".join(FH_EXTS)

        @classmethod
        def poll_drop(cls, context):
            return (context.area and context.area.type == 'VIEW_3D')
except:
    ...


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
    bl_label = "Import Volumetric Data"
    bl_description = "Import Volumetric Data as Layer"
    bl_options = {'UNDO'}

    meta = {}
    thread = None
    _timer = None

    progress: bpy.props.FloatProperty(name="Progress",
                                      options={"SKIP_SAVE"},
                                      default=1)  # type: ignore

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # type: ignore
    directory: bpy.props.StringProperty(subtype='DIR_PATH')  # type: ignore
    container: bpy.props.StringProperty()   # type: ignore

    read_as: bpy.props.EnumProperty(name="Read as",
                                    default="scalar",
                                    items=[("scalar", "Scalar", ""),
                                           ("label", "Labels", "")])  # type: ignore

    series_id: bpy.props.EnumProperty(name="Select Series",
                                      items=get_series_ids)  # type: ignore

    series_ids: bpy.props.CollectionProperty(
        type=BIOXELNODES_Series)  # type: ignore

    def execute(self, context):
        ext = get_ext(self.filepath)
        if ext not in SUPPORT_EXTS:
            self.report({"WARNING"}, "Not supported extension.")
            return {'CANCELLED'}

        print("Collecting Meta Data...")

        def parse_volumetric_data_func(self, context, cancel):

            def progress_callback(factor, text):
                if cancel():
                    return False
                progress_update(context, factor, text)
                return True

            try:
                volume, meta = parse_volumetric_data(filepath=self.filepath,
                                                     series_id=self.series_id,
                                                     progress_callback=progress_callback)
            except CancelledByUser:
                return

            if cancel():
                return

            self.meta = meta

        # Init cancel flag
        self.is_cancelled = False
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
            progress_update(context, 0, "Canceling...")
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

        # Check if thread is cancelled by user
        if self.is_cancelled:
            self.report({"WARNING"}, "Canncelled by user.")
            return {'CANCELLED'}

        # If not canncelled...
        for key, value in self.meta.items():
            print(f"{key}: {value}")

        orig_shape = self.meta['shape']
        orig_spacing = self.meta['spacing']
        min_size = min(orig_spacing[0],
                       orig_spacing[1], orig_spacing[2])
        bioxel_size = max(min_size, 1.0)

        layer_size = get_layer_size(orig_shape,
                                    bioxel_size)
        log10 = math.floor(math.log10(max(*layer_size)))
        scene_scale = math.pow(10, -log10)

        if self.container:
            container = bpy.data.objects[self.container]
            container_name = container.name
        else:
            container_name = self.meta['name']

        bpy.ops.bioxelnodes.import_volumetric_data_dialog(
            'INVOKE_DEFAULT',
            filepath=self.filepath,
            container_name=container_name,
            layer_name=self.meta['description'],
            orig_shape=orig_shape,
            orig_spacing=orig_spacing,
            bioxel_size=bioxel_size,
            series_id=self.series_id or "",
            frame_count=self.meta['frame_count'],
            channel_count=self.meta['channel_count'],
            container=self.container,
            read_as=self.read_as,
            scene_scale=scene_scale
        )

        self.report({"INFO"}, "Successfully Readed.")
        return {'FINISHED'}

    def invoke(self, context, event):
        if not self.filepath and not self.directory:
            return {'CANCELLED'}

        ext = get_ext(self.filepath)

        # Series Selection
        if ext in DICOM_EXTS:
            dir_path = Path(self.filepath).parent
            reader = sitk.ImageSeriesReader()
            reader.MetaDataDictionaryArrayUpdateOn()
            reader.LoadPrivateTagsOn()

            series_ids = reader.GetGDCMSeriesIDs(str(dir_path))

            for series_id in series_ids:
                series_files = reader.GetGDCMSeriesFileNames(
                    str(dir_path), series_id)
                single = sitk.ImageFileReader()
                single.SetFileName(series_files[0])
                single.LoadPrivateTagsOn()
                single.ReadImageInformation()

                def get_meta(key):
                    try:
                        stirng = single.GetMetaData(key).removesuffix(" ")
                        if stirng in ["No study description",
                                      "No series description"]:
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

                # some series image count = 0 ????
                if int(count) == 0:
                    continue

                series_item = self.series_ids.add()
                series_item.id = series_id
                series_item.label = "{:<20} {:>1}".format(f"{study_description}>{series_description}({series_modality})",
                                                          f"({size_x}x{size_y})x{count}")

            if len(series_ids) > 1:
                context.window_manager.invoke_props_dialog(self,
                                                           width=400,
                                                           title="Which series to import?")
                return {'RUNNING_MODAL'}
            else:
                self.series_id = series_ids[0]

        self.execute(context)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        layout.label(
            text='Detect multi-series in DICOM, pick one')
        layout.prop(self, "series_id")


class ImportVolumetricDataDialog(bpy.types.Operator):
    bl_idname = "bioxelnodes.import_volumetric_data_dialog"
    bl_label = "Import Volumetric Data"
    bl_description = "Import Volumetric Data as Layer"
    bl_options = {'UNDO'}

    layers = []
    thread = None
    _timer = None

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # type: ignore

    container_name: bpy.props.StringProperty(
        name="Container Name")   # type: ignore

    layer_name: bpy.props.StringProperty(name="Layer Name")   # type: ignore

    series_id: bpy.props.StringProperty()   # type: ignore

    container: bpy.props.StringProperty()   # type: ignore

    frame_count: bpy.props.IntProperty()  # type: ignore

    channel_count: bpy.props.IntProperty()  # type: ignore

    read_as: bpy.props.EnumProperty(name="Read as",
                                    default="scalar",
                                    items=[("scalar", "Scalar", ""),
                                           ("label", "Labels", "")])  # type: ignore

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

    as_time_sequence: bpy.props.BoolProperty(name="As Time Sequence",
                                             default=False)  # type: ignore

    split_channels: bpy.props.BoolProperty(name="Split Channels",
                                           default=False)  # type: ignore

    def execute(self, context):
        def import_volumetric_data_func(self, context, cancel):
            progress_update(context, 0.0, "Parsing Volumetirc Data...")

            def progress_callback(factor, text):
                if cancel():
                    return False
                progress_update(context, factor*0.2, text)
                return True

            try:
                volume, meta = parse_volumetric_data(filepath=self.filepath,
                                                     series_id=self.series_id,
                                                     progress_callback=progress_callback)
            except CancelledByUser:
                return

            if cancel():
                return

            layer_shape = get_layer_shape(self.bioxel_size,
                                          meta['shape'],
                                          self.orig_spacing)
            layer_dtype = volume.dtype.num

            # After sitk.DICOMOrient(), origin and direction will also orient base on LPS
            # so we need to convert them into RAS
            mat_lps2ras = axis_conversion(from_forward='-Z',
                                          from_up='-Y',
                                          to_forward='-Z',
                                          to_up='Y').to_4x4()

            mat_location = mathutils.Matrix.Translation(
                mathutils.Vector(meta['origin'])
            )

            mat_rotation = mathutils.Matrix(
                np.array(meta['direction']).reshape((3, 3))
            ).to_4x4()

            mat_scale = mathutils.Matrix.Scale(self.bioxel_size,
                                               4)

            layer_transfrom = mat_lps2ras @ mat_location @ mat_rotation @ mat_scale \
                if meta['is_oriented'] else mat_location @ mat_rotation @ mat_scale

            def convert_to_vdb(volume, layer_shape, layer_type, progress_callback=None):
                if self.as_time_sequence:
                    grids_sequence = []
                    for f in range(volume.shape[0]):
                        if cancel():
                            raise CancelledByUser

                        print(f"Processing Frame {f+1}...")
                        if progress_callback:
                            progress_callback(f, volume.shape[0])
                        frame = ski.resize(volume[f, :, :, :],
                                           layer_shape,
                                           preserve_range=True,
                                           anti_aliasing=volume.dtype.kind != "b")

                        grid = vdb.FloatGrid()
                        frame = frame.copy().astype(np.float32)
                        grid.copyFromArray(frame)
                        grid.transform = vdb.createLinearTransform(
                            layer_transfrom.transposed())
                        grid.name = layer_type
                        grids_sequence.append([grid])

                    print(f"Saving the Cache...")
                    vdb_paths = save_vdbs(grids_sequence, context)

                else:
                    if cancel():
                        raise CancelledByUser
                    print(f"Processing the Data...")
                    volume = ski.resize(volume,
                                        layer_shape,
                                        preserve_range=True,
                                        anti_aliasing=volume.dtype.kind != "b")

                    grid = vdb.FloatGrid()
                    volume = volume.copy().astype(np.float32)
                    grid.copyFromArray(volume)
                    grid.transform = vdb.createLinearTransform(
                        layer_transfrom.transposed())
                    grid.name = layer_type

                    print(f"Saving the Cache...")
                    vdb_paths = [save_vdb([grid], context)]

                return vdb_paths

            if cancel():
                return

            # change shape as sequence or not
            if self.as_time_sequence:
                if volume.shape[0] == 1:
                    # channel as frame
                    volume = volume.transpose(4, 1, 2, 3, 0)

            else:
                volume = volume[0, :, :, :, :]

            layers = []

            if self.read_as == "label":
                layer_name = self.layer_name or "Label"
                volume = np.amax(volume, -1)
                volume = volume.astype(int)
                orig_max = int(np.max(volume))
                orig_min = int(np.min(volume))
                progress_step = 0.7/orig_max

                for i in range(orig_max):
                    if cancel():
                        return

                    layer_name_i = f"{layer_name}_{i+1}"
                    progress = 0.2+i*progress_step
                    progress_update(context, progress,
                                    f"Processing {layer_name_i}...")

                    def progress_callback(frame, total):
                        sub_progress_step = progress_step/total
                        sub_progress = progress + frame * sub_progress_step
                        progress_update(context, sub_progress,
                                        f"Processing {layer_name_i} Frame {frame+1}...")

                    label = volume == np.full_like(volume, i+1)
                    try:
                        filepaths = convert_to_vdb(volume=label,
                                                   layer_shape=layer_shape,
                                                   layer_type="label",
                                                   progress_callback=progress_callback)
                    except CancelledByUser:
                        return

                    layers.append({"name": layer_name_i,
                                   "filepaths": filepaths,
                                   "type": "label",
                                   "shape": layer_shape,
                                   "transfrom": layer_transfrom,
                                   "dtype": layer_dtype,
                                   "node_type": "BioxelNodes_MaskByLabel",
                                   "scalar_offset": 0,
                                   "orig_min": 0,
                                   "orig_max": 1})

            elif self.read_as == "scalar":
                layer_name = self.layer_name or "Scalar"
                # SHOULD NOT change any value!
                volume = volume.astype(np.float32)

                if self.split_channels:
                    progress_step = 0.7/volume.shape[-1]
                    for i in range(volume.shape[-1]):
                        if cancel():
                            return

                        layer_name_i = f"{layer_name}_{i+1}"
                        progress = 0.2 + i*progress_step

                        progress_update(context, progress,
                                        f"Processing {layer_name_i}...")

                        def progress_callback(frame, total):
                            sub_progress_step = progress_step/total
                            sub_progress = progress + frame * sub_progress_step
                            progress_update(context, sub_progress,
                                            f"Processing {layer_name_i} Frame {frame+1}...")

                        scalar = volume[:, :, :, :, i] \
                            if self.as_time_sequence else volume[:, :, :, i]
                        orig_max = float(np.max(scalar))
                        orig_min = float(np.min(scalar))

                        scalar_offset = 0
                        if orig_min < 0:
                            scalar_offset = -orig_min
                            scalar = scalar + \
                                np.full_like(scalar, scalar_offset)
                        try:
                            filepaths = convert_to_vdb(volume=scalar,
                                                       layer_shape=layer_shape,
                                                       layer_type="scalar",
                                                       progress_callback=progress_callback)
                        except CancelledByUser:
                            return

                        layers.append({"name": layer_name_i,
                                       "filepaths": filepaths,
                                       "type": "scalar",
                                       "shape": layer_shape,
                                       "transfrom": layer_transfrom,
                                       "dtype": layer_dtype,
                                       "node_type": "BioxelNodes_MaskByThreshold",
                                       "scalar_offset": scalar_offset,
                                       "orig_min": orig_min,
                                       "orig_max": orig_max})

                else:
                    if cancel():
                        return

                    progress_update(context, 0.2,
                                    f"Processing {layer_name}...")
                    volume = np.amax(volume, -1)
                    orig_max = float(np.max(volume))
                    orig_min = float(np.min(volume))

                    scalar_offset = 0
                    if orig_min < 0:
                        scalar_offset = -orig_min
                        volume = volume + np.full_like(volume, scalar_offset)

                    def progress_callback(frame, total):
                        sub_progress_step = 0.7/total
                        sub_progress = 0.2 + frame * sub_progress_step
                        progress_update(context, sub_progress,
                                        f"Processing {layer_name} Frame {frame+1}...")

                    try:
                        filepaths = convert_to_vdb(volume=volume,
                                                   layer_shape=layer_shape,
                                                   layer_type="scalar",
                                                   progress_callback=progress_callback)
                    except CancelledByUser:
                        return

                    layers.append({"name": layer_name,
                                   "filepaths": filepaths,
                                   "type": "scalar",
                                   "shape": layer_shape,
                                   "transfrom": layer_transfrom,
                                   "dtype": layer_dtype,
                                   "node_type": "BioxelNodes_MaskByThreshold",
                                   "scalar_offset": scalar_offset,
                                   "orig_min": orig_min,
                                   "orig_max": orig_max})

            if cancel():
                return

            self.layers = layers
            self.is_first_import = len(get_all_layers()) == 0
            progress_update(context, 0.9, "Creating Layers...")

        self.is_cancelled = False
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
            progress_update(context, 0, "Canceling...")
            return {'PASS_THROUGH'}

        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        bpy.context.workspace.status_text_set_internal(None)
        if self.thread.is_alive():
            return {'PASS_THROUGH'}

        self.thread.join()
        context.window_manager.event_timer_remove(self._timer)
        bpy.types.STATUSBAR_HT_header.remove(progress_bar)

        if self.is_cancelled:
            self.report({"WARNING"}, "Canncelled by user.")
            return {'CANCELLED'}

        # Wrapper a Container
        if not self.container:
            container_name = self.container_name or "Container"

            # Make transformation
            # (S)uperior  -Z -> Y
            # (A)osterior  Y -> Z
            mat_ras2blender = axis_conversion(from_forward='-Z',
                                              from_up='Y',
                                              to_forward='Y',
                                              to_up='Z').to_4x4()

            mat_scene_scale = mathutils.Matrix.Scale(self.scene_scale,
                                                     4)

            bpy.ops.mesh.primitive_cube_add(enter_editmode=False,
                                            align='WORLD',
                                            location=(0, 0, 0),
                                            scale=(1, 1, 1))

            container = bpy.context.active_object

            bbox_verts = calc_bbox_verts((0, 0, 0), self.layers[0]['shape'])
            for i, vert in enumerate(container.data.vertices):
                vert.co = self.layers[0]['transfrom'] @ mathutils.Vector(
                    bbox_verts[i])

            container.matrix_world = mat_ras2blender @ mat_scene_scale
            container.name = container_name
            container.data.name = container_name

            container['bioxel_container'] = True
            bpy.ops.node.new_geometry_nodes_modifier()
            container_node_group = container.modifiers[0].node_group
            input_node = get_nodes_by_type(container_node_group,
                                           'NodeGroupInput')[0]
            container_node_group.links.remove(
                input_node.outputs[0].links[0])

        else:
            container = bpy.data.objects[self.container]
            container_node_group = container.modifiers[0].node_group

        for i, layer_info in enumerate(self.layers):
            # Read VDB
            print(f"Loading the Cache of {layer_info['name']}...")
            filepaths = layer_info["filepaths"]
            if len(filepaths) > 0:
                # Read VDB
                files = [{"name": str(filepath.name), "name": str(filepath.name)}
                         for filepath in filepaths]

                bpy.ops.object.volume_import(filepath=str(filepaths[0]), directory=str(filepaths[0].parent),
                                             files=files, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
            else:
                bpy.ops.object.volume_import(filepath=str(filepaths[0]),
                                             align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))

            layer = bpy.context.active_object
            layer.data.sequence_mode = 'REPEAT'

            # Set props to VDB object
            layer.name = f"{container.name}_{layer_info['name']}"
            layer.data.name = f"{container.name}_{layer_info['name']}"

            lock_transform(layer)
            hide_in_ray(layer)
            layer.hide_select = True
            layer.hide_render = True
            layer.hide_viewport = True
            layer.data.display.use_slice = True
            layer.data.display.density = 1e-05

            layer['bioxel_layer'] = True
            layer['bioxel_layer_type'] = layer_info['type']
            layer.parent = container

            for collection in layer.users_collection:
                collection.objects.unlink(layer)

            for collection in container.users_collection:
                collection.objects.link(layer)

            print(f"Creating Node for {layer_info['name']}...")

            bpy.ops.node.new_geometry_nodes_modifier()
            node_group = layer.modifiers[0].node_group

            input_node = get_nodes_by_type(node_group, 'NodeGroupInput')[0]
            output_node = get_nodes_by_type(
                node_group, 'NodeGroupOutput')[0]

            to_layer_node = custom_nodes.add_node(node_group,
                                                  "BioxelNodes__ConvertToLayer")

            node_group.links.new(input_node.outputs[0],
                                 to_layer_node.inputs[0])
            node_group.links.new(to_layer_node.outputs[0],
                                 output_node.inputs[0])

            # TODO: change to transform when 4.2?
            loc, rot, sca = layer_info['transfrom'].decompose()
            layer_origin = tuple(loc)
            layer_rotation = tuple(rot.to_euler())

            # for compatibility to old vdb
            # to_layer_node.inputs['Not Transfromed'].default_value = True
            to_layer_node.inputs['Layer ID'].default_value = random.randint(-200000000,
                                                                            200000000)
            to_layer_node.inputs['Bioxel Size'].default_value = self.bioxel_size
            to_layer_node.inputs['Data Type'].default_value = layer_info['dtype']
            to_layer_node.inputs['Shape'].default_value = layer_info['shape']
            to_layer_node.inputs['Origin'].default_value = layer_origin
            to_layer_node.inputs['Rotation'].default_value = layer_rotation
            to_layer_node.inputs['Scalar Offset'].default_value = layer_info['scalar_offset']
            to_layer_node.inputs['Scalar Min'].default_value = layer_info['orig_min']
            to_layer_node.inputs['Scalar Max'].default_value = layer_info['orig_max']

            move_node_between_nodes(
                to_layer_node, [input_node, output_node])

            mask_node = custom_nodes.add_node(container_node_group,
                                              layer_info['node_type'])
            mask_node.label = layer_info['name']
            mask_node.inputs[0].default_value = layer

            # Connect to output if no output linked
            output_node = get_nodes_by_type(container_node_group,
                                            'NodeGroupOutput')[0]
            if len(output_node.inputs[0].links) == 0:
                container_node_group.links.new(mask_node.outputs[0],
                                               output_node.inputs[0])
                move_node_to_node(mask_node, output_node, (-300, 0))
            else:
                move_node_to_node(mask_node, output_node, (0, -100 * (i+1)))

        select_object(container)

        # Change render setting for better result
        preferences = context.preferences.addons[__package__].preferences

        if preferences.do_change_render_setting and self.is_first_import:
            if bpy.app.version < (4, 2, 0):
                bpy.context.scene.render.engine = 'CYCLES'

            try:
                bpy.context.scene.cycles.shading_system = True
                bpy.context.scene.cycles.volume_bounces = 12
                bpy.context.scene.cycles.transparent_max_bounces = 16
                bpy.context.scene.cycles.volume_preview_step_rate = 10
                bpy.context.scene.cycles.volume_step_rate = 10
            except:
                pass

            try:
                bpy.context.scene.eevee.use_taa_reprojection = False
                bpy.context.scene.eevee.volumetric_tile_size = '2'
                bpy.context.scene.eevee.volumetric_shadow_samples = 128
                bpy.context.scene.eevee.volumetric_samples = 256
            except:
                pass

            if bpy.app.version >= (4, 2, 0):
                try:
                    bpy.context.scene.eevee.use_volumetric_shadows = True
                except:
                    pass

        self.report({"INFO"}, "Successfully Imported")
        return {'FINISHED'}

    def invoke(self, context, event):
        if self.read_as == "label":
            volume_dtype = "Label"
        elif self.read_as == "scalar":
            volume_dtype = "Scalar"
        title = f"As {volume_dtype} Opitons (Add to Container: {self.container})" \
            if self.container != "" else f"As {volume_dtype} Options (Init a Container)"
        context.window_manager.invoke_props_dialog(self,
                                                   width=500,
                                                   title=title)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layer_shape = get_layer_shape(self.bioxel_size,
                                      self.orig_shape,
                                      self.orig_spacing)

        orig_shape = tuple(self.orig_shape)

        bioxel_count = layer_shape[0] * layer_shape[1] * layer_shape[2]
        layer_shape_text = f"Shape from {str(orig_shape)} to {str(layer_shape)}"
        if bioxel_count > 100000000:
            layer_shape_text += "**TOO LARGE!**"

        layout = self.layout
        if self.container == "":
            layout.prop(self, "container_name")
        layout.prop(self, "layer_name")

        panel = layout.box()
        panel.prop(self, "bioxel_size")
        row = panel.row()
        row.prop(self, "orig_spacing")
        panel.label(text=layer_shape_text)

        panel = layout.box()
        if self.as_time_sequence and self.frame_count == 1:
            channel_count = 1
            frame_count = self.channel_count
        else:
            channel_count = self.channel_count
            frame_count = self.frame_count

        import_channel = channel_count if self.split_channels or channel_count == 1 else "combined"
        import_frame = frame_count if self.as_time_sequence else "1"
        panel.prop(self, "as_time_sequence",
                   text=f"As Time Sequence (get {frame_count} frames, import {import_frame} frames)")
        if self.read_as == "scalar":
            panel.prop(self, "split_channels",
                       text=f"Split Channels (get {channel_count} channels, import {import_channel} channels)")

        if self.container == "":
            layer_size = get_layer_size(layer_shape,
                                        self.bioxel_size,
                                        self.scene_scale)
            layer_size_text = f"Size will be: ({layer_size[0]:.2f}, {layer_size[1]:.2f}, {layer_size[2]:.2f}) m"
            panel = layout.box()
            panel.prop(self, "scene_scale")
            panel.label(text=layer_size_text)


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
        layer = get_layer(bpy.context.active_object)
        return True if layer else False

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        layer = get_layer(bpy.context.active_object)

        filepath = f"{self.filepath.split('.')[0]}.vdb"
        # "//"
        source_dir = bpy.path.abspath(layer.data.filepath)

        output_path: Path = Path(filepath).resolve()
        source_path: Path = Path(source_dir).resolve()
        # print('output_path', output_path)
        # print('source_path', source_path)
        shutil.copy(source_path, output_path)

        self.report({"INFO"}, f"Successfully exported to {output_path}")

        return {'FINISHED'}
