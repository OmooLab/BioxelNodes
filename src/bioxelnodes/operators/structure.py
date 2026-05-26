import bpy
from ..utils import get_use_link
from ..node import add_node_to_graph, get_output_node, get_main_node_group


class ExtractMesh(bpy.types.Operator):
    bl_idname = "bioxel.extract_mesh"
    bl_label = "Extract Mesh"
    bl_description = "Extract Mesh"
    bl_icon = "OUTLINER_OB_MESH"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        # Check if there is a selected node in the node group
        node_group = get_main_node_group(context)
        selected_nodes = [n for n in node_group.nodes if n.select]

        if len(selected_nodes) == 0:
            return False
        else:
            source_node = selected_nodes[0]
            return "Structure" in source_node.outputs

    def execute(self, context):
        container_obj = context.object

        if container_obj is None:
            self.report({"WARNING"}, "Cannot find any bioxel container.")
            return {"FINISHED"}

        node_group = container_obj.modifiers[0].node_group
        selected_nodes = [n for n in node_group.nodes if n.select]

        source_node = selected_nodes[0]

        # Check if the selected node has a "Structure" output
        if "Structure" not in source_node.outputs:
            self.report({"ERROR"}, "Selected node has no 'Structure' output.")
            return {"CANCELLED"}

        # 记录原始输出连接（用于后续复原）
        output_node = get_output_node(node_group)
        original_links = list(output_node.inputs[0].links)

        # 添加Component to Mesh节点
        to_mesh_node = add_node_to_graph(
            "Structure to Mesh", node_group, use_link=get_use_link()
        )

        # 连接节点：源节点 -> Component to Mesh -> 输出节点
        node_group.links.new(
            source_node.outputs["Structure"], to_mesh_node.inputs[0])
        node_group.links.new(to_mesh_node.outputs[0], output_node.inputs[0])

        new_obj = None

        try:
            deps = context.evaluated_depsgraph_get()
            eval_obj = container_obj.evaluated_get(deps)
            # obtain evaluated mesh (from modifiers including Geometry Nodes)
            mesh_eval = eval_obj.to_mesh()
            if mesh_eval is None:
                raise RuntimeError("Failed to produce evaluated mesh")

            mesh_name = f"{container_obj.name}_Mesh"
            mesh_copy = mesh_eval.copy()
            mesh_copy.name = mesh_name
            # clear the temporary evaluated mesh
            try:
                eval_obj.to_mesh_clear()
            except Exception:
                pass

            # create the new object with same transform as source
            new_obj = bpy.data.objects.new(mesh_name, mesh_copy)
            # link to same collection as the container (fallback to current collection)
            col = (
                container_obj.users_collection[0]
                if getattr(container_obj, "users_collection", None)
                else context.collection
            )
            if col is None:
                col = context.collection
            col.objects.link(new_obj)

            # copy world transform exactly
            new_obj.matrix_world = container_obj.matrix_world.copy()
        except Exception as e:
            self.report({"ERROR"}, f"Failed to extract mesh: {e}")

        # 恢复原始连接
        for link in original_links:
            node_group.links.new(link.from_socket, output_node.inputs[0])

        # 删除临时添加的Component to Mesh节点
        node_group.nodes.remove(to_mesh_node)
        if new_obj:
            # deselect everything, select and activate new_obj
            for o in list(context.selected_objects):
                o.select_set(False)
            new_obj.select_set(True)
            context.view_layer.objects.active = new_obj
            self.report({"INFO"}, f"Mesh extracted: {new_obj.name}")
            return {"FINISHED"}
        else:
            return {"CANCELLED"}
