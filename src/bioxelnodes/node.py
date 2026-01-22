from pathlib import Path
import bpy

# LookupError replaced with built-in LookupError
from .constants import LATEST_NODE_LIB_PATH


def move_node_to_node(node, target_node, offset=(0, 0)):
    node.location.x = target_node.location.x + offset[0]
    node.location.y = target_node.location.y + offset[1]


def move_node_between_nodes(node, target_nodes, offset=(0, 0)):
    xs = []
    ys = []
    for target_node in target_nodes:
        xs.append(target_node.location.x)
        ys.append(target_node.location.y)

    node.location.x = sum(xs) / len(xs) + offset[0]
    node.location.y = sum(ys) / len(ys) + offset[1]


def get_node_type(node):
    node_type = type(node).__name__
    if node_type == "GeometryNodeGroup":
        node_type = node.node_tree.name

    return node_type


def get_nodes_by_type(node_group, type_name: str):
    return [node for node in node_group.nodes if get_node_type(node) == type_name]


def get_node_tree(node_type: str, use_link=True):
    try:
        return bpy.data.node_groups[node_type]
    except KeyError:
        lib_path_str = str(LATEST_NODE_LIB_PATH)
        with bpy.data.libraries.load(lib_path_str, link=use_link, relative=True) as (
            data_from,
            data_to,
        ):
            data_to.node_groups = [
                n for n in data_from.node_groups if n == node_type]
        node_tree = data_to.node_groups[0]

        if node_tree is None:
            raise LookupError("No custom node found")

        return node_tree


def assign_node_tree(node, node_tree):
    node.node_tree = node_tree
    node.width = 200.0
    node.name = node_tree.name
    return node


def add_node_to_graph(node_name: str, node_group, node_label=None, use_link=True):
    node_type = f"O {node_name}"
    node_label = node_label or node_name

    # Deselect all nodes first
    for node in node_group.nodes:
        if node.select:
            node.select = False

    node_tree = get_node_tree(node_type, use_link)
    node = node_group.nodes.new("GeometryNodeGroup")
    assign_node_tree(node, node_tree)

    node.label = node_label
    node.show_options = False
    bpy.ops.node.view_selected()
    return node


def get_output_node(node_group):
    try:
        output_node = get_nodes_by_type(node_group, "NodeGroupOutput")[0]
    except:
        output_node = node_group.nodes.new("NodeGroupOutput")

    return output_node


def add_bioxel_node(name: str):
    # bpy.ops.node.add_group_asset(
    #     asset_library_type="CUSTOM",
    #     asset_library_identifier = "O Bioxel",
    #     relative_asset_identifier = "NodeTreO Crop Layer"
    # )
    # bpy.ops.node.add_group_asset(
    #     asset_library_type="CUSTOM",
    #     asset_library_identifier="O Bioxel",
    #     relative_asset_identifier="Nodes.blend\\NodeTree\\O Render Structure"
    # )

    try:
        node_tree = bpy.data.node_groups[name]
    except KeyError:
        bpy.ops.object.modifier_add_node_group(
            asset_library_type="CUSTOM",
            asset_library_identifier="O Bioxel",
            relative_asset_identifier=f"BioxelNodes.blend\\NodeTree\\{name}",
        )
        bpy.ops.object.modifier_remove(modifier=name)
        try:
            node_tree = bpy.data.node_groups[name]
        except Exception as e:
            raise e

    bpy.ops.node.add_node(
        "INVOKE_DEFAULT", type="GeometryNodeGroup", use_transform=True
    )

    node = bpy.context.active_node
    node.node_tree = node_tree
    node.show_options = False

    return bpy.context.active_node


def get_layer_nodes(node_group):
    """Return all O Layer nodes in the given node_tree."""
    return [
        n
        for n in node_group.nodes
        if n.bl_idname == "GeometryNodeGroup"
        and getattr(n, "node_tree", None)
        and n.node_tree.name.startswith("O Layer")
    ]


def get_main_node_group(context):
    space = getattr(context, "space_data", None) or getattr(
        context, "space", None)
    if not space:
        return None
    node_tree = getattr(space, "node_tree", None)
    if not node_tree:
        return None
    # accept GeometryNodeTree by bl_idname or class name for compatibility
    if getattr(node_tree, "bl_idname", "") == "GeometryNodeTree" or node_tree.__class__.__name__ == "GeometryNodeTree":
        return node_tree
    return None
