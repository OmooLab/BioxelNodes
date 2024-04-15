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
        default="Add custom node group.",
        subtype="NONE"
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

    def get_node_tree(self, node_type):
        # try to get node from current file if exists
        node_tree = bpy.data.node_groups.get(node_type)
        # if not exists, get it from asset file.
        if not node_tree:
            bpy.ops.wm.append(
                'EXEC_DEFAULT',
                directory=f"{self.nodes_file}/NodeTree",
                filename=node_type,
                link=False,
                use_recursive=True
            )

        node_tree = bpy.data.node_groups.get(node_type)
        if node_tree:
            # self.recursive_append_material(node_tree)
            return node_tree
        else:
            raise RuntimeError('No custom node found')

    def recursive_append_material(self, node_tree):
        for child in node_tree.nodes:
            material_socket = child.inputs.get('Material')
            if material_socket:
                print(material_socket.default_value)
            try:
                self.recursive_append_material(child.node_tree)
            except:
                ...

    def add_node(self, node_tree):
        self.get_node_tree(self.node_type)

        node = node_tree.new("GeometryNodeGroup")

        self.assign_node_tree(node)

        return node


class CUSTOMNODES_OT_Add_Custom_Node(bpy.types.Operator, AddCustomNode):
    bl_idname = "customnodes.add_custom_node"
    bl_label = "Add Custom Node"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        self.get_node_tree(self.node_type)

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

        return {"FINISHED"}
