import bpy

from .props import BIOXELNODES_LayerListUL
from . import auto_load
from . import menus


auto_load.init()


def register():
    auto_load.register()
    bpy.types.WindowManager.bioxelnodes_progress_factor = bpy.props.FloatProperty(
        default=1.0)
    bpy.types.WindowManager.bioxelnodes_progress_text = bpy.props.StringProperty()
    bpy.types.WindowManager.bioxelnodes_layer_list_UL = bpy.props.PointerProperty(
        type=BIOXELNODES_LayerListUL)
    menus.add()


def unregister():
    menus.remove()
    del bpy.types.WindowManager.bioxelnodes_progress_factor
    del bpy.types.WindowManager.bioxelnodes_progress_text
    del bpy.types.WindowManager.bioxelnodes_layer_list_UL
    auto_load.unregister()
