import bpy
from pathlib import Path
import shutil
from .utils import get_cache_dir
from ..nodes import custom_nodes
from ..bioxelutils.utils import (get_container_objs_from_selection,
                                 get_all_layer_objs,
                                 get_container_layer_objs)

CLASS_PREFIX = "BIOXELNODES_MT_NODES"


class ReLinkNodes(bpy.types.Operator):
    bl_idname = "bioxelnodes.relink_nodes"
    bl_label = "Relink Nodes to Addon"
    bl_description = "Relink all nodes to addon source"

    def execute(self, context):
        file_name = Path(custom_nodes.nodes_file).name
        for lib in bpy.data.libraries:
            lib_path = Path(bpy.path.abspath(lib.filepath)).resolve()
            lib_name = lib_path.name
            if lib_name == file_name:
                if str(lib_path) != custom_nodes.nodes_file:
                    lib.filepath = custom_nodes.nodes_file

        self.report({"INFO"}, f"Successfully relinked.")

        return {'FINISHED'}


class SaveStagedData(bpy.types.Operator):
    bl_idname = "bioxelnodes.save_staged_data"
    bl_label = "Save Staged Data"
    bl_description = "Save all staged data in this file for sharing"

    save_cache: bpy.props.BoolProperty(
        name="Save Layer Caches",
        default=True,
    )  # type: ignore

    cache_dir: bpy.props.StringProperty(
        name="Cache Directory",
        subtype='DIR_PATH',
        default="//"
    )  # type: ignore

    save_lib: bpy.props.BoolProperty(
        name="Save Node Library File",
        default=True,
    )  # type: ignore

    lib_dir: bpy.props.StringProperty(
        name="Library Directory",
        subtype='DIR_PATH',
        default="//"
    )  # type: ignore

    def execute(self, context):
        if self.save_lib:
            files = []
            for classname in dir(bpy.types):
                if CLASS_PREFIX in classname:
                    cls = getattr(bpy.types, classname)
                    files.append(cls.nodes_file)
            files = list(set(files))

            for file in files:
                file_name = Path(file).name
                # "//"
                lib_dir = bpy.path.abspath(self.lib_dir)

                output_path: Path = Path(lib_dir, file_name).resolve()
                source_path: Path = Path(file).resolve()

                if output_path != source_path:
                    shutil.copy(source_path, output_path)

                for lib in bpy.data.libraries:
                    lib_path = Path(bpy.path.abspath(lib.filepath)).resolve()
                    if lib_path == source_path:
                        blend_path = Path(bpy.path.abspath("//")).resolve()
                        lib.filepath = bpy.path.relpath(
                            str(output_path), start=str(blend_path))

                self.report({"INFO"}, f"Successfully saved to {output_path}")

        if self.save_cache:
            fails = []
            for layer_obj in get_all_layer_objs():
                try:
                    bpy.ops.bioxelnodes.save_layer_cache('EXEC_DEFAULT',
                                                         layer_obj_name=layer_obj.name,
                                                         cache_dir=self.cache_dir)
                except:
                    fails.append(layer_obj)

            if len(fails) == 0:
                self.report({"INFO"}, f"Successfully saved bioxel layers.")
            else:
                self.report(
                    {"WARNING"}, f"{','.join([layer_obj.name for layer_obj in fails])} fail to save.")

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_props_dialog(self,
                                                   width=500)
        return {'RUNNING_MODAL'}

    @classmethod
    def poll(cls, context):
        return bpy.data.is_saved

    def draw(self, context):
        layout = self.layout
        panel = layout.box()
        panel.prop(self, "save_cache")
        panel.prop(self, "cache_dir")
        panel = layout.box()
        panel.prop(self, "save_lib")
        panel.prop(self, "lib_dir")


class CleanAllCaches(bpy.types.Operator):
    bl_idname = "bioxelnodes.clear_all_caches"
    bl_label = "Clean All Caches in Temp"
    bl_description = "Clean all caches saved in temp"

    def execute(self, context):
        cache_dir = get_cache_dir(context)
        try:
            shutil.rmtree(cache_dir)
            self.report({"INFO"}, f"Successfully cleaned caches.")
            return {'FINISHED'}
        except:
            self.report({"WARNING"},
                        "Fail to clean caches, you may do it manually.")
            return {'CANCELLED'}

    def invoke(self, context, event):
        context.window_manager.invoke_confirm(self,
                                              event,
                                              message="All caches will be cleaned, include other project files, do you still want to clean?")
        return {'RUNNING_MODAL'}


class RenderSettingPreset(bpy.types.Operator):
    bl_idname = "bioxelnodes.render_setting_preset"
    bl_label = "Render Setting Preset"
    bl_description = "Render Setting Preset"

    PRESETS = {
        "slice_viewer": "Slice Viewer",
        "eevee_preview": "EEVEE Preview",
        "eevee_production": "EEVEE Production",
        "cycles_preview": "Cycles Preview",
        "cycles_production": "Cycles Production"
    }

    preset: bpy.props.EnumProperty(name="Preset",
                                   default="eevee_preview",
                                   items=[(k, v, "")
                                          for k, v in PRESETS.items()])  # type: ignore

    def execute(self, context):
        if self.preset == "eevee_preview":
            bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
            bpy.context.scene.eevee.use_taa_reprojection = False
            bpy.context.scene.eevee.taa_samples = 16
            bpy.context.scene.eevee.volumetric_tile_size = '2'
            bpy.context.scene.eevee.volumetric_shadow_samples = 128
            bpy.context.scene.eevee.volumetric_samples = 128
            bpy.context.scene.eevee.volumetric_ray_depth = 16
            bpy.context.scene.eevee.use_volumetric_shadows = True

        elif self.preset == "eevee_production":
            bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
            bpy.context.scene.eevee.use_taa_reprojection = False
            bpy.context.scene.eevee.taa_samples = 16
            bpy.context.scene.eevee.volumetric_tile_size = '1'
            bpy.context.scene.eevee.volumetric_shadow_samples = 128
            bpy.context.scene.eevee.volumetric_samples = 256
            bpy.context.scene.eevee.volumetric_ray_depth = 16
            bpy.context.scene.eevee.use_volumetric_shadows = True

        elif self.preset == "cycles_preview":
            bpy.context.scene.render.engine = 'CYCLES'
            bpy.context.scene.cycles.shading_system = True
            bpy.context.scene.cycles.volume_bounces = 12
            bpy.context.scene.cycles.transparent_max_bounces = 16
            bpy.context.scene.cycles.volume_preview_step_rate = 10
            bpy.context.scene.cycles.volume_step_rate = 10

        elif self.preset == "cycles_production":
            bpy.context.scene.render.engine = 'CYCLES'
            bpy.context.scene.cycles.shading_system = True
            bpy.context.scene.cycles.volume_bounces = 16
            bpy.context.scene.cycles.transparent_max_bounces = 32
            bpy.context.scene.cycles.volume_preview_step_rate = 1
            bpy.context.scene.cycles.volume_step_rate = 1

        elif self.preset == "slice_viewer":
            # bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
            bpy.context.scene.eevee.use_taa_reprojection = False
            bpy.context.scene.eevee.taa_samples = 4
            bpy.context.scene.eevee.volumetric_tile_size = '2'
            bpy.context.scene.eevee.volumetric_shadow_samples = 128
            bpy.context.scene.eevee.volumetric_samples = 128
            bpy.context.scene.eevee.volumetric_ray_depth = 1
            bpy.context.scene.eevee.use_volumetric_shadows = False

        return {'FINISHED'}
