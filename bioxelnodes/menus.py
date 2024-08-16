from pathlib import Path
import bpy

from .operators.utils import get_layer_item_label
from .bioxelutils.utils import (get_container_obj,
                                get_container_objs_from_selection,
                                get_container_layer_objs,
                                get_layer_prop_value)
from .operators.layer import (FetchLayerMenu, FetchLayer,
                              RemoveLayer, RemoveMissingLayers, RenameLayer, ResampleScalar, SaveLayerCache,
                              SignScalar, CombineLabels,
                              FillByLabel, FillByThreshold, FillByRange, get_selected_objs_in_node_tree)
from .operators.container import (SaveAllLayerCaches, SaveContainer, LoadContainer,
                                  AddPieCutter, AddPlaneCutter,
                                  AddCylinderCutter, AddCubeCutter, AddSphereCutter,
                                  PickBboxWire, PickMesh, PickVolume, ScaleContainer)
from .operators.io import (ImportAsLabel, ImportAsScalar, ImportAsColor)
from .operators.misc import (CleanAllCaches,
                             ReLinkNodes, RenderSettingPreset, SaveStagedData, SliceViewer)


class PickFromContainerMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_PICK"
    bl_label = "Pick from Container"

    def draw(self, context):
        layout = self.layout
        layout.operator(PickMesh.bl_idname)
        layout.operator(PickVolume.bl_idname)
        layout.operator(PickBboxWire.bl_idname)


class AddCutterMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_CUTTERS"
    bl_label = "Add a Object Cutter"

    def draw(self, context):
        layout = self.layout
        layout.operator(AddPlaneCutter.bl_idname, text="Plane Cutter")
        layout.operator(AddCylinderCutter.bl_idname, text="Cylinder Cutter")
        layout.operator(AddCubeCutter.bl_idname, text="Cube Cutter")
        layout.operator(AddSphereCutter.bl_idname, text="Sphere Cutter")
        layout.operator(AddPieCutter.bl_idname, text="Pie Cutter")


class ImportLayerMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_IMPORTLAYER"
    bl_label = "Import Volumetric Data (Init)"
    bl_icon = "FILE_NEW"

    def draw(self, context):
        layout = self.layout
        layout.operator(ImportAsScalar.bl_idname,
                        text="as Scalar")
        layout.operator(ImportAsLabel.bl_idname,
                        text="as Label")
        layout.operator(ImportAsColor.bl_idname,
                        text="as Color")


class AddLayerMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_ADDLAYER"
    bl_label = "Import Volumetric Data (Add to)"
    bl_icon = "FILE_NEW"

    def draw(self, context):
        layout = self.layout
        layout.operator(ImportAsScalar.bl_idname,
                        text="as Scalar")
        layout.operator(ImportAsLabel.bl_idname,
                        text="as Label")
        layout.operator(ImportAsColor.bl_idname,
                        text="as Color")


class ModifyLayerMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_MODIFYLAYER"
    bl_label = "Modify Layer"
    bl_icon = "FILE_NEW"

    def draw(self, context):
        layer_objs = get_selected_objs_in_node_tree(context)
        if len(layer_objs) > 0:
            active_obj_name = layer_objs[0].name
        else:
            active_obj_name = ""

        layout = self.layout
        op = layout.operator(ResampleScalar.bl_idname,
                             icon=ResampleScalar.bl_icon)
        op.layer_obj_name = active_obj_name
        op = layout.operator(SignScalar.bl_idname,
                             icon=SignScalar.bl_icon)
        op.layer_obj_name = active_obj_name
        op = layout.operator(FillByThreshold.bl_idname,
                             icon=FillByThreshold.bl_icon)
        op.layer_obj_name = active_obj_name
        op = layout.operator(FillByRange.bl_idname,
                             icon=FillByRange.bl_icon)
        op.layer_obj_name = active_obj_name
        op = layout.operator(FillByLabel.bl_idname,
                             icon=FillByLabel.bl_icon)
        op.layer_obj_name = active_obj_name
        op = layout.operator(CombineLabels.bl_idname,
                             icon=CombineLabels.bl_icon)
        op.layer_obj_name = active_obj_name


class RenderSettingMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_RENDER"
    bl_label = "Render Setting Presets"

    def draw(self, context):
        layout = self.layout
        for k, v in RenderSettingPreset.PRESETS.items():
            op = layout.operator(RenderSettingPreset.bl_idname,
                                 text=v)
            op.preset = k


class BioxelNodesTopbarMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_TOPBAR"
    bl_label = "Bioxel Nodes"

    def draw(self, context):
        layout = self.layout

        layout.menu(ImportLayerMenu.bl_idname,
                    icon=ImportLayerMenu.bl_icon)
        layout.operator(LoadContainer.bl_idname)

        layout.separator()
        layout.operator(SaveStagedData.bl_idname)
        layout.operator(ReLinkNodes.bl_idname)
        layout.operator(CleanAllCaches.bl_idname)

        layout.separator()
        layout.menu(RenderSettingMenu.bl_idname)


def TOPBAR(self, context):
    layout = self.layout
    layout.menu(BioxelNodesTopbarMenu.bl_idname)


class BioxelNodesNodeMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_NODE"
    bl_label = "Bioxel Nodes"
    bl_icon = "FILE_VOLUME"

    def draw(self, context):
        layer_objs = get_selected_objs_in_node_tree(context)
        if len(layer_objs) > 0:
            active_obj_name = layer_objs[0].name
        else:
            active_obj_name = ""

        layout = self.layout
        layout.separator()
        layout.menu(AddLayerMenu.bl_idname,
                    icon=AddLayerMenu.bl_icon)
        layout.separator()
        layout.operator(SaveContainer.bl_idname)
        layout.separator()
        layout.operator(ScaleContainer.bl_idname)
        layout.menu(AddCutterMenu.bl_idname)
        layout.menu(PickFromContainerMenu.bl_idname)
        layout.operator(SaveAllLayerCaches.bl_idname,
                        icon=SaveAllLayerCaches.bl_icon)
        layout.operator(RemoveMissingLayers.bl_idname,
                        icon=RemoveMissingLayers.bl_icon)

        layout.separator()
        layout.menu(FetchLayerMenu.bl_idname)
        op = layout.operator(SaveLayerCache.bl_idname,
                             icon=SaveLayerCache.bl_icon)
        op.layer_obj_name = active_obj_name
        op = layout.operator(RenameLayer.bl_idname,
                             icon=RenameLayer.bl_icon)
        op.layer_obj_name = active_obj_name

        op = layout.operator(RemoveLayer.bl_idname,
                             icon=RemoveLayer.bl_icon)
        op.layer_obj_name = active_obj_name

        layout.separator()
        layout.menu(ModifyLayerMenu.bl_idname)


def NODE(self, context):
    container_obj = context.object
    is_geo_nodes = context.area.ui_type == "GeometryNodeTree"
    is_container = get_container_obj(container_obj)

    if not is_geo_nodes or not is_container:
        return

    layout = self.layout
    layout.separator()
    layout.menu(BioxelNodesNodeMenu.bl_idname)


def NODE_PT(self, context):
    container_obj = context.object
    is_geo_nodes = context.area.ui_type == "GeometryNodeTree"
    is_container = get_container_obj(container_obj)
    self.bl_label = "Group"

    if not is_geo_nodes or not is_container:
        return

    if container_obj.modifiers[0].node_group != context.space_data.edit_tree:
        return

    self.bl_label = "Bioxel Nodes"

    layer_list_UL = bpy.context.window_manager.bioxelnodes_layer_list_UL
    layer_list = layer_list_UL.layer_list
    layer_list_active = layer_list_UL.layer_list_active
    layer_list.clear()

    for layer_obj in get_container_layer_objs(container_obj):
        layer_item = layer_list.add()
        layer_item.label = get_layer_item_label(context, layer_obj)
        layer_item.obj_name = layer_obj.name
        layer_item.info_text = "\n".join([f"{prop}: {get_layer_prop_value(layer_obj, prop)}"
                                          for prop in ["kind", "bioxel_size", "shape", "min", "max", ]])

    if len(layer_list) > 0 and layer_list_active != -1 and layer_list_active < len(layer_list):
        active_obj_name = layer_list[layer_list_active].obj_name
    else:
        active_obj_name = ""

    layout = self.layout
    layout.label(text="Layer List")
    split = layout.row()
    split.template_list(listtype_name="BIOXELNODES_UL_layer_list",
                        list_id="layer_list",
                        dataptr=layer_list_UL,
                        propname="layer_list",
                        active_dataptr=layer_list_UL,
                        active_propname="layer_list_active",
                        item_dyntip_propname="info_text",
                        rows=20)

    sidebar = split.column(align=True)
    sidebar.menu(AddLayerMenu.bl_idname,
                 icon=AddLayerMenu.bl_icon, text="")

    sidebar.operator(SaveAllLayerCaches.bl_idname,
                    icon=SaveAllLayerCaches.bl_icon, text="")
    sidebar.operator(RemoveMissingLayers.bl_idname,
                     icon=RemoveMissingLayers.bl_icon, text="")

    sidebar.separator()
    op = sidebar.operator(FetchLayer.bl_idname,
                          icon=FetchLayer.bl_icon, text="")
    op.layer_obj_name = active_obj_name
    op = sidebar.operator(SaveLayerCache.bl_idname,
                          icon=SaveLayerCache.bl_icon, text="")
    op.layer_obj_name = active_obj_name
    op = sidebar.operator(RenameLayer.bl_idname,
                          icon=RenameLayer.bl_icon, text="")
    op.layer_obj_name = active_obj_name
    op = sidebar.operator(RemoveLayer.bl_idname,
                          icon=RemoveLayer.bl_icon, text="")
    op.layer_obj_name = active_obj_name

    sidebar.separator()
    op = sidebar.operator(ResampleScalar.bl_idname,
                          icon=ResampleScalar.bl_icon, text="")
    op.layer_obj_name = active_obj_name
    op = sidebar.operator(SignScalar.bl_idname,
                          icon=SignScalar.bl_icon, text="")
    op.layer_obj_name = active_obj_name
    op = sidebar.operator(FillByThreshold.bl_idname,
                          icon=FillByThreshold.bl_icon, text="")
    op.layer_obj_name = active_obj_name
    op = sidebar.operator(FillByRange.bl_idname,
                          icon=FillByRange.bl_icon, text="")
    op.layer_obj_name = active_obj_name
    op = sidebar.operator(FillByLabel.bl_idname,
                          icon=FillByLabel.bl_icon, text="")
    op.layer_obj_name = active_obj_name

    sidebar.separator()
    layout.separator()


def VIEW3D_TOPBAR(self, context):
    layout = self.layout
    layout.operator(SliceViewer.bl_idname,
                    icon=SliceViewer.bl_icon, text="")


def add():
    bpy.types.VIEW3D_HT_header.append(VIEW3D_TOPBAR)
    bpy.types.NODE_PT_node_tree_properties.prepend(NODE_PT)
    bpy.types.TOPBAR_MT_editor_menus.append(TOPBAR)
    bpy.types.NODE_MT_editor_menus.append(NODE)


def remove():
    bpy.types.VIEW3D_HT_header.remove(VIEW3D_TOPBAR)
    bpy.types.NODE_PT_node_tree_properties.remove(NODE_PT)
    bpy.types.TOPBAR_MT_editor_menus.remove(TOPBAR)
    bpy.types.NODE_MT_editor_menus.remove(NODE)
