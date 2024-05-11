import bpy

from .nodes import custom_nodes
from . import auto_load


bl_info = {
    "name": "Bioxel Nodes",
    "author": "Ma Nan",
    "description": "",
    "blender": (4, 0, 0),
    "version": (0, 1, 0),
    "location": "File -> Import",
    "warning": "",
    "category": "Node"
}

auto_load.init()


def register():
    auto_load.register()
    bpy.types.Scene.bioxels_dir = bpy.props.StringProperty(
        name="Bioxels Directory",
        subtype='DIR_PATH',
        default="//"
    )


def unregister():
    try:
        auto_load.unregister()
    except RuntimeError:
        pass
