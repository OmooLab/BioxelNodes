from pathlib import Path
import bpy

from .common import get_file_prop, set_file_prop
from ..exceptions import NoFound

from ..constants import LATEST_NODE_LIB_PATH, VERSIONS


def get_node_tree(node_type: str, use_link=True):
    # unannotate below for local debug in node lib file.
    # node_group = bpy.data.node_groups[node_type]
    # return node_group

    # added node is always from latest node version
    addon_version = VERSIONS[0]["node_version"]
    addon_lib_path = LATEST_NODE_LIB_PATH

    if get_file_prop("node_version") is None:
        set_file_prop("node_version", addon_version)

    local_lib = None
    for node_group in bpy.data.node_groups:
        if node_group.name.startswith("BioxelNodes"):
            lib = node_group.library
            if lib:
                lib_path = Path(bpy.path.abspath(lib.filepath)).resolve()
                if lib_path != addon_lib_path:
                    local_lib = lib.filepath
                    break

    # local lib first
    lib_path_str = local_lib or str(addon_lib_path)

    with bpy.data.libraries.load(lib_path_str,
                                 link=use_link,
                                 relative=True) as (data_from, data_to):
        data_to.node_groups = [n for n in data_from.node_groups
                               if n == node_type]

    node_tree = data_to.node_groups[0]

    if node_tree is None:
        raise NoFound('No custom node found')

    return node_tree


def assign_node_tree(node, node_tree):
    node.node_tree = node_tree
    node.width = 200.0
    node.name = node_tree.name
    return node


def add_node_to_graph(node_name: str, node_group, node_label=None, use_link=True):
    node_type = f"BioxelNodes_{node_name}"
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
    return node
