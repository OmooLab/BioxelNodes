import bpy
from .operators import ConvertToMesh, JoinLayers
from .io import ExportVDB, ImportVolumeData, AddVolumeData
from .misc import SaveBioxelLayers


class View3DBioxelsMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_VIEW3D"
    bl_label = "Bioxel Nodes"

    def draw(self, context):
        layout = self.layout
        layout.operator(ConvertToMesh.bl_idname)
        layout.operator(AddVolumeData.bl_idname)
        layout.separator()
        layout.operator(SaveBioxelLayers.bl_idname)


class OutlinerBioxelsMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_OUTLINER"
    bl_label = "Bioxel Nodes"

    def draw(self, context):
        layout = self.layout
        layout.operator(JoinLayers.bl_idname)
        layout.operator(ConvertToMesh.bl_idname)
        layout.operator(AddVolumeData.bl_idname)
        layout.separator()
        layout.operator(SaveBioxelLayers.bl_idname)


def TOPBAR_FILE_IMPORT(self, context):
    layout = self.layout
    layout.separator()
    layout.operator(ImportVolumeData.bl_idname)


def TOPBAR_FILE_EXPORT(self, context):
    layout = self.layout
    layout.separator()
    layout.operator(ExportVDB.bl_idname)


def VIEW3D_OBJECT(self, context):
    layout = self.layout
    layout.menu(View3DBioxelsMenu.bl_idname)
    layout.separator()


def OUTLINER_OBJECT(self, context):
    layout = self.layout
    layout.menu(OutlinerBioxelsMenu.bl_idname)
    layout.separator()


def add():
    bpy.types.TOPBAR_MT_file_import.append(TOPBAR_FILE_IMPORT)
    bpy.types.TOPBAR_MT_file_export.append(TOPBAR_FILE_EXPORT)
    bpy.types.OUTLINER_MT_object.prepend(OUTLINER_OBJECT)
    bpy.types.VIEW3D_MT_object_context_menu.prepend(VIEW3D_OBJECT)


def remove():
    bpy.types.TOPBAR_MT_file_import.remove(TOPBAR_FILE_IMPORT)
    bpy.types.TOPBAR_MT_file_export.remove(TOPBAR_FILE_EXPORT)
    bpy.types.OUTLINER_MT_object.remove(OUTLINER_OBJECT)
    bpy.types.VIEW3D_MT_object_context_menu.remove(VIEW3D_OBJECT)
