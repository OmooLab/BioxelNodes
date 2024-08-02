import bpy
from pathlib import Path
from .. import __package__ as base_package


def change_render_setting(context):
    preferences = get_preferences(context)
    if preferences.do_change_render_setting:
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
            bpy.context.scene.eevee.use_volumetric_shadows = True
        except:
            pass


def select_object(target_obj):
    for obj in bpy.data.objects:
        obj.select_set(False)

    target_obj.select_set(True)
    bpy.context.view_layer.objects.active = target_obj


def progress_bar(self, context):
    row = self.layout.row()
    row.progress(
        factor=context.window_manager.bioxelnodes_progress_factor,
        type="BAR",
        text=context.window_manager.bioxelnodes_progress_text
    )
    row.scale_x = 2


def progress_update(context, factor, text=""):
    context.window_manager.bioxelnodes_progress_factor = factor
    context.window_manager.bioxelnodes_progress_text = text


def get_preferences(context):
    return context.preferences.addons[base_package].preferences


def get_cache_dir(context):
    preferences = get_preferences(context)
    cache_path = Path(preferences.cache_dir, 'VDBs')
    cache_path.mkdir(parents=True, exist_ok=True)
    return str(cache_path)
