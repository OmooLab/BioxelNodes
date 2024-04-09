from .nodes import custom_nodes
from . import auto_load
from .dicom import MEDNODES_add_topbar_menu
import bpy


bl_info = {
    "name": "MedNodes",
    "author": "Ma Nan",
    "description": "",
    "blender": (4, 0, 0),
    "version": (0, 1, 0),
    "location": "File -> Import",
    "warning": "",
    "category": "Import-Export"
}

auto_load.init()


def register():
    auto_load.register()
    custom_nodes.register()
    bpy.types.TOPBAR_MT_file_import.prepend(MEDNODES_add_topbar_menu)


def unregister():
    try:
        bpy.types.TOPBAR_MT_file_import.remove(MEDNODES_add_topbar_menu)
        custom_nodes.unregister()
        auto_load.unregister()
    except RuntimeError:
        pass
