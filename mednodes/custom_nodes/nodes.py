import bpy


def add_driver(target_prop, var_sources, expression):

    driver = target_prop.driver_add("default_value")
    is_vector = isinstance(driver, list)
    drivers = driver if is_vector else [driver]

    for i, driver in enumerate(drivers):
        for j, var_source in enumerate(var_sources):

            source = var_source['source']
            prop = var_source['prop']

            var = driver.driver.variables.new()
            var.name = f"var{j}"

            var.targets[0].id_type = source.id_type
            var.targets[0].id = source
            var.targets[0].data_path = f'["{prop}"][{i}]'\
                if is_vector else f'["{prop}"]'

        driver.driver.expression = expression


def add_direct_driver(target, target_prop, source, source_prop):
    target_prop = target.inputs.get(target_prop)
    drivers = [
        {
            "source": source,
            "prop": source_prop
        }
    ]
    expression = "var0"
    add_driver(target_prop, drivers, expression)


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

    node_driver: bpy.props.StringProperty(
        name='node_driver',
        default=''
    )  # type: ignore

    node_description: bpy.props.StringProperty(
        name="node_description",
        description="",
        default="Add custom node group.",
        subtype="NONE"
    )  # type: ignore

    node_link: bpy.props.BoolProperty(
        name='node_link',
        default=True
    )  # type: ignore

    @classmethod
    def description(cls, context, properties):
        return properties.node_description

    def assign_node_tree(self, node):
        node.node_tree = bpy.data.node_groups[self.node_type]

        node.width = 200.0
        node.label = self.node_label or self.node_type
        node.name = self.node_type

        if self.node_driver:
            source_prop = self.node_driver.split(":")[0]
            target_prop = self.node_driver.split(":")[1]
            add_direct_driver(
                target=node,
                target_prop=target_prop,
                source=bpy.context.active_object,
                source_prop=source_prop
            )

        return node

    def append_node_tree(self, node_type):
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
        self.append_node_tree(self.node_type)

        node = node_tree.new("GeometryNodeGroup")

        self.assign_node_tree(node)

        return node


class CUSTOMNODES_OT_Add_Custom_Node(bpy.types.Operator, AddCustomNode):
    bl_idname = "customnodes.add_custom_node"
    bl_label = "Add Custom Node"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        self.append_node_tree(self.node_type)

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
