import bpy
import bpy.utils.previews as previews

from .constants import NODE_LIB_DIRPATH, PREVIEW_COLLECTIONS
from .props import _bioxel_layer_items, _update_layer_gallery, _update_snapshot_z

from . import auto_load
from . import menus

auto_load.init()


def add_asset_library_if_missing():
    """检查并添加Asset Library（如果不存在），使用link导入方式"""
    # 检查路径是否存在
    if not NODE_LIB_DIRPATH.exists():
        print(f"警告: 节点库路径不存在 - {NODE_LIB_DIRPATH}")
        return

    # 转换为字符串路径用于Blender设置
    lib_path_str = str(NODE_LIB_DIRPATH)

    # 检查是否已存在该资产库
    prefs = bpy.context.preferences.filepaths.asset_libraries
    for lib in prefs:
        if lib.path == lib_path_str:
            return  # 已存在，无需添加

    # 添加新的资产库，使用link导入方式
    new_lib = prefs.new()
    new_lib.name = "O Bioxel"  # 资产库名称
    new_lib.path = lib_path_str  # 资产库路径（字符串形式）
    new_lib.import_method = "PACK"  # 设置导入方式为link

    print(f"Add Bioxel Nodes library: {lib_path_str}")


def remove_asset_library_if_exists():
    """Remove the Bioxel asset library entry if it was added (by path or name)."""
    # if path missing, nothing to remove
    lib_path_str = str(NODE_LIB_DIRPATH)
    prefs = bpy.context.preferences.filepaths.asset_libraries

    # iterate over a snapshot of prefs to safely find index
    lib_to_remove = None
    for i, lib in enumerate(list(prefs)):
        try:
            if lib.path == lib_path_str:
                lib_to_remove = lib
                break
        except Exception:
            continue

    if lib_to_remove is not None:
        try:
            prefs.remove(lib_to_remove)
            print(f"Removed Bioxel Nodes library: {lib_path_str}")
        except Exception as e:
            print(f"Warning: failed to remove Bioxel node library: {e}")


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
    add_asset_library_if_missing()


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
