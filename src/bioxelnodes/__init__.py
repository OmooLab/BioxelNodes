import bpy
import bpy.utils.previews as previews

from .constants import PREVIEW_COLLECTIONS
from .asset_library import remove_bioxel_asset_library_if_exists
from .props import _bioxel_layer_items, _update_layer_gallery, _update_snapshot_z

from . import auto_load
from . import menus

auto_load.init()

CLI_COMMAND_NAME = "bioxelnodes_import_worker"


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
    register_cli_commands()


def unregister():
    remove_bioxel_asset_library_if_exists()
    unregister_cli_commands()
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


def import_worker_cli(args):
    from .operators import io_worker

    return io_worker.main(args)


def register_cli_commands():
    unregister_cli_commands()
    bpy.utils.register_cli_command(CLI_COMMAND_NAME, import_worker_cli)


def unregister_cli_commands():
    try:
        bpy.utils.unregister_cli_command(CLI_COMMAND_NAME)
    except Exception:
        pass
