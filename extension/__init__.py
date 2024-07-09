import bpy

from . import auto_load
from . import menus


auto_load.init()


def register():
    auto_load.register()
    menus.add()


def unregister():
    menus.remove()
    auto_load.unregister()
