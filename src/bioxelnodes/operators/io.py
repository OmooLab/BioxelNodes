import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

import bpy
import numpy as np
import SimpleITK as sitk

# KeyboardInterrupt replaced with built-in KeyboardInterrupt
from ..props import BIOXEL_Series
from ..utils import get_layer_obj, wrapped_label

from ..bioxel.parse import DICOM_EXTS, SUPPORT_EXTS, get_ext, parse_volumetric_data

from ..utils import get_cache_dir, progress_update, progress_bar
from ..layer import get_layer_caches, set_layer_caches


def get_layer_shape(bioxel_size: float, orig_shape: tuple, orig_spacing: tuple):
    shape = (
        int(orig_shape[0] / bioxel_size * orig_spacing[0]),
        int(orig_shape[1] / bioxel_size * orig_spacing[1]),
        int(orig_shape[2] / bioxel_size * orig_spacing[2]),
    )

    return (
        shape[0] if shape[0] > 0 else 1,
        shape[1] if shape[1] > 0 else 1,
        shape[2] if shape[2] > 0 else 1,
    )


def get_layer_size(shape: tuple, bioxel_size: float, scale: float = 1.0):
    size = (
        float(shape[0] * bioxel_size * scale),
        float(shape[1] * bioxel_size * scale),
        float(shape[2] * bioxel_size * scale),
    )

    return size


def write_worker_json(path: Path, data):
    path.write_text(json.dumps(data), encoding="utf-8")


def read_worker_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def remove_progress_bar_safe():
    try:
        bpy.types.STATUSBAR_HT_header.remove(progress_bar)
    except Exception:
        pass


def get_addon_module_name():
    package_name = __package__ or "bioxelnodes.operators"
    suffix = ".operators"
    if package_name.endswith(suffix):
        return package_name[: -len(suffix)]
    return package_name


def start_worker_process(owner, command: str, payload: dict):
    job_dir = Path(tempfile.mkdtemp(prefix="bioxel_import_", dir=str(get_cache_dir())))
    config_path = job_dir / "config.json"
    progress_path = job_dir / "progress.json"
    result_path = job_dir / "result.json"
    cancel_path = job_dir / "cancel"
    log_path = job_dir / "worker.log"

    addon_name = get_addon_module_name()
    config = {
        **payload,
        "command": command,
        "addon_name": addon_name,
        "progress_path": str(progress_path),
        "result_path": str(result_path),
        "cancel_path": str(cancel_path),
    }
    write_worker_json(config_path, config)
    write_worker_json(
        progress_path,
        {"factor": 0.0, "text": "Starting background Blender..."},
    )

    print(f"Starting Bioxel worker with addon module: {addon_name}")
    cmd = [
        bpy.app.binary_path,
        "--background",
        "--addons",
        addon_name,
        "--command",
        "bioxelnodes_import_worker",
        str(config_path),
    ]

    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    log_file = log_path.open("w", encoding="utf-8")
    try:
        owner.process = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
        )
    finally:
        log_file.close()

    owner.job_dir = job_dir
    owner.progress_path = progress_path
    owner.result_path = result_path
    owner.cancel_path = cancel_path
    owner.log_path = log_path


def cancel_worker_process(owner, context):
    owner.is_cancelled = True
    try:
        owner.cancel_path.write_text("cancel", encoding="utf-8")
    except Exception:
        pass
    progress_update(context, 0.0, "Canceling...")


def update_worker_progress(owner, context):
    progress = read_worker_json(owner.progress_path)
    if progress:
        progress_update(
            context,
            float(progress.get("factor", 0.0)),
            progress.get("text", ""),
        )

"""
ImportData    -> ParseVolumetricData -> ImportDataDialog
    start import                 parse data              execute import
"""


class ImportDataBase:
    bl_options = {"UNDO"}
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # type: ignore
    read_as = None

    def draw(self, context):
        """
        Display helpful information in the file browser's properties region
        when the file selector is open for this operator.
        """
        layout = self.layout
        exts_list = sorted(SUPPORT_EXTS)
        layout.label(text="Supported formats:")
        chunk_size = 6  # adjust per-line count to taste
        for i in range(0, len(exts_list), chunk_size):
            layout.label(text=" ".join(exts_list[i : i + chunk_size]))

        layout.separator()
        layout.label(text="Tips:")
        wrapped_label(
            layout, "- Use 'Import Data' button in Bioxel panel to import data"
        )
        wrapped_label(
            layout, "- Use 'Import as ...' to choose data type (Scalar/Label/Color)"
        )
        wrapped_label(
            layout, "- If the file contains multiple series, select series after open"
        )

    def execute(self, context):
        data_path = Path(self.filepath).resolve()
        ext = get_ext(data_path)
        if ext not in SUPPORT_EXTS:
            self.report({"WARNING"}, "Not supported format.")
            return {"CANCELLED"}

        if self.read_as is None:
            bpy.ops.bioxel.parse_volumetric_data(
                "INVOKE_DEFAULT", filepath=self.filepath, skip_read_as=False
            )
        else:

            bpy.ops.bioxel.parse_volumetric_data(
                "INVOKE_DEFAULT",
                filepath=self.filepath,
                skip_read_as=True,
                read_as=self.read_as,
            )

        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

class ImportData(bpy.types.Operator, ImportDataBase):
    bl_idname = "bioxel.import_data"
    bl_label = "Import Data"
    bl_description = "Import Volumetric Data to Layer"
    bl_icon = "EVENT_S"


class ImportAsScalar(bpy.types.Operator, ImportDataBase):
    bl_idname = "bioxel.import_as_scalar"
    bl_label = "Import as Scalar"
    bl_description = "Import Volumetric Data to Container as Scalar"
    bl_icon = "EVENT_S"
    read_as = "SCALAR"


class ImportAsLabel(bpy.types.Operator, ImportDataBase):
    bl_idname = "bioxel.import_as_label"
    bl_label = "Import as Label"
    bl_description = "Import Volumetric Data to Container as Label"
    bl_icon = "EVENT_L"
    read_as = "LABEL"


class ImportAsColor(bpy.types.Operator, ImportDataBase):
    bl_idname = "bioxel.import_as_color"
    bl_label = "Import as Color"
    bl_description = "Import Volumetric Data to Container as Color"
    bl_icon = "EVENT_C"
    read_as = "COLOR"


class BIOXELNODES_FH_ImportData(bpy.types.FileHandler):
    bl_idname = "BIOXELNODES_FH_ImportData"
    bl_label = "File handler for dicom import"
    bl_import_operator = "bioxel.parse_volumetric_data"
    bl_file_extensions = ";".join(SUPPORT_EXTS)

    @classmethod
    def poll_drop(cls, context):
        return (
            bpy.context.area.type == "NODE_EDITOR"
            and bpy.context.space_data.node_tree.bl_idname == "GeometryNodeTree"
        )


def get_series_ids(self, context):
    items = []
    for index, series_id in enumerate(self.series_ids):
        items.append((series_id.id, series_id.label, "", index))

    return items


class ParseVolumetricData(bpy.types.Operator):
    bl_idname = "bioxel.parse_volumetric_data"
    bl_label = "Import Volumetric Data (BioxelNodes)"
    bl_description = "Import Volumetric Data as Layer"
    bl_options = {"UNDO"}

    meta = None
    label_count = 0
    dtype = None
    process = None
    job_dir = None
    progress_path = None
    result_path = None
    cancel_path = None
    log_path = None
    _timer = None

    progress: bpy.props.FloatProperty(
        name="Progress", options={"SKIP_SAVE"}, default=1
    )  # type: ignore

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # type: ignore

    skip_read_as: bpy.props.BoolProperty(
        name="Skip Read As", default=False, options={"SKIP_SAVE"}
    )  # type: ignore

    skip_series_select: bpy.props.BoolProperty(
        name="Skip Sries Select", default=True, options={"SKIP_SAVE"}
    )  # type: ignore

    read_as: bpy.props.EnumProperty(
        name="Read as",
        default="SCALAR",
        items=[
            ("SCALAR", "Scalar", ""),
            ("LABEL", "Label", ""),
            ("COLOR", "Color", ""),
        ],
    )  # type: ignore

    series_id: bpy.props.EnumProperty(
        name="Select Series", items=get_series_ids
    )  # type: ignore

    series_ids: bpy.props.CollectionProperty(type=BIOXEL_Series)  # type: ignore

    def execute(self, context):
        print("Collecting Meta Data...")
        progress_update(context, 0.0, "Collecting Meta Data...")

        def progress_callback(factor, text):
            progress_update(context, factor, text)

        try:
            series_id = self.series_id if self.series_id != "empty" else ""
            data, meta = parse_volumetric_data(
                data_file=self.filepath,
                series_id=series_id,
                progress_callback=progress_callback,
            )
        except Exception as e:
            raise e

        self.meta = meta
        self.label_count = int(np.max(data))
        self.dtype = data.dtype
        progress_update(context, 1.0)

        for key, value in self.meta.items():
            print(f"{key}: {value}")

        if self.read_as == "LABEL":
            if self.label_count > 100 or self.dtype.kind not in ["i", "u"]:
                self.report({"ERROR"}, "Invaild label data.")
                return {"CANCELLED"}

            if self.label_count == 0:
                self.report({"ERROR"}, "Get no label.")
                return {"CANCELLED"}

        orig_shape = self.meta["xyz_shape"]
        orig_spacing = self.meta["spacing"]

        min_log10 = math.floor(math.log10(min(*orig_spacing)))
        max_log10 = math.floor(math.log10(max(*orig_spacing)))

        if orig_spacing[2] == 1 and min_log10 < -1:
            orig_spacing = (
                orig_spacing[0] * math.pow(10, -min_log10 - 2),
                orig_spacing[1] * math.pow(10, -min_log10 - 2),
                1,
            )
        elif min_log10 > 0:
            orig_spacing = (
                orig_spacing[0] * math.pow(10, -min_log10 - 1),
                orig_spacing[1] * math.pow(10, -min_log10 - 1),
                orig_spacing[2] * math.pow(10, -min_log10 - 1),
            )
        elif max_log10 < 0:
            orig_spacing = (
                orig_spacing[0] * math.pow(10, -max_log10 - 1),
                orig_spacing[1] * math.pow(10, -max_log10 - 1),
                orig_spacing[2] * math.pow(10, -max_log10 - 1),
            )

        bioxel_size = max(min(*orig_spacing), 1.0)

        layer_shape = get_layer_shape(bioxel_size, orig_shape, orig_spacing)
        layer_size = get_layer_size(layer_shape, bioxel_size, 0.01)
        min_log10 = math.floor(math.log10(min(*layer_size)))
        max_log10 = math.floor(math.log10(max(*layer_size)))

        if min_log10 > 0:
            scene_scale = math.pow(10, -min_log10 - 2)
        elif max_log10 < 0:
            scene_scale = math.pow(10, -max_log10 - 2)
        else:
            scene_scale = 0.01

        series_id = self.series_id if self.series_id != "empty" else ""
        bpy.ops.bioxel.import_volumetric_data_dialog(
            "INVOKE_DEFAULT",
            filepath=self.filepath,
            layer_name=self.meta["description"],
            orig_shape=orig_shape,
            orig_spacing=orig_spacing,
            bioxel_size=bioxel_size,
            series_id=series_id,
            frame_count=self.meta["frame_count"],
            channel_count=self.meta["channel_count"],
            read_as=self.read_as,
            label_count=self.label_count,
            scene_scale=scene_scale,
        )

        self.report({"INFO"}, "Successfully Readed.")
        return {"FINISHED"}

    def invoke(self, context, event):
        # why not report in execute?
        # If this operator is executing, a new execute will when pre-one done.
        if context.window_manager.bioxel_progress_factor < 1:
            print("A process is executing, please wait for it to finish.")
            return {"CANCELLED"}

        if not self.filepath:
            self.report({"WARNING"}, "No file selected.")
            return {"CANCELLED"}

        data_path = Path(self.filepath).resolve()
        ext = get_ext(data_path)
        if ext not in SUPPORT_EXTS:
            self.report({"WARNING"}, "Not supported format.")
            return {"CANCELLED"}

        title = f"Add to **{context.object.name}**"

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
                    str(data_dirpath), series_id
                )
                single = sitk.ImageFileReader()
                single.SetFileName(series_files[0])
                single.LoadPrivateTagsOn()
                single.ReadImageInformation()

                def get_meta(key):
                    try:
                        stirng = single.GetMetaData(key).removesuffix(" ")
                        stirng.encode("utf-8")
                        if stirng in [
                            "No study description",
                            "No series description",
                            "",
                        ]:
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

                label = "{:<20} {:>1}".format(
                    f"{study_description}>{series_description}({series_modality})",
                    f"({size_x}x{size_y})x{count}",
                )

                series_items[series_id] = label

            for series_id, label in series_items.items():
                series_item = self.series_ids.add()
                series_item.id = series_id
                series_item.label = label

            if len(series_items.keys()) > 1:
                self.skip_series_select = False
                context.window_manager.invoke_props_dialog(self, width=400, title=title)
                return {"RUNNING_MODAL"}
            elif len(series_items.keys()) == 1:
                self.series_id = list(series_items.keys())[0]
            else:
                self.report({"ERROR"}, "Get no vaild series.")
                return {"CANCELLED"}

        if self.skip_read_as:
            return self.execute(context)
        else:
            context.window_manager.invoke_props_dialog(self, width=400, title=title)
            return {"RUNNING_MODAL"}

    def draw(self, context):
        layout = self.layout
        if not self.skip_read_as:
            layout.label(text="What kind is the data read as?")
            layout.prop(self, "read_as")
        if not self.skip_series_select:
            layout.label(text="Which series to import?")
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


class ImportDataDialog(bpy.types.Operator):
    bl_idname = "bioxel.import_volumetric_data_dialog"
    bl_label = "Import Volumetric Data"
    bl_description = "Import Volumetric Data as Layer"
    bl_options = {"UNDO"}

    cache_infos = None
    added_ids = None
    process = None
    job_dir = None
    progress_path = None
    result_path = None
    cancel_path = None
    log_path = None
    _timer = None

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # type: ignore
    layer_name: bpy.props.StringProperty(name="Layer Name")  # type: ignore
    series_id: bpy.props.StringProperty()  # type: ignore
    frame_count: bpy.props.IntProperty()  # type: ignore
    channel_count: bpy.props.IntProperty()  # type: ignore
    label_count: bpy.props.IntProperty()  # type: ignore
    smooth: bpy.props.IntProperty(
        name="Smooth Size (Larger takes longer time)", default=0
    )  # type: ignore
    read_as: bpy.props.EnumProperty(
        name="Read as",
        default="SCALAR",
        items=[
            ("SCALAR", "Scalar", ""),
            ("LABEL", "Label", ""),
            ("COLOR", "Color", ""),
        ],
    )  # type: ignore
    bioxel_size: bpy.props.FloatProperty(
        name="Bioxel Size (Larger size means small resolution)",
        soft_min=0.1,
        soft_max=10.0,
        min=0.1,
        max=1e2,
        default=1,
    )  # type: ignore
    orig_spacing: bpy.props.FloatVectorProperty(
        name="Original Spacing", default=(1, 1, 1)
    )  # type: ignore
    orig_shape: bpy.props.IntVectorProperty(
        name="Original Shape", default=(100, 100, 100)
    )  # type: ignore
    scene_scale: bpy.props.FloatProperty(
        name="Scene Scale (Bioxel Unit pre Blender Unit)",
        soft_min=0.0001,
        soft_max=10.0,
        min=1e-6,
        max=1e6,
        default=0.01,
    )  # type: ignore
    remap: bpy.props.BoolProperty(name="Remap to 0~1", default=False)  # type: ignore
    split_channel: bpy.props.BoolProperty(
        name="Split Channels", default=False
    )  # type: ignore
    frame_source: bpy.props.EnumProperty(
        name="Frame From", items=get_frame_sources
    )  # type: ignore

    def execute(self, context):
        self.is_cancelled = False
        self.has_error = None
        self.cache_infos = None
        self.added_ids = None

        start_worker_process(
            self,
            "import_layers",
            {
                "filepath": self.filepath,
                "series_id": self.series_id,
                "cache_dir": str(get_cache_dir() / "layers"),
                "layer_name": self.layer_name,
                "orig_shape": list(self.orig_shape),
                "orig_spacing": list(self.orig_spacing),
                "bioxel_size": self.bioxel_size,
                "read_as": self.read_as,
                "frame_source": self.frame_source,
                "smooth": self.smooth,
                "remap": self.remap,
                "split_channel": self.split_channel,
                "channel_count": self.channel_count,
            },
        )

        self._timer = context.window_manager.event_timer_add(
            time_step=0.1, window=context.window
        )
        bpy.types.STATUSBAR_HT_header.append(progress_bar)

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if event.type == "ESC":
            cancel_worker_process(self, context)
            return {"PASS_THROUGH"}

        if event.type != "TIMER":
            return {"PASS_THROUGH"}

        bpy.context.workspace.status_text_set_internal(None)
        update_worker_progress(self, context)

        if self.process.poll() is None:
            return {"PASS_THROUGH"}

        context.window_manager.event_timer_remove(self._timer)
        remove_progress_bar_safe()
        progress_update(context, 1.0)

        result = read_worker_json(self.result_path)
        if self.is_cancelled or (result and result.get("cancelled")):
            self.report({"WARNING"}, "Canncelled by user.")
            return {"CANCELLED"}

        if not result:
            self.report({"ERROR"}, f"Import worker failed. See log: {self.log_path}")
            return {"CANCELLED"}

        if not result.get("ok"):
            print(result.get("traceback", ""))
            self.report({"ERROR"}, result.get("error", "Import worker failed."))
            return {"CANCELLED"}

        self.cache_infos = result.get("cache_infos")
        self.added_ids = result.get("added_ids")
        if not self.cache_infos or not self.added_ids:
            self.report({"ERROR"}, "Some thing went wrong.")
            return {"CANCELLED"}

        is_first_import = len(get_layer_caches()) == 0
        existing_data = get_layer_caches()
        existing_data.extend(self.cache_infos)
        set_layer_caches(existing_data)

        setattr(context.window_manager, "bioxel_layer_library", self.added_ids[-1])

        if is_first_import:
            bpy.ops.bioxel.render_setting_preset("EXEC_DEFAULT", preset="balance")

        self.report({"INFO"}, "Successfully Imported")
        return {"FINISHED"}

    def invoke(self, context, event):
        layer_kind = self.read_as.capitalize()
        title = f"Add to **{context.object.name}**, As {layer_kind}"
        context.window_manager.invoke_props_dialog(self, width=500, title=title)
        return {"RUNNING_MODAL"}

    def draw(self, context):
        layer_shape = get_layer_shape(
            self.bioxel_size, self.orig_shape, self.orig_spacing
        )

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
        orig_shape_text = f"[{self.frame_count}, {orig_shape[0]},{orig_shape[1]},{orig_shape[2]}, {self.channel_count}]"
        layer_shape_text = f"{layer_count} x [{frame_count}, {layer_shape[0]},{layer_shape[1]},{layer_shape[2]}, {channel_count}]"

        if bioxel_count > 100000000:
            layer_shape_text += "**TOO LARGE!**"

        layout = self.layout
        panel = layout.box()
        panel.prop(self, "layer_name")
        panel.prop(self, "bioxel_size")
        row = panel.row()
        row.prop(self, "orig_spacing")
        panel.prop(self, "frame_source")

        if self.read_as == "SCALAR":
            panel.prop(self, "split_channel", text=f"Split Channel as Multi Layer")
        elif self.read_as == "LABEL":
            panel.prop(self, "smooth")

        panel.label(text=f"Shape from {orig_shape_text} to {layer_shape_text}")
        panel.label(text="Dimension Order: [Frame, X-axis, Y-axis, Z-axis, Channel]")


class ExportVolumetricData(bpy.types.Operator):
    bl_idname = "bioxel.export_volumetric_data"
    bl_label = "Export Layer as VDB"
    bl_description = "Export Layer as VDB"
    bl_options = {"UNDO"}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # type: ignore

    filename_ext = ".vdb"

    @classmethod
    def poll(cls, context):
        layer_obj = get_layer_obj(bpy.context.active_object)
        return True if layer_obj else False

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

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

        return {"FINISHED"}
