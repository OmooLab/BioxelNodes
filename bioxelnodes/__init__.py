import bpy

from . import auto_load
from . import menus


bl_info = {
    "name": "Bioxel Nodes",
    "author": "Ma Nan",
    "description": "",
    "blender": (4, 0, 0),
    "version": (0, 1, 1),
    "location": "File -> Import",
    "warning": "",
    "category": "Node"
}

auto_load.init()


def register():
    auto_load.register()
    menus.add()
    bpy.types.Scene.bioxels_dir = bpy.props.StringProperty(
        name="Bioxels Directory",
        subtype='DIR_PATH',
        default="//"
    )


def unregister():
    menus.remove()
    auto_load.unregister()
