import bpy

from . import auto_load
from . import menus


bl_info = {
    "name": "Bioxel Nodes",
    "author": "Ma Nan",
    "description": "",
    "blender": (4, 1, 0),
    "version": (0, 2, 7),
    "location": "File -> Import",
    "warning": "",
    "category": "Node"
}

auto_load.init()


def register():
    auto_load.register()
    menus.add()


def unregister():
    menus.remove()
    auto_load.unregister()
