from pathlib import Path
import shutil
import bpy

from .common import get_file_prop, set_file_prop
from ..exceptions import Incompatible, NoFound

from ..constants import NODE_LIB_FILEPATH, VERSION


def get_node_group(node_type: str, use_link=True):
    # unannotate below for local debug in node lib file.
    # node_group = bpy.data.node_groups[node_type]
    # return node_group

    if get_file_prop("addon_version") is None:
        set_file_prop("addon_version", VERSION)

    local_lib_file = None
    addon_lib_file = NODE_LIB_FILEPATH.as_posix()

    for node_group in bpy.data.node_groups:
        if node_group.name.startswith("BioxelNodes"):
            node_group_lib = node_group.library
            if node_group_lib:
                abs_filepath = bpy.path.abspath(node_group_lib.filepath)
                _local_lib_file = Path(abs_filepath).resolve().as_posix()
                if _local_lib_file != addon_lib_file:
                    local_lib_file = _local_lib_file
                    break

    # local lib first
    lib_file = local_lib_file or addon_lib_file
    bpy.ops.wm.append('EXEC_DEFAULT',
                      directory=f"{lib_file}/NodeTree",
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


def add_node_to_graph(node_name: str, node_group, use_link=True):
    node_type = f"BioxelNodes_{node_name}"

    # Deselect all nodes first
    for node in node_group.nodes:
        if node.select:
            node.select = False

    get_node_group(node_type, use_link)
    node = node_group.nodes.new("GeometryNodeGroup")
    assign_node_group(node, node_type)

    node.show_options = False
    return node
