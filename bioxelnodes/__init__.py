import bpy

from . import auto_load
from . import menus


bl_info = {
    "name": "Bioxel Nodes",
    "author": "Ma Nan",
    "description": "",
    "blender": (4, 1, 0),
    "version": (0, 2, 9),
    "location": "File -> Import",
    "warning": "",
    "category": "Node"
}

auto_load.init()


def register():
    auto_load.register()
    bpy.types.WindowManager.bioxelnodes_progress_factor = bpy.props.FloatProperty()
    bpy.types.WindowManager.bioxelnodes_progress_text = bpy.props.StringProperty()
    menus.add()


def unregister():
    menus.remove()
    auto_load.unregister()
