import bpy

from . import auto_load
from . import menus


bl_info = {
    "name": "Bioxel Nodes",
    "author": "Ma Nan",
    "description": "",
    "blender": (4, 0, 0),
    "version": (0, 2, 0),
    "location": "File -> Import",
    "warning": "",
    "category": "Node"
}

auto_load.init()


def register():
    auto_load.register()
    menus.add()
    bpy.types.Scene.bioxel_layer_dir = bpy.props.StringProperty(
        name="Bioxel Layers Directory",
        subtype='DIR_PATH',
        default="//"
    )


def unregister():
    menus.remove()
    auto_load.unregister()
