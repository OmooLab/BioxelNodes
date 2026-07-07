from pathlib import Path
import bpy

from .asset_library import has_bioxel_asset_library
from .node import get_layer_nodes, get_main_node_group
from .utils import load_icon
from .layer import get_layer_caches
from .operators.io import ImportAsColor, ImportAsLabel, ImportAsScalar, ImportData
from .operators.misc import AddAssetLibrary, Help, RenderSettingPreset
from .operators.layer import (
    AddLayerNode,
    DeleteLayer,
    RelocatePath,
    RenameLayer,
    SaveLayer,
)


class ImportMenu(bpy.types.Menu):
    bl_label = "Bioxel Import"
    bl_idname = "BIOXEL_MT_import"

    def draw(self, context):
        layout = self.layout
        layout.operator(ImportAsScalar.bl_idname,
                        text="Import As Scalar").filepath = ""
        layout.operator(ImportAsLabel.bl_idname,
                        text="Import As Label").filepath = ""
        layout.operator(ImportAsColor.bl_idname,
                        text="Import As Color").filepath = ""


class RenderSettingMenu(bpy.types.Menu):
    bl_label = "Render Setting Presets"
    bl_idname = "BIOXEL_MT_render_setting"

    def draw(self, context):
        layout = self.layout
        for k, v in RenderSettingPreset.PRESETS.items():
            op = layout.operator(RenderSettingPreset.bl_idname, text=v)
            op.preset = k


class BioxelPanelBase:
    """
    Abstract base panel for all Bioxel UI panels.

    - Ensures the panel appears only when the active area is the Node Editor
      and the Node Editor is editing a Geometry Nodes tree.
    - Places the panel under the "Bioxel" sidebar tab.
    - Provides an optional bl_order for panel ordering inside the category.
    """

    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_context = "geometry_node"
    bl_category = "Bioxel Nodes"
    requires_asset_library = True
    # try to make Bioxel panels order early (may be respected by Blender)

    @classmethod
    def poll(cls, context):
        node_group = get_main_node_group(context)
        if node_group is None:
            return False

        if not getattr(cls, "requires_asset_library", True):
            return True

        return has_bioxel_asset_library()


class HeaderPanel(bpy.types.Panel, BioxelPanelBase):
    bl_label = "Bioxel Nodes"
    bl_idname = "BIOXEL_PT_header_panel"
    bl_order = 0
    requires_asset_library = False

    def draw(self, context):
        layout = self.layout

        if not has_bioxel_asset_library():
            layout.operator(
                AddAssetLibrary.bl_idname,
                text="Add Nodes Library",
                icon="ASSET_MANAGER",
            )
            return

        layout.operator(
            Help.bl_idname, text="Help", icon=Help.bl_icon  # 复用原操作的图标定义
        )

        layout.menu(
            RenderSettingMenu.bl_idname, text="Render Preset", icon="RENDER_STILL"
        )


class LayerNodePanel(BioxelPanelBase, bpy.types.Panel):
    bl_label = "Layer Nodes"
    bl_idname = "BIOXEL_PT_o_layer_nodes"
    bl_order = 1

    def draw(self, context):
        layout = self.layout
        node_group = get_main_node_group(context)

        layout.template_list(
            "BIOXEL_UL_layer_nodes",
            "",
            node_group,
            "nodes",
            context.window_manager,
            "bioxel_layer_list_index",
            rows=3,
        )


class LibraryPanel(BioxelPanelBase, bpy.types.Panel):
    bl_label = "Layer Library"
    bl_idname = "BIOXEL_PT_library_panel"
    bl_order = 2

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        caches = get_layer_caches()

        row = layout.row()
        row.scale_y = 2.0
        row.operator(ImportData.bl_idname, icon="IMPORT")
        # row.menu(ImportMenu.bl_idname, icon="IMPORT", text="Import")
        layout.separator()
        layout.template_icon_view(
            bpy.context.window_manager,
            "bioxel_layer_library",
            show_labels=False,
            scale=10.0,
            scale_popup=6.0,
        )

        selected_id = getattr(wm, "bioxel_layer_library", None)
        selected_id = None if selected_id == "nothing_found" else selected_id
        entry = next((c for c in caches if c.get("id") == selected_id), None)
        if entry:
            cache_id = entry["id"]
            path = entry["path"]
            name = entry.get("name", "?")
            kind = entry.get("kind", "?")
            path_exists = Path(bpy.path.abspath(path)).exists()

            layout.prop(wm, "bioxel_snapshot_z", text="Z Slice", slider=True)
            layout.separator()
            # operations and meta_box as before
            ops_row = layout.row(align=True)
            if path_exists:
                ops_row.operator(
                    AddLayerNode.bl_idname, text="Add", icon="PLUS"
                ).cache_id = selected_id
                ops_row.operator(
                    SaveLayer.bl_idname, text="Save", icon="FILE_TICK"
                ).cache_id = selected_id
                ops_row.operator(
                    RenameLayer.bl_idname, text="Name", icon="FONT_DATA"
                ).cache_id = selected_id
                ops_row.operator(
                    DeleteLayer.bl_idname, text="", icon="TRASH"
                ).cache_id = selected_id
            else:
                ops_row.operator(
                    RelocatePath.bl_idname, text="Relocate", icon="FILE_FOLDER"
                ).cache_id = selected_id
                ops_row.operator(
                    DeleteLayer.bl_idname, text="", icon="TRASH"
                ).cache_id = selected_id

                meta_box = layout.box()
                if hasattr(meta_box, "alert"):
                    meta_box.alert = True
                meta_box.label(text=f"Cache is missing...")
                meta_box.label(text=f"Please relocate the cache path!")
                return

            meta_box = layout.box()
            meta_box.label(text=f"Name: {name}")
            meta_box.label(text=f"Path: {path}")
            meta_box.label(text=f"Kind: {kind}")
            meta_box.label(
                text=f"Dims: [{entry.get('frame_count',1)},{tuple(entry.get('shape',''))},{entry.get('channel_count',1)}]"
            )
            if kind in ["scalar", "color", "vector"]:
                path = Path(bpy.path.abspath(entry["path"]))
                histogram = load_icon(
                    path / "histogram.png", f"{cache_id}_histogram")
                meta_box.template_icon(histogram, scale=10.0)
        else:
            layout.label(text="No layer selected", icon="QUESTION")
