from pathlib import Path
import shutil
import bpy


def copy_to_dir(source_path, dir_path, new_name=None, exist_ok=True):
    source = Path(source_path)
    target = Path(dir_path)

    # Check if the source exists
    if not source.exists():
        raise FileNotFoundError

    # Check if the target exists
    if not target.exists():
        target.mkdir(parents=True, exist_ok=True)

    target_path = target / new_name if new_name else target / source.name
    # If source is a file, copy it to the target directory
    if source.is_file():
        try:
            shutil.copy(source, target_path)
        except shutil.SameFileError:
            if exist_ok:
                pass
            else:
                raise shutil.SameFileError
    # If source is a directory, copy its contents to the target directory
    elif source.is_dir():
        shutil.copytree(source, target_path, dirs_exist_ok=exist_ok)

    if not target_path.exists():
        raise Exception


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


def get_preferences():
    return bpy.context.preferences.addons[__package__].preferences


def get_cache_dir():
    preferences = get_preferences()
    cache_path = Path(preferences.cache_dir, 'VDBs')
    cache_path.mkdir(parents=True, exist_ok=True)
    return str(cache_path)


def get_use_link():
    preferences = get_preferences()
    return preferences.node_import_method == "LINK"
