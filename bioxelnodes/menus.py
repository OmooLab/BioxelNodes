import bpy
from .operators import (AddPlaneCutter, AddCylinderCutter, AddCubeCutter, AddSphereCutter, CombineLabels,
                        ConvertToMesh, InvertScalar, FillByLabel, FillByThreshold, FillByRange)
from .io import ExportVolumeData, ImportAsLabelLayer, ImportAsScalarLayer, ImportVolumeData, AddVolumeData
from .misc import SaveLayers


class ModifyLayer(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_MODIFY_LAYERS"
    bl_label = "Modify Layer"

    def draw(self, context):
        layout = self.layout
        layout.operator(InvertScalar.bl_idname)
        layout.operator(FillByThreshold.bl_idname)
        layout.operator(FillByRange.bl_idname)
        layout.operator(FillByLabel.bl_idname)
        layout.operator(CombineLabels.bl_idname)


class AddCutterMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_CUTTERS"
    bl_label = "Add Cutter"

    def draw(self, context):
        layout = self.layout
        layout.operator(AddPlaneCutter.bl_idname)
        layout.operator(AddCylinderCutter.bl_idname)
        layout.operator(AddCubeCutter.bl_idname)
        layout.operator(AddSphereCutter.bl_idname)


class ImportLayerMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_LAYERS"
    bl_label = "Import Layer"

    def draw(self, context):
        layout = self.layout
        layout.operator(ImportAsScalarLayer.bl_idname)
        layout.operator(ImportAsLabelLayer.bl_idname)


class BioxelNodesView3DMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_VIEW3D"
    bl_label = "Bioxel Nodes"

    def draw(self, context):
        layout = self.layout
        layout.menu(ImportLayerMenu.bl_idname)
        layout.menu(AddCutterMenu.bl_idname)
        layout.operator(ConvertToMesh.bl_idname)
        layout.separator()
        layout.operator(SaveLayers.bl_idname)


class BioxelNodesOutlinerMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_OUTLINER"
    bl_label = "Bioxel Nodes"

    def draw(self, context):
        layout = self.layout
        layout.menu(ImportLayerMenu.bl_idname)
        layout.menu(AddCutterMenu.bl_idname)
        layout.operator(ConvertToMesh.bl_idname)
        layout.separator()
        layout.menu(ModifyLayer.bl_idname)
        layout.separator()
        layout.operator(SaveLayers.bl_idname)


# def TOPBAR_FILE_IMPORT(self, context):
#     layout = self.layout
#     layout.separator()
#     layout.operator(ImportVolumeData.bl_idname)


# def TOPBAR_FILE_EXPORT(self, context):
#     layout = self.layout
#     layout.separator()
#     layout.operator(ExportVolumeData.bl_idname)


def VIEW3D_OBJECT(self, context):
    layout = self.layout
    layout.menu(BioxelNodesView3DMenu.bl_idname)
    layout.separator()


def OUTLINER_OBJECT(self, context):
    layout = self.layout
    layout.menu(BioxelNodesOutlinerMenu.bl_idname)
    layout.separator()


class BioxelNodesTopbarMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_TOPBAR"
    bl_label = "Bioxel Nodes"

    def draw(self, context):
        layout = self.layout
        layout.menu(ImportLayerMenu.bl_idname)
        layout.operator(ExportVolumeData.bl_idname)
        layout.separator()
        layout.menu(AddCutterMenu.bl_idname)
        layout.operator(ConvertToMesh.bl_idname)
        layout.separator()
        layout.operator(SaveLayers.bl_idname)


def TOPBAR(self, context):
    layout = self.layout
    layout.menu(BioxelNodesTopbarMenu.bl_idname)


def add():
    # bpy.types.TOPBAR_MT_file_import.append(TOPBAR_FILE_IMPORT)
    # bpy.types.TOPBAR_MT_file_export.append(TOPBAR_FILE_EXPORT)
    bpy.types.OUTLINER_MT_object.prepend(OUTLINER_OBJECT)
    bpy.types.VIEW3D_MT_object_context_menu.prepend(VIEW3D_OBJECT)
    bpy.types.TOPBAR_MT_editor_menus.append(TOPBAR)


def remove():
    # bpy.types.TOPBAR_MT_file_import.remove(TOPBAR_FILE_IMPORT)
    # bpy.types.TOPBAR_MT_file_export.remove(TOPBAR_FILE_EXPORT)
    bpy.types.OUTLINER_MT_object.remove(OUTLINER_OBJECT)
    bpy.types.VIEW3D_MT_object_context_menu.remove(VIEW3D_OBJECT)
    bpy.types.TOPBAR_MT_editor_menus.remove(TOPBAR)
