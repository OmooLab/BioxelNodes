import bpy


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


def get_container_objs_from_selection():
    container_objs = []
    for obj in bpy.context.selected_objects:
        if get_container_obj(obj):
            container_objs.append(obj)

    return list(set(container_objs))


def get_container_obj(current_obj):
    if current_obj:
        if current_obj.get('bioxel_container'):
            return current_obj
        elif current_obj.get('bioxel_layer'):
            parent = current_obj.parent
            return parent if parent.get('bioxel_container') else None
    return None


def get_layer_prop_value(layer_obj: bpy.types.Object, prop: str):
    node_group = layer_obj.modifiers[0].node_group
    layer_node = get_nodes_by_type(node_group, "BioxelNodes__Layer")[0]
    value = layer_node.inputs[prop].default_value
    if type(value).__name__ == "bpy_prop_array":
        value = tuple(value)
        return tuple([int(v) for v in value]) \
            if prop in ["shape"] else value
    elif type(value).__name__ == "str":
        return str(value)
    if type(value).__name__ == "float":
        value = float(value)
        return round(value, 2) \
            if prop in ["bioxel_size"] else value


def set_layer_prop_value(layer_obj: bpy.types.Object, prop: str, value):
    node_group = layer_obj.modifiers[0].node_group
    layer_node = get_nodes_by_type(node_group, "BioxelNodes__Layer")[0]
    layer_node.inputs[prop].default_value = value


def get_layer_obj(current_obj: bpy.types.Object):
    if current_obj:
        if current_obj.get('bioxel_layer') and current_obj.parent:
            if current_obj.parent.get('bioxel_container'):
                return current_obj
    return None


def get_container_layer_objs(container_obj: bpy.types.Object):
    layer_objs = []
    for obj in bpy.data.objects:
        if obj.parent == container_obj and get_layer_obj(obj):
            layer_objs.append(obj)

    return layer_objs


def get_all_layer_objs():
    layer_objs = []
    for obj in bpy.data.objects:
        if get_layer_obj(obj):
            layer_objs.append(obj)

    return layer_objs
