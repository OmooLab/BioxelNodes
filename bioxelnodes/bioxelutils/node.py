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
