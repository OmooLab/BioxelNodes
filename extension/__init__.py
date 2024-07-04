import bpy

from . import auto_load
from . import menus


auto_load.init()


def register():
    auto_load.register()
    menus.add()
    bpy.types.Scene.bioxel_layer_dir = bpy.props.StringProperty(
        name="Layer Directory",
        subtype='DIR_PATH',
        default="//"
    )


def unregister():
    menus.remove()
    auto_load.unregister()
