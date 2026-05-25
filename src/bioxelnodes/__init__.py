import bpy
import bpy.utils.previews as previews

from .constants import NODE_LIB_DIRPATH, PREVIEW_COLLECTIONS
from .props import _bioxel_layer_items, _update_layer_gallery, _update_snapshot_z

from . import auto_load
from . import menus

auto_load.init()


def add_asset_library():
    """Add Bioxel asset library, ensuring only one exists by removing duplicates first."""
    if not NODE_LIB_DIRPATH.exists():
        print(f"Node library path does not exist - {NODE_LIB_DIRPATH}")
        return

    lib_path_str = str(NODE_LIB_DIRPATH)
    prefs = bpy.context.preferences.filepaths.asset_libraries

    # Add new library
    new_lib = prefs.new()
    new_lib.name = "O Bioxel"
    new_lib.path = lib_path_str
    new_lib.import_method = "PACK"

    print(f"Add Bioxel Nodes library: {lib_path_str}")


def remove_asset_library_if_exists():
    """Remove the Bioxel asset library entry if it was added (by path or name)."""
    lib_path_str = str(NODE_LIB_DIRPATH)
    prefs = bpy.context.preferences.filepaths.asset_libraries

    for lib in list(prefs):
        try:
            if "Bioxel" in lib.name or lib.path == lib_path_str:
                prefs.remove(lib)
        except Exception:
            continue


def register():
    pcoll = previews.new()
    pcoll.layer_previews = ()
    PREVIEW_COLLECTIONS["layers"] = pcoll

    bpy.types.WindowManager.bioxel_progress_factor = bpy.props.FloatProperty(
        default=1.0
    )

    bpy.types.WindowManager.bioxel_progress_text = bpy.props.StringProperty()

    bpy.types.WindowManager.bioxel_layer_library = bpy.props.EnumProperty(
        name="Bioxel Layer Gallery",
        items=_bioxel_layer_items,
        update=_update_layer_gallery,
    )

    bpy.types.WindowManager.bioxel_snapshot_z = bpy.props.FloatProperty(
        name="Snapshot Z",
        default=0.5,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
        update=_update_snapshot_z,
    )

    bpy.types.WindowManager.bioxel_layer_list_index = bpy.props.IntProperty(
        default=0)

    auto_load.register()
    menus.add()
    remove_asset_library_if_exists()
    add_asset_library()


def unregister():
    remove_asset_library_if_exists()
    menus.remove()
    auto_load.unregister()

    del bpy.types.WindowManager.bioxel_progress_factor
    del bpy.types.WindowManager.bioxel_progress_text
    del bpy.types.WindowManager.bioxel_layer_library
    del bpy.types.WindowManager.bioxel_snapshot_z
    del bpy.types.WindowManager.bioxel_layer_list_index

    for pcoll in PREVIEW_COLLECTIONS.values():
        previews.remove(pcoll)
    PREVIEW_COLLECTIONS.clear()
