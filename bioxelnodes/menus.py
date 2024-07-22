import bpy

from .utils import get_container_from_selection
from .operators import (AddPieCutter, AddPlaneCutter, AddCylinderCutter, AddCubeCutter, AddSphereCutter, CombineLabels,
                        ConvertToMesh, InvertScalar, FillByLabel, FillByThreshold, FillByRange, PickBboxWire, PickMesh, PickVolume)
from .io import ExportVolumetricData, ImportAsLabelLayer, ImportAsScalarLayer
from .save import CleanAllCaches, ReLinkNodes, SaveLayers, SaveStagedData


class PickFromContainerMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_PICK"
    bl_label = "Pick from Container"

    def draw(self, context):
        layout = self.layout
        layout.operator(PickMesh.bl_idname)
        layout.operator(PickVolume.bl_idname)
        layout.operator(PickBboxWire.bl_idname)


class ModifyLayerMenu(bpy.types.Menu):
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
    bl_label = "Add a Cutter to Container"

    def draw(self, context):
        layout = self.layout
        layout.operator(AddPlaneCutter.bl_idname, text="Plane Cutter")
        layout.operator(AddCylinderCutter.bl_idname, text="Cylinder Cutter")
        layout.operator(AddCubeCutter.bl_idname, text="Cube Cutter")
        layout.operator(AddSphereCutter.bl_idname, text="Sphere Cutter")
        layout.operator(AddPieCutter.bl_idname, text="Pie Cutter")


class ImportLayerMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_LAYERS"
    bl_label = "Import Volumetric Data"

    def draw(self, context):
        layout = self.layout
        layout.operator(ImportAsScalarLayer.bl_idname, text="as Scalar")
        layout.operator(ImportAsLabelLayer.bl_idname, text="as Label")


class BioxelNodesView3DMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_VIEW3D"
    bl_label = "Bioxel Nodes"

    def draw(self, context):
        layout = self.layout
        containers = get_container_from_selection()
        is_selected = len(containers) > 0
        layout.operator(ImportAsScalarLayer.bl_idname,
                        text=ImportAsScalarLayer.bl_label+" (Add to)"
                        if is_selected else ImportAsScalarLayer.bl_label+" (Init)")
        layout.operator(ImportAsLabelLayer.bl_idname,
                        text=ImportAsLabelLayer.bl_label+" (Add to)"
                        if is_selected else ImportAsLabelLayer.bl_label+" (Init)")
        layout.separator()
        layout.operator(AddPlaneCutter.bl_idname)
        layout.operator(AddCylinderCutter.bl_idname)
        layout.operator(AddCubeCutter.bl_idname)
        layout.operator(AddSphereCutter.bl_idname)
        layout.operator(AddPieCutter.bl_idname)
        layout.separator()
        layout.operator(PickMesh.bl_idname)
        layout.operator(PickVolume.bl_idname)
        layout.operator(PickBboxWire.bl_idname)
        layout.separator()
        layout.operator(SaveLayers.bl_idname)


class BioxelNodesOutlinerMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_OUTLINER"
    bl_label = "Bioxel Nodes"

    def draw(self, context):
        layout = self.layout
        containers = get_container_from_selection()
        is_selected = len(containers) > 0
        layout.operator(ImportAsScalarLayer.bl_idname,
                        text=ImportAsScalarLayer.bl_label+" (Add to)"
                        if is_selected else ImportAsScalarLayer.bl_label+" (Init)")
        layout.operator(ImportAsLabelLayer.bl_idname,
                        text=ImportAsLabelLayer.bl_label+" (Add to)"
                        if is_selected else ImportAsLabelLayer.bl_label+" (Init)")
        layout.separator()
        layout.operator(AddPlaneCutter.bl_idname)
        layout.operator(AddCylinderCutter.bl_idname)
        layout.operator(AddCubeCutter.bl_idname)
        layout.operator(AddSphereCutter.bl_idname)
        layout.operator(AddPieCutter.bl_idname)
        layout.separator()
        layout.operator(PickMesh.bl_idname)
        layout.operator(PickVolume.bl_idname)
        layout.operator(PickBboxWire.bl_idname)
        layout.separator()
        layout.operator(SaveLayers.bl_idname)
        layout.separator()
        layout.operator(InvertScalar.bl_idname)
        layout.operator(FillByThreshold.bl_idname)
        layout.operator(FillByRange.bl_idname)
        layout.operator(FillByLabel.bl_idname)
        layout.operator(CombineLabels.bl_idname)
        layout.separator()
        layout.operator(ExportVolumetricData.bl_idname)


def TOPBAR_FILE_IMPORT(self, context):
    layout = self.layout
    containers = get_container_from_selection()
    is_selected = len(containers) > 0

    layout.separator()
    layout.menu(ImportLayerMenu.bl_idname, text="Volumetric Data as Bioxel (Add to)"
                if is_selected else "Volumetric Data as Bioxel (Init)")


def TOPBAR_FILE_EXPORT(self, context):
    layout = self.layout
    layout.separator()
    layout.operator(ExportVolumetricData.bl_idname,
                    text="Bioxel Layer (.vdb)")


def VIEW3D_OBJECT(self, context):
    layout = self.layout
    layout.separator()
    layout.menu(BioxelNodesView3DMenu.bl_idname, icon="FILE_VOLUME")


def OUTLINER_OBJECT(self, context):
    layout = self.layout
    layout.separator()
    layout.menu(BioxelNodesOutlinerMenu.bl_idname, icon="FILE_VOLUME")


class BioxelNodesTopbarMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_TOPBAR"
    bl_label = "Bioxel Nodes"

    def draw(self, context):
        layout = self.layout
        containers = get_container_from_selection()
        is_selected = len(containers) > 0

        layout.menu(ImportLayerMenu.bl_idname, text=ImportLayerMenu.bl_label+" (Add to)"
                    if is_selected else ImportLayerMenu.bl_label+" (Init)")
        layout.separator()
        layout.menu(AddCutterMenu.bl_idname)
        layout.menu(PickFromContainerMenu.bl_idname)
        layout.separator()
        layout.operator(SaveStagedData.bl_idname)
        layout.operator(ReLinkNodes.bl_idname)
        layout.separator()
        layout.operator(CleanAllCaches.bl_idname)


def TOPBAR(self, context):
    layout = self.layout
    layout.menu(BioxelNodesTopbarMenu.bl_idname)
    
    
def add():
    bpy.types.TOPBAR_MT_file_import.append(TOPBAR_FILE_IMPORT)
    bpy.types.TOPBAR_MT_file_export.append(TOPBAR_FILE_EXPORT)
    bpy.types.OUTLINER_MT_object.append(OUTLINER_OBJECT)
    bpy.types.VIEW3D_MT_object_context_menu.append(VIEW3D_OBJECT)
    bpy.types.TOPBAR_MT_editor_menus.append(TOPBAR)


def remove():
    bpy.types.TOPBAR_MT_file_import.remove(TOPBAR_FILE_IMPORT)
    bpy.types.TOPBAR_MT_file_export.remove(TOPBAR_FILE_EXPORT)
    bpy.types.OUTLINER_MT_object.remove(OUTLINER_OBJECT)
    bpy.types.VIEW3D_MT_object_context_menu.remove(VIEW3D_OBJECT)
    bpy.types.TOPBAR_MT_editor_menus.remove(TOPBAR)
