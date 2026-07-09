from pathlib import Path
import shutil

import bpy

from ..asset_library import ASSET_LIBRARY_MISSING, get_bioxel_asset_library_status
from ..node import add_bioxel_node, get_layer_nodes, get_main_node_group
from ..utils import refresh_bioxel_panels
from ..layer import get_layer_caches, set_layer_caches


class RenameLayer(bpy.types.Operator):
    """Rename a cached Bioxel layer"""

    bl_idname = "bioxel.rename_layer"
    bl_label = "Rename Layer"
    bl_options = {"REGISTER", "UNDO"}

    cache_id: bpy.props.StringProperty(options={"HIDDEN"})  # type: ignore
    new_name: bpy.props.StringProperty(name="New name", default="")  # type: ignore

    def invoke(self, context, event):
        caches = get_layer_caches()
        entry = next((c for c in caches if str(c.get("id", "")) == self.cache_id), None)
        if entry:
            self.new_name = str(entry.get("name", ""))
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        if not self.new_name:
            self.report({"ERROR"}, "Name cannot be empty")
            return {"CANCELLED"}

        caches = get_layer_caches()
        for c in caches:
            if str(c.get("id", "")) == self.cache_id:
                c["name"] = self.new_name
                break

        try:
            set_layer_caches(caches)
            refresh_bioxel_panels(context)
            self.report({"INFO"}, "Layer renamed")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Failed to save changes: {e}")
            return {"CANCELLED"}


class DeleteLayer(bpy.types.Operator):
    """Delete a saved Bioxel layer"""

    bl_idname = "bioxel.delete_layer"
    bl_label = "Delete Layer"
    bl_options = {"REGISTER", "UNDO"}

    cache_id: bpy.props.StringProperty()  # type: ignore

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        if not self.cache_id:
            self.report({"ERROR"}, "Missing cache id")
            return {"CANCELLED"}

        caches = get_layer_caches()
        new_list = [c for c in caches if str(c.get("id", "")) != self.cache_id]
        removed = next(
            (c for c in caches if str(c.get("id", "")) == self.cache_id), None
        )

        try:
            set_layer_caches(new_list)
            refresh_bioxel_panels(context)
        except Exception as e:
            self.report({"ERROR"}, f"Failed to update layer list: {e}")
            return {"CANCELLED"}

        self.report({"INFO"}, "Layer removed")
        return {"FINISHED"}


# 添加图层到节点图的操作器
class AddLayerNode(bpy.types.Operator):
    """将选中的图层添加到几何节点图"""

    bl_idname = "bioxel.add_layer_node"
    bl_label = "添加图层节点"
    bl_options = {"REGISTER", "UNDO"}

    cache_id: bpy.props.StringProperty()  # type: ignore # 图层ID

    def execute(self, context):
        status = get_bioxel_asset_library_status()
        if status["code"] == ASSET_LIBRARY_MISSING:
            self.report({"ERROR"}, status["message"])
            return {"CANCELLED"}

        # 获取图层数据
        caches = get_layer_caches()

        # 查找目标图层
        entry = next(
            (c for c in caches if str(c.get("id", "")) == str(self.cache_id)), None
        )

        if not entry:
            self.report({"ERROR"}, "Layer not found")
            return {"CANCELLED"}

        # 创建并设置节点属性
        try:
            layer_node = add_bioxel_node("O Layer")
        except:
            self.report({"ERROR"}, "Fail to add layer node")
            return {"CANCELLED"}

        layer_node.node_tree.make_local()
        layer_node.inputs["Path"].default_value = entry["path"]
        layer_node.inputs["Name"].default_value = entry["name"]
        layer_node.inputs["Shape"].default_value = entry["shape"]
        layer_node.inputs["Min"].default_value = entry["min"]
        layer_node.inputs["Max"].default_value = entry["max"]
        layer_node.inputs["ID"].default_value = entry["id"]

        # 将特定属性隐藏到hidden面板
        hidden_sockets = ["Path", "Shape", "Min", "Max", "ID", "Animation"]

        if entry["frame_count"] > 1:
            layer_node.inputs["Frame Count"].default_value = entry["frame_count"]
            layer_node.inputs["Animation"].default_value = True
        else:
            hidden_sockets = hidden_sockets + ["Frame Count", "Frame Offset", "Cycle"]

        # 将特定属性隐藏到hidden面板
        for socket_name in hidden_sockets:
            if socket_name in layer_node.inputs:
                layer_node.inputs[socket_name].hide = True

        for socket_name in layer_node.outputs.keys():
            if socket_name != entry["kind"].capitalize():
                layer_node.outputs[socket_name].hide = True

        self.report({"INFO"}, f"Successfully created node: {entry['name']}")
        return {"FINISHED"}


class RelocatePath(bpy.types.Operator):
    """Locate and update the missing layer folder, and update all related nodes"""

    bl_idname = "bioxel.find_layer_folder"
    bl_label = "Relocate"
    bl_options = {"REGISTER", "UNDO"}

    cache_id: bpy.props.StringProperty(options={"HIDDEN"})  # type: ignore

    use_relative: bpy.props.BoolProperty(
        name="Relative Path",
        description="Store the path relative to the current Blender file",
        default=True,
    )  # type: ignore

    directory: bpy.props.StringProperty(
        name="Layer Folder",
        description="Select the correct folder for this layer",
        subtype="DIR_PATH",
    )  # type: ignore

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        if not self.cache_id:
            self.report({"ERROR"}, "Missing cache id")
            return {"CANCELLED"}
        if not self.directory:
            self.report({"ERROR"}, "Please select a folder")
            return {"CANCELLED"}

        caches = get_layer_caches()
        entry = next((c for c in caches if str(c.get("id", "")) == self.cache_id), None)
        if not entry:
            self.report({"ERROR"}, "Layer not found")
            return {"CANCELLED"}

        old_path = entry["path"]
        new_path = (
            bpy.path.relpath(self.directory)
            if self.use_relative and bpy.data.filepath
            else bpy.path.abspath(self.directory)
        )
        entry["path"] = new_path

        set_layer_caches(caches)
        refresh_bioxel_panels(context)

        # 更新所有 node group 中 O Layer 节点的 Path
        for node_group in bpy.data.node_groups:
            for node in get_layer_nodes(node_group):
                node_path = getattr(node.inputs.get("Path"), "default_value")
                if node_path and node_path == old_path:
                    node.inputs["Path"].default_value = new_path

        self.report({"INFO"}, f"Cache path updated: {new_path}")
        return {"FINISHED"}


class SaveLayer(bpy.types.Operator):
    """Copy the entire layer folder (named by id) to a target folder and update its path in the cache"""

    bl_idname = "bioxel.cache_layer_to_folder"
    bl_label = "Save Layer"
    bl_options = {"REGISTER", "UNDO"}

    cache_id: bpy.props.StringProperty(options={"HIDDEN"})  # type: ignore

    use_relative: bpy.props.BoolProperty(
        name="Relative Path",
        description="Store the path relative to the current Blender file",
        default=True,
    )  # type: ignore

    directory: bpy.props.StringProperty(
        name="Target Folder",
        description="Select a folder to cache the layer files",
        subtype="DIR_PATH",
    )  # type: ignore

    def invoke(self, context, event):
        # Default to Blender file directory if possible
        blend_dir = Path(bpy.data.filepath).parent if bpy.data.filepath else Path.cwd()
        context.window_manager.fileselect_add(self)
        if not self.directory:
            self.directory = str(blend_dir)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        if not self.cache_id:
            self.report({"ERROR"}, "Missing cache id")
            return {"CANCELLED"}
        if not self.directory:
            self.report({"ERROR"}, "Please select a target folder")
            return {"CANCELLED"}

        caches = get_layer_caches()
        entry = next((c for c in caches if str(c.get("id")) == self.cache_id), None)
        cache_id = entry.get("id")

        if not entry:
            self.report({"ERROR"}, "Layer not found")
            return {"CANCELLED"}

        old_path = entry["path"]
        src_path = bpy.path.abspath(old_path)
        if not src_path or not Path(src_path).is_dir():
            self.report({"ERROR"}, "Source folder not found")
            return {"CANCELLED"}

        src_dir = Path(src_path).resolve()
        dst_root = Path(self.directory)
        # copy as a subfolder named by id
        dst_dir = (dst_root / src_dir.name).resolve()

        try:
            if src_dir != dst_dir:
                if dst_dir.exists():
                    shutil.rmtree(dst_dir)
                shutil.copytree(src_dir, dst_dir)

                # Save as relative path if requested and possible

            new_path = (
                bpy.path.relpath(str(dst_dir))
                if self.use_relative and bpy.data.filepath
                else bpy.path.abspath(str(dst_dir))
            )

            entry["path"] = new_path

            set_layer_caches(caches)
            refresh_bioxel_panels(context)

            # 遍历所有 node group
            for node_group in bpy.data.node_groups:
                for node in get_layer_nodes(node_group):
                    if cache_id == getattr(node.inputs.get("ID"), "default_value"):
                        node.inputs["Path"].default_value = new_path

            self.report({"INFO"}, f"Layer cached to {dst_dir}")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Failed to cache layer: {e}")
            return {"CANCELLED"}


class SelectAndFocusNode(bpy.types.Operator):
    """Select and focus the specified node in the current node tree"""

    bl_idname = "bioxel.select_and_focus_node"
    bl_label = "Select and Focus Node"
    node_name: bpy.props.StringProperty()  # type: ignore

    def execute(self, context):
        node_group = get_main_node_group(context)
        if not node_group:
            self.report({"ERROR"}, "No node group found.")
            return {"CANCELLED"}
        node = node_group.nodes.get(self.node_name)
        if not node:
            self.report({"ERROR"}, f"Node '{self.node_name}' not found.")
            return {"CANCELLED"}
        # Deselect all, select and focus this node
        for n in node_group.nodes:
            n.select = False
        node.select = True
        node_group.nodes.active = node
        bpy.ops.node.view_selected()
        return {"FINISHED"}
