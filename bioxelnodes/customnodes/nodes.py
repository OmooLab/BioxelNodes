import bpy


class AddCustomNode():

    nodes_file: bpy.props.StringProperty(
        name="nodes_file",
        subtype='FILE_PATH',
        default=""
    )  # type: ignore

    node_type: bpy.props.StringProperty(
        name='node_type',
        description='',
        default='',
        subtype='NONE',
        maxlen=0
    )  # type: ignore

    node_label: bpy.props.StringProperty(
        name='node_label',
        default=''
    )  # type: ignore

    node_description: bpy.props.StringProperty(
        name="node_description",
        description="",
        default="",
        subtype="NONE"
    )  # type: ignore

    node_link: bpy.props.BoolProperty(
        name='node_link',
        default=True
    )  # type: ignore

    node_callback: bpy.props.StringProperty(
        name='node_callback',
        default=''
    )  # type: ignore

    @classmethod
    def description(cls, context, properties):
        return properties.node_description

    def assign_node_tree(self, node):
        node.node_tree = bpy.data.node_groups[self.node_type]

        node.width = 200.0
        node.label = self.node_label or self.node_type
        node.name = self.node_type

        if self.node_callback:
            exec(self.node_callback)

        return node

    def get_node_tree(self, node_type, node_link):
        # try to get node from current file if exists
        node_tree = bpy.data.node_groups.get(node_type)
        # if not exists, get it from asset file.
        if not node_tree:
            bpy.ops.wm.append(
                'EXEC_DEFAULT',
                directory=f"{self.nodes_file}/NodeTree",
                filename=node_type,
                link=node_link,
                use_recursive=True
            )

        node_tree = bpy.data.node_groups.get(node_type)
        if node_tree:
            return node_tree
        else:
            raise RuntimeError('No custom node found')


    def add_node(self, node_group):
        # Deselect all nodes first
        for node in node_group.nodes:
            if node.select:
                node.select = False

        self.get_node_tree(self.node_type, self.node_link)
        node = node_group.nodes.new("GeometryNodeGroup")
        self.assign_node_tree(node)
        node.show_options = False

        return node


class CUSTOMNODES_OT_Add_Custom_Node(bpy.types.Operator, AddCustomNode):
    bl_idname = "customnodes.add_custom_node"
    bl_label = "Add Custom Node"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        self.get_node_tree(self.node_type, self.node_link)

        # intended to be called upon button press in the node tree
        prev_context = bpy.context.area.type
        bpy.context.area.type = 'NODE_EDITOR'
        # actually invoke the operator to add a node to the current node tree
        # use_transform=True ensures it appears where the user's mouse is and is currently
        # being moved so the user can place it where they wish
        bpy.ops.node.add_node(
            'INVOKE_DEFAULT',
            type='GeometryNodeGroup',
            use_transform=True
        )
        bpy.context.area.type = prev_context
        node = bpy.context.active_node

        self.assign_node_tree(node)
        node.show_options = False

        return {"FINISHED"}
