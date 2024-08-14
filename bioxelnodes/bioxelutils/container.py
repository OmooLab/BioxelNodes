import bpy

from ..bioxel.container import Container
from bpy_extras.io_utils import axis_conversion
from mathutils import Matrix, Vector


from .layer import Layer, layer_to_obj, obj_to_layer
from ..nodes import custom_nodes
from .utils import (get_container_layer_objs,
                    get_layer_prop_value,
                    get_nodes_by_type,
                    move_node_to_node)


NODE_TYPE = {
    "label": "BioxelNodes_MaskByLabel",
    "scalar": "BioxelNodes_MaskByThreshold"
}


def calc_bbox_verts(origin: tuple, size: tuple):
    bbox_origin = Vector(
        (origin[0], origin[1], origin[2]))
    bbox_size = Vector(
        (size[0], size[1], size[2]))
    bbox_verts = [
        (
            bbox_origin[0] + 0,
            bbox_origin[1] + 0,
            bbox_origin[2] + 0
        ),
        (
            bbox_origin[0] + 0,
            bbox_origin[1] + 0,
            bbox_origin[2] + bbox_size[2]
        ),
        (
            bbox_origin[0] + 0,
            bbox_origin[1] + bbox_size[1],
            bbox_origin[2] + 0
        ),
        (
            bbox_origin[0] + 0,
            bbox_origin[1] + bbox_size[1],
            bbox_origin[2] + bbox_size[2]
        ),
        (
            bbox_origin[0] + bbox_size[0],
            bbox_origin[1] + 0,
            bbox_origin[2] + 0
        ),
        (
            bbox_origin[0] + bbox_size[0],
            bbox_origin[1] + 0,
            bbox_origin[2] + bbox_size[2],
        ),
        (
            bbox_origin[0] + bbox_size[0],
            bbox_origin[1] + bbox_size[1],
            bbox_origin[2] + 0,
        ),
        (
            bbox_origin[0] + bbox_size[0],
            bbox_origin[1] + bbox_size[1],
            bbox_origin[2] + bbox_size[2],
        ),
    ]
    return bbox_verts


def obj_to_container(container_obj: bpy.types.Object):
    layer_objs = get_container_layer_objs(container_obj)
    layers = [obj_to_layer(obj) for obj in layer_objs]
    container = Container(name=container_obj.name,
                          layers=layers)
    return container


def add_layers(layers: list[Layer],
               container_obj: bpy.types.Object,
               cache_dir: str):

    node_group = container_obj.modifiers[0].node_group
    output_node = get_nodes_by_type(node_group,
                                    'NodeGroupOutput')[0]

    for i, layer in enumerate(layers):
        layer_obj = layer_to_obj(layer, container_obj, cache_dir)
        fetch_node = custom_nodes.add_node(node_group,
                                           "BioxelNodes_FetchLayer")
        fetch_node.label = get_layer_prop_value(layer_obj, "name")
        fetch_node.inputs[0].default_value = layer_obj

        if len(output_node.inputs[0].links) == 0:
            node_group.links.new(fetch_node.outputs[0],
                                 output_node.inputs[0])
            move_node_to_node(fetch_node, output_node, (-600, 0))
        else:
            move_node_to_node(fetch_node, output_node, (0, -100 * (i+1)))

    return container_obj


def container_to_obj(container: Container,
                     scene_scale: float,
                     cache_dir: str):
    # Wrapper a Container

    # Make transformation
    # (S)uperior  -Z -> Y
    # (A)osterior  Y -> Z
    mat_ras2blender = axis_conversion(from_forward='-Z',
                                      from_up='Y',
                                      to_forward='Y',
                                      to_up='Z').to_4x4()

    mat_scene_scale = Matrix.Scale(scene_scale,
                                   4)

    bpy.ops.mesh.primitive_cube_add(enter_editmode=False,
                                    align='WORLD',
                                    location=(0, 0, 0),
                                    scale=(1, 1, 1))

    container_obj = bpy.context.active_object

    bbox_verts = calc_bbox_verts((0, 0, 0), container.layers[0].shape)
    for i, vert in enumerate(container_obj.data.vertices):
        transform = Matrix(container.layers[0].affine)
        vert.co = transform @ Vector(bbox_verts[i])

    container_obj.matrix_world = mat_ras2blender @ mat_scene_scale
    container_obj.name = container.name
    container_obj.data.name = container.name
    container_obj.show_in_front = True
    container_obj['bioxel_container'] = True

    modifier = container_obj.modifiers.new("GeometryNodes", 'NODES')
    node_group = bpy.data.node_groups.new('GeometryNodes', 'GeometryNodeTree')
    node_group.interface.new_socket(name="Component",
                                    in_out="OUTPUT",
                                    socket_type="NodeSocketGeometry")
    modifier.node_group = node_group
    node_group.nodes.new("NodeGroupOutput")

    container_obj = add_layers(container.layers,
                               container_obj=container_obj,
                               cache_dir=cache_dir)

    return container_obj
