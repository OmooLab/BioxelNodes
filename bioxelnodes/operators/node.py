import bpy

from ..bioxelutils.common import is_incompatible, local_lib_not_updated
from ..bioxelutils.node import assign_node_group, get_node_group
from ..utils import get_use_link


class AddNode(bpy.types.Operator):
    bl_idname = "bioxelnodes.add_node"
    bl_label = "Add Node"
    bl_options = {"REGISTER", "UNDO"}

    node_name: bpy.props.StringProperty(
        default='',
    )  # type: ignore

    node_label: bpy.props.StringProperty(
        default=''
    )  # type: ignore

    node_description: bpy.props.StringProperty(
        default="",
    )  # type: ignore

    @property
    def node_type(self):
        return f"BioxelNodes_{self.node_name}"

    def execute(self, context):
        space = context.space_data
        if space.type != "NODE_EDITOR":
            self.report({"ERROR"}, "Not in node editor.")
            return {'CANCELLED'}

        if not space.edit_tree.is_editable:
            self.report({"ERROR"}, "Not editable.")
            return {'CANCELLED'}

        if is_incompatible():
            self.report({"ERROR"},
                        "Current addon verison is not compatible to this file. If you insist on editing this file please keep the same addon version.")
            return {'CANCELLED'}

        get_node_group(self.node_type, get_use_link())
        bpy.ops.node.add_node(
            'INVOKE_DEFAULT',
            type='GeometryNodeGroup',
            use_transform=True
        )
        node = bpy.context.active_node
        assign_node_group(node, self.node_type)
        node.label = self.node_label

        node.show_options = False

        if local_lib_not_updated():
            self.report({"WARNING"},
                        "Local node library version does not match the current addon version, which may cause problems, please save the node library again.")

        return {"FINISHED"}
