import bpy
from .operators.structure import ExtractMesh

from .operators.io import ImportAsLabel, ImportAsScalar, ImportAsColor
from .operators.misc import (
    CleanTemp,
    Help,
    RenderSettingPreset,
    TogglePhantom,
)


class ImportLayerMenu(bpy.types.Menu):
    bl_idname = "BIOXEL_MT_IMPORTLAYER"
    bl_label = "Import Volumetric Data (Init)"
    bl_icon = "FILE_NEW"

    def draw(self, context):
        layout = self.layout
        layout.operator(ImportAsScalar.bl_idname, text="as Scalar")
        layout.operator(ImportAsLabel.bl_idname, text="as Label")
        layout.operator(ImportAsColor.bl_idname, text="as Color")


class RenderSettingMenu(bpy.types.Menu):
    bl_idname = "BIOXEL_MT_RENDER"
    bl_label = "Render Setting Presets"

    def draw(self, context):
        layout = self.layout
        for k, v in RenderSettingPreset.PRESETS.items():
            op = layout.operator(RenderSettingPreset.bl_idname, text=v)
            op.preset = k


class DangerZoneMenu(bpy.types.Menu):
    bl_idname = "BIOXEL_MT_DANGER"
    bl_label = "Danger Zone"

    def draw(self, context):
        layout = self.layout
        layout.operator(CleanTemp.bl_idname)


class BioxelNodesTopbarMenu(bpy.types.Menu):
    bl_idname = "BIOXEL_MT_TOPBAR"
    bl_label = "Bioxel Nodes"

    def draw(self, context):
        layout = self.layout

        layout.separator()
        layout.menu(DangerZoneMenu.bl_idname)

        layout.separator()
        layout.operator(Help.bl_idname, icon=Help.bl_icon)


class NodeContextMenu(bpy.types.Menu):
    bl_idname = "BIOXEL_MT_NODE_CONTEXT"
    bl_label = "Bioxel Nodes"
    bl_icon = "FILE_VOLUME"

    def draw(self, context):
        layout = self.layout
        layout.operator(ExtractMesh.bl_idname)


class ObjectContextMenu(bpy.types.Menu):
    bl_idname = "BIOXEL_MT_OBJECT_CONTEXT"
    bl_label = "Bioxel Nodes"
    bl_icon = "FILE_VOLUME"

    def draw(self, context):
        layout = self.layout
        layout.operator(TogglePhantom.bl_idname)


def NODE_CONTEXT(self, context):
    container_obj = context.object
    is_geo_nodes = context.area.ui_type == "GeometryNodeTree"

    if not is_geo_nodes or not container_obj:
        return

    layout = self.layout
    layout.separator()
    layout.menu(NodeContextMenu.bl_idname)


# 定义添加到右键菜单的函数，放在首位
def OBJECT_CONTEXT(self, context):
    layout = self.layout
    layout.separator()
    layout.menu(ObjectContextMenu.bl_idname)


def add():
    bpy.types.VIEW3D_MT_object_context_menu.append(OBJECT_CONTEXT)
    # bpy.types.NODE_MT_context_menu.append(NODE_CONTEXT)


def remove():
    bpy.types.VIEW3D_MT_object_context_menu.remove(OBJECT_CONTEXT)
    # bpy.types.NODE_MT_context_menu.remove(NODE_CONTEXT)
