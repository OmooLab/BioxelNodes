import bpy
from pathlib import Path
from .. import __package__ as base_package


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
