import bpy

from .constants import MENU_ITEMS, VERSIONS
from .node_menu import NodeMenu

from .bioxelutils.common import (get_container_obj,
                                 get_container_layer_objs, get_layer_label,
                                 get_layer_prop_value, get_node_version, is_incompatible)
from .operators.layer import (FetchLayer, RelocateLayer, RetimeLayer, RenameLayer,
                              RemoveSelectedLayers, SaveSelectedLayersCache,
                              ResampleLayer, SignScalar, CombineLabels,
                              FillByLabel, FillByThreshold, FillByRange)
from .operators.container import (AddLocator, AddSlicer, ContainerProps,
                                  SaveContainerLayersCache, RemoveContainerMissingLayers,
                                  SaveContainer, LoadContainer,
                                  AddPieCutter, AddPlaneCutter,
                                  AddCylinderCutter, AddCubeCutter, AddSphereCutter,
                                  ExtractBboxWire, ExtractMesh, ExtractShapeWire,
                                  ExtractNodeMesh, ExtractNodeBboxWire, ExtractNodeShapeWire)

from .operators.io import (ImportAsLabel, ImportAsScalar, ImportAsColor)
from .operators.misc import (AddEeveeEnv, CleanTemp, Help,
                             ReLinkNodeLib, RemoveAllMissingLayers,
                             RenderSettingPreset, SaveAllLayersCache,
                             SaveNodeLib, SliceViewer)


class IncompatibleMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_INCOMPATIBLE"
    bl_label = "Bioxel Nodes"

    def draw(self, context):
        tip_text = "please downgrade addon version."
        node_version = get_node_version()
        if node_version:
            version_str = "v"+".".join([str(i) for i in list(node_version)])
            tip_text = f"please downgrade addon version to {version_str}."

        layout = self.layout
        layout.label(text="Incompatible node version detected.")
        layout.separator()
        layout.label(
            text="If you still want to edit this file with bioxel nodes, ")
        layout.label(text=tip_text)
        layout.separator()
        layout.label(text="If this file is archived, "
                     "please relink node library, ")
        layout.label(text="check if it still works, "
                     "then save node library.")
        layout.separator()
        layout.menu(ReLinkNodeLibMenu.bl_idname)
        layout.operator(SaveNodeLib.bl_idname)

        layout.separator()
        layout.menu(DangerZoneMenu.bl_idname)

        layout.separator()
        layout.menu(RenderSettingMenu.bl_idname)

        layout.separator()
        layout.operator(Help.bl_idname,
                        icon=Help.bl_icon)


class FetchLayerMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_ADD_LAYER"
    bl_label = "Fetch Layer"

    def draw(self, context):
        container_obj = get_container_obj(bpy.context.active_object)
        layer_objs = get_container_layer_objs(container_obj)
        layout = self.layout

        for layer_obj in layer_objs:
            op = layout.operator(FetchLayer.bl_idname,
                                 text=get_layer_label(layer_obj))
            op.layer_obj_name = layer_obj.name


class ExtractFromContainerMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_PICK"
    bl_label = "Extract from Container"

    def draw(self, context):
        layout = self.layout
        layout.operator(ExtractMesh.bl_idname)
        layout.operator(ExtractShapeWire.bl_idname)
        layout.operator(ExtractBboxWire.bl_idname)


class AddCutterMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_CUTTERS"
    bl_label = "Add a Cutter"

    def draw(self, context):
        layout = self.layout
        layout.operator(AddPlaneCutter.bl_idname,
                        icon=AddPlaneCutter.bl_icon, text="Plane Cutter")
        layout.operator(AddCylinderCutter.bl_idname,
                        icon=AddCylinderCutter.bl_icon, text="Cylinder Cutter")
        layout.operator(AddCubeCutter.bl_idname,
                        icon=AddCubeCutter.bl_icon, text="Cube Cutter")
        layout.operator(AddSphereCutter.bl_idname,
                        icon=AddSphereCutter.bl_icon, text="Sphere Cutter")
        layout.operator(AddPieCutter.bl_idname,
                        icon=AddPieCutter.bl_icon, text="Pie Cutter")


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
    bl_label = "Import Volumetric Data (Add)"
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
        layout = self.layout
        layout.operator(SignScalar.bl_idname,
                        icon=SignScalar.bl_icon)
        layout.operator(FillByThreshold.bl_idname,
                        icon=FillByThreshold.bl_icon)
        layout.operator(FillByRange.bl_idname,
                        icon=FillByRange.bl_icon)
        layout.operator(FillByLabel.bl_idname,
                        icon=FillByLabel.bl_icon)
        layout.operator(CombineLabels.bl_idname,
                        icon=CombineLabels.bl_icon)


class ReLinkNodeLibMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_RELINK"
    bl_label = "Relink Node Library"

    def draw(self, context):
        layout = self.layout

        for index, version in enumerate(VERSIONS):
            op = layout.operator(ReLinkNodeLib.bl_idname,
                                 text=version["label"])
            op.index = index


class RenderSettingMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_RENDER"
    bl_label = "Render Setting Presets"

    def draw(self, context):
        layout = self.layout
        for k, v in RenderSettingPreset.PRESETS.items():
            op = layout.operator(RenderSettingPreset.bl_idname,
                                 text=v)
            op.preset = k


class DangerZoneMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_DANGER"
    bl_label = "Danger Zone"

    def draw(self, context):
        layout = self.layout
        layout.operator(CleanTemp.bl_idname)


class BioxelNodesTopbarMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_TOPBAR"
    bl_label = "Bioxel Nodes"

    def draw(self, context):
        layout = self.layout

        layout.menu(ImportLayerMenu.bl_idname,
                    icon=ImportLayerMenu.bl_icon)
        layout.operator(LoadContainer.bl_idname)

        layout.separator()
        layout.operator(SaveAllLayersCache.bl_idname)
        layout.operator(RemoveAllMissingLayers.bl_idname)

        layout.separator()
        layout.menu(ReLinkNodeLibMenu.bl_idname)
        layout.operator(SaveNodeLib.bl_idname)

        layout.separator()
        layout.menu(DangerZoneMenu.bl_idname)

        layout.separator()
        layout.operator(AddEeveeEnv.bl_idname)
        layout.menu(RenderSettingMenu.bl_idname)

        layout.separator()
        layout.operator(Help.bl_idname,
                        icon=Help.bl_icon)


def TOPBAR(self, context):
    layout = self.layout

    if is_incompatible():
        layout.menu(IncompatibleMenu.bl_idname)
    else:
        layout.menu(BioxelNodesTopbarMenu.bl_idname)


class NodeHeadMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_NODE_HEAD"
    bl_label = "Bioxel Nodes"
    bl_icon = "FILE_VOLUME"

    def draw(self, context):

        layout = self.layout
        layout.menu(AddLayerMenu.bl_idname,
                    icon=AddLayerMenu.bl_icon)
        layout.operator(SaveContainer.bl_idname)

        layout.separator()
        layout.operator(ContainerProps.bl_idname)
        layout.menu(ExtractFromContainerMenu.bl_idname)

        layout.separator()
        layout.operator(SaveContainerLayersCache.bl_idname,
                        icon=SaveContainerLayersCache.bl_icon)
        layout.operator(RemoveContainerMissingLayers.bl_idname)

        layout.separator()
        layout.operator(AddLocator.bl_idname,
                        icon=AddLocator.bl_icon)
        layout.operator(AddSlicer.bl_idname,
                        icon=AddSlicer.bl_icon)
        layout.menu(AddCutterMenu.bl_idname)

        layout.separator()
        layout.menu(FetchLayerMenu.bl_idname)


class NodeContextMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_NODE_CONTEXT"
    bl_label = "Bioxel Nodes"
    bl_icon = "FILE_VOLUME"

    def draw(self, context):
        layout = self.layout
        layout.operator(ExtractNodeMesh.bl_idname)
        layout.operator(ExtractNodeShapeWire.bl_idname)
        layout.operator(ExtractNodeBboxWire.bl_idname)

        layout.separator()
        layout.operator(SaveSelectedLayersCache.bl_idname,
                        icon=SaveSelectedLayersCache.bl_icon)
        layout.operator(RemoveSelectedLayers.bl_idname)

        layout.separator()
        layout.operator(RenameLayer.bl_idname,
                        icon=RenameLayer.bl_icon)
        layout.operator(RetimeLayer.bl_idname)
        layout.operator(RelocateLayer.bl_idname)

        layout.separator()
        layout.operator(ResampleLayer.bl_idname,
                        icon=ResampleLayer.bl_icon)
        layout.operator(SignScalar.bl_idname)
        layout.operator(FillByThreshold.bl_idname)
        layout.operator(FillByRange.bl_idname)
        layout.operator(FillByLabel.bl_idname)
        layout.operator(CombineLabels.bl_idname)


def NODE_CONTEXT(self, context):
    if is_incompatible():
        return

    container_obj = context.object
    is_geo_nodes = context.area.ui_type == "GeometryNodeTree"
    is_container = get_container_obj(container_obj)

    if not is_geo_nodes or not is_container:
        return

    layout = self.layout
    layout.separator()
    layout.menu(NodeContextMenu.bl_idname)


def NODE_HEAD(self, context):
    if is_incompatible():
        return

    container_obj = context.object
    is_geo_nodes = context.area.ui_type == "GeometryNodeTree"
    is_container = get_container_obj(container_obj)

    if not is_geo_nodes or not is_container:
        return

    layout = self.layout
    layout.separator()
    layout.menu(NodeHeadMenu.bl_idname)


def NODE_PROP(self, context):
    if is_incompatible():
        return

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
    layer_list.clear()

    for layer_obj in get_container_layer_objs(container_obj):
        layer_item = layer_list.add()
        layer_item.label = get_layer_label(layer_obj)
        layer_item.obj_name = layer_obj.name
        layer_item.info_text = "\n".join([f"{prop}: {get_layer_prop_value(layer_obj, prop)}"
                                          for prop in ["kind",
                                                       "bioxel_size",
                                                       "shape",
                                                       "frame_count",
                                                       "channel_count",
                                                       "min", "max"]])

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

    # sidebar = split.column(align=True)
    # sidebar.menu(AddLayerMenu.bl_idname,
    #              icon=AddLayerMenu.bl_icon, text="")

    # sidebar.operator(SaveContainerLayersCache.bl_idname,
    #                  icon=SaveContainerLayersCache.bl_icon, text="")
    # sidebar.operator(RemoveContainerMissingLayers.bl_idname,
    #                  icon=RemoveContainerMissingLayers.bl_icon, text="")

    # sidebar.separator()
    # sidebar.operator(SaveSelectedLayersCache.bl_idname,
    #                  icon=SaveSelectedLayersCache.bl_icon, text="")
    # sidebar.operator(RemoveSelectedLayers.bl_idname,
    #                  icon=RemoveSelectedLayers.bl_icon, text="")

    # sidebar.separator()
    # sidebar.operator(RenameLayer.bl_idname,
    #                  icon=RenameLayer.bl_icon, text="")
    # sidebar.operator(ResampleLayer.bl_idname,
    #                  icon=ResampleLayer.bl_icon, text="")
    # sidebar.operator(RetimeLayer.bl_idname,
    #                  icon=RetimeLayer.bl_icon, text="")

    # sidebar.separator()
    # sidebar.operator(SignScalar.bl_idname,
    #                  icon=SignScalar.bl_icon, text="")
    # sidebar.operator(FillByThreshold.bl_idname,
    #                  icon=FillByThreshold.bl_icon, text="")
    # sidebar.operator(FillByRange.bl_idname,
    #                  icon=FillByRange.bl_icon, text="")
    # sidebar.operator(FillByLabel.bl_idname,
    #                  icon=FillByLabel.bl_icon, text="")

    # sidebar.separator()
    # layout.separator()


def VIEW3D_TOPBAR(self, context):
    layout = self.layout
    layout.operator(SliceViewer.bl_idname)


node_menu = NodeMenu(
    menu_items=MENU_ITEMS
)


def add():
    node_menu.register()
    # bpy.types.VIEW3D_HT_header.append(VIEW3D_TOPBAR)
    bpy.types.TOPBAR_MT_editor_menus.append(TOPBAR)
    bpy.types.NODE_PT_node_tree_properties.prepend(NODE_PROP)
    bpy.types.NODE_MT_editor_menus.append(NODE_HEAD)
    bpy.types.NODE_MT_context_menu.append(NODE_CONTEXT)


def remove():
    # bpy.types.VIEW3D_HT_header.remove(VIEW3D_TOPBAR)
    bpy.types.TOPBAR_MT_editor_menus.remove(TOPBAR)
    bpy.types.NODE_PT_node_tree_properties.remove(NODE_PROP)
    bpy.types.NODE_MT_editor_menus.remove(NODE_HEAD)
    bpy.types.NODE_MT_context_menu.remove(NODE_CONTEXT)
    node_menu.unregister()
