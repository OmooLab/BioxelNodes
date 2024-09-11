import bpy
from pathlib import Path
import shutil

from ..bioxelutils.common import get_all_layer_objs, get_node_lib_path, get_node_version, is_missing_layer, set_file_prop
from .layer import RemoveLayers, SaveLayersCache

from ..constants import NODE_LIB_DIRPATH, VERSIONS
from ..utils import get_cache_dir


class ReLinkNodeLib(bpy.types.Operator):
    bl_idname = "bioxelnodes.relink_node_lib"
    bl_label = "Relink Node Library"
    bl_description = "Relink all nodes to addon library source"
    bl_options = {'UNDO'}

    index: bpy.props.IntProperty()  # type: ignore

    def execute(self, context):
        node_version = VERSIONS[self.index]['node_version']
        lib_path = get_node_lib_path(node_version)

        node_libs = []
        for node_group in bpy.data.node_groups:
            if node_group.name.startswith("BioxelNodes"):
                node_lib = node_group.library
                if node_lib:
                    node_libs.append(node_lib)

        node_libs = list(set(node_libs))

        for node_lib in node_libs:
            node_lib.filepath = str(lib_path)
            # FIXME: may cause crash
            node_lib.reload()

        set_file_prop("node_version", node_version)

        self.report({"INFO"}, f"Successfully relinked.")

        return {'FINISHED'}


class SaveNodeLib(bpy.types.Operator):
    bl_idname = "bioxelnodes.save_node_lib"
    bl_label = "Save Node Library"
    bl_description = "Save node library file to local"
    bl_options = {'UNDO'}

    lib_dir: bpy.props.StringProperty(
        name="Library Directory",
        subtype='DIR_PATH',
        default="//"
    )  # type: ignore

    def execute(self, context):
        node_version = get_node_version()
        if node_version is None:
            node_version = VERSIONS[0]["node_version"]
        else:
            if node_version not in [v["node_version"] for v in VERSIONS]:
                node_version = VERSIONS[0]["node_version"]
                
        lib_path = get_node_lib_path(node_version)
        
        lib_dir = bpy.path.abspath(self.lib_dir)
        local_lib_path: Path = Path(lib_dir, lib_path.name).resolve()
        node_lib_path: Path = lib_path
        blend_path = Path(bpy.path.abspath("//")).resolve()

        if local_lib_path != node_lib_path:
            shutil.copy(node_lib_path, local_lib_path)

        libs = []
        for node_group in bpy.data.node_groups:
            if node_group.name.startswith("BioxelNodes"):
                if node_group.library:
                    libs.append(node_group.library)

        libs = list(set(libs))
        for lib in libs:
            lib.filepath = bpy.path.relpath(str(local_lib_path),
                                            start=str(blend_path))

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_props_dialog(self)
        return {'RUNNING_MODAL'}

    @classmethod
    def poll(cls, context):
        return bpy.data.is_saved


class CleanTemp(bpy.types.Operator):
    bl_idname = "bioxelnodes.clear_temp"
    bl_label = "Clean Temp"
    bl_description = "Clean all cache in temp (include other project cache)"

    def execute(self, context):
        cache_dir = get_cache_dir()
        try:
            shutil.rmtree(cache_dir)
            self.report({"INFO"}, f"Successfully cleaned temp.")
            return {'FINISHED'}
        except:
            self.report({"WARNING"},
                        "Fail to clean temp, you may do it manually.")
            return {'CANCELLED'}

    def invoke(self, context, event):
        context.window_manager.invoke_confirm(self,
                                              event,
                                              message="All temp files will be removed, include other project cache, do you still want to clean?")
        return {'RUNNING_MODAL'}


class RenderSettingPreset(bpy.types.Operator):
    bl_idname = "bioxelnodes.render_setting_preset"
    bl_label = "Render Setting Presets"
    bl_description = "Render setting presets for bioxel"
    bl_options = {'UNDO'}

    PRESETS = {
        "performance": "Performance",
        "balance": "Balance",
        "quality": "Quality",
    }

    preset: bpy.props.EnumProperty(name="Preset",
                                   default="balance",
                                   items=[(k, v, "")
                                          for k, v in PRESETS.items()])  # type: ignore

    def execute(self, context):
        if self.preset == "performance":
            # EEVEE
            bpy.context.scene.eevee.use_taa_reprojection = False
            bpy.context.scene.eevee.volumetric_tile_size = '2'
            bpy.context.scene.eevee.volumetric_shadow_samples = 32
            bpy.context.scene.eevee.volumetric_samples = 64
            bpy.context.scene.eevee.volumetric_ray_depth = 1
            bpy.context.scene.eevee.use_volumetric_shadows = True

            # Cycles
            bpy.context.scene.cycles.shading_system = True
            bpy.context.scene.cycles.volume_bounces = 0
            bpy.context.scene.cycles.transparent_max_bounces = 4
            bpy.context.scene.cycles.volume_preview_step_rate = 4
            bpy.context.scene.cycles.volume_step_rate = 4

        elif self.preset == "balance":
            # EEVEE
            bpy.context.scene.eevee.use_taa_reprojection = False
            bpy.context.scene.eevee.volumetric_tile_size = '2'
            bpy.context.scene.eevee.volumetric_shadow_samples = 64
            bpy.context.scene.eevee.volumetric_samples = 128
            bpy.context.scene.eevee.volumetric_ray_depth = 8
            bpy.context.scene.eevee.use_volumetric_shadows = True

            # Cycles
            bpy.context.scene.cycles.shading_system = True
            bpy.context.scene.cycles.volume_bounces = 4
            bpy.context.scene.cycles.transparent_max_bounces = 8
            bpy.context.scene.cycles.volume_preview_step_rate = 1
            bpy.context.scene.cycles.volume_step_rate = 1

        elif self.preset == "quality":
            # EEVEE
            bpy.context.scene.eevee.use_taa_reprojection = False
            bpy.context.scene.eevee.volumetric_tile_size = '2'
            bpy.context.scene.eevee.volumetric_shadow_samples = 128
            bpy.context.scene.eevee.volumetric_samples = 256
            bpy.context.scene.eevee.volumetric_ray_depth = 16
            bpy.context.scene.eevee.use_volumetric_shadows = True

            # Cycles
            bpy.context.scene.cycles.shading_system = True
            bpy.context.scene.cycles.volume_bounces = 8
            bpy.context.scene.cycles.transparent_max_bounces = 16
            bpy.context.scene.cycles.volume_preview_step_rate = 0.5
            bpy.context.scene.cycles.volume_step_rate = 0.5

        return {'FINISHED'}


class SliceViewer(bpy.types.Operator):
    bl_idname = "bioxelnodes.slice_viewer"
    bl_label = "Slice Viewer"
    bl_description = "A preview scene setting for viewing slicers"
    bl_icon = "FILE_VOLUME"

    def execute(self, context):
        bpy.context.scene.eevee.use_taa_reprojection = False
        bpy.context.scene.eevee.volumetric_tile_size = '2'
        bpy.context.scene.eevee.volumetric_shadow_samples = 128
        bpy.context.scene.eevee.volumetric_samples = 128
        bpy.context.scene.eevee.volumetric_ray_depth = 1
        bpy.context.scene.eevee.use_volumetric_shadows = False

        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].shading.type = 'MATERIAL'
                area.spaces[0].shading.studio_light = 'studio.exr'
                area.spaces[0].shading.studiolight_intensity = 2.5
                area.spaces[0].shading.use_scene_lights = False
                area.spaces[0].shading.use_scene_world = False

        return {'FINISHED'}


def get_all_layers(layer_filter=None):
    def _layer_filter(layer_obj):
        return True

    layer_filter = layer_filter or _layer_filter
    layer_objs = get_all_layer_objs()
    return [obj for obj in layer_objs if layer_filter(obj)]


class SaveAllLayersCache(bpy.types.Operator, SaveLayersCache):
    bl_idname = "bioxelnodes.save_all_layers_cache"
    bl_label = "Save All Layers Cache"
    bl_description = "Save all cache of this file"
    bl_icon = "FILE_TICK"

    success_msg = "Successfully saved all layers."

    def get_layers(self, context):
        def is_not_missing(layer_obj):
            return not is_missing_layer(layer_obj)
        return get_all_layers(is_not_missing)


class RemoveAllMissingLayers(bpy.types.Operator, RemoveLayers):
    bl_idname = "bioxelnodes.remove_all_missing_layers"
    bl_label = "Remove All Missing Layers"
    bl_description = "Remove all current container missing layers"
    bl_icon = "BRUSH_DATA"

    success_msg = "Successfully removed all missing layers."

    def get_layers(self, context):
        def is_missing(layer_obj):
            return is_missing_layer(layer_obj)
        return get_all_layers(is_missing)

    def invoke(self, context, event):
        context.window_manager.invoke_confirm(self,
                                              event,
                                              message=f"Are you sure to remove all **Missing** layers?")
        return {'RUNNING_MODAL'}
