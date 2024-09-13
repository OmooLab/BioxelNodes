from pathlib import Path
import bpy

from .common import get_file_prop, get_node_lib_path, set_file_prop
from ..exceptions import Incompatible, NoFound

from ..constants import LATEST_NODE_LIB_PATH, VERSIONS


def get_node_group(node_type: str, use_link=True):
    # unannotate below for local debug in node lib file.
    # node_group = bpy.data.node_groups[node_type]
    # return node_group

    # added node is always from latest node version
    addon_version = VERSIONS[0]["node_version"]
    addon_lib_path = LATEST_NODE_LIB_PATH

    if get_file_prop("node_version") is None:
        set_file_prop("node_version", addon_version)

    local_lib_path = None
    for node_group in bpy.data.node_groups:
        if node_group.name.startswith("BioxelNodes"):
            lib = node_group.library
            if lib:
                lib_path = Path(bpy.path.abspath(lib.filepath)).resolve()
                if lib_path != addon_lib_path:
                    local_lib_path = lib_path
                    break

    # local lib first
    lib_path = local_lib_path or addon_lib_path
    bpy.ops.wm.append('EXEC_DEFAULT',
                      directory=f"{lib_path.as_posix()}/NodeTree",
                      filename=node_type,
                      link=use_link,
                      use_recursive=True,
                      do_reuse_local_id=True)
    node_group = bpy.data.node_groups.get(node_type)

    if node_group is None:
        raise NoFound('No custom node found')

    return node_group


def assign_node_group(node, node_type: str):
    node.node_tree = bpy.data.node_groups[node_type]
    node.width = 200.0
    node.name = node_type
    return node


def add_node_to_graph(node_name: str, node_group, node_label=None, use_link=True):
    node_type = f"BioxelNodes_{node_name}"
    node_label = node_label or node_name

    # Deselect all nodes first
    for node in node_group.nodes:
        if node.select:
            node.select = False

    get_node_group(node_type, use_link)
    node = node_group.nodes.new("GeometryNodeGroup")
    assign_node_group(node, node_type)

    node.label = node_label
    node.show_options = False
    return node
