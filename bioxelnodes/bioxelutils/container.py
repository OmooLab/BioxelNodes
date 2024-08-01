import bpy

from ..bioxel.container import Container
from bpy_extras.io_utils import axis_conversion
from mathutils import Matrix, Vector


from .layer import Layer, get_container_layer_objs, layer_to_obj, obj_to_layer
from ..nodes import custom_nodes
from .node import get_nodes_by_type, move_node_to_node


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


def add_layers(layers: list[Layer],
               container_obj: bpy.types.Object,
               cache_dir: str):

    container_node_group = container_obj.modifiers[0].node_group

    for i, layer in enumerate(layers):
        layer_obj = layer_to_obj(layer, container_obj, cache_dir)
        mask_node = custom_nodes.add_node(container_node_group,
                                          NODE_TYPE[layer.kind])
        mask_node.label = layer_obj.name
        mask_node.inputs[0].default_value = layer_obj

        # Connect to output if no output linked
        output_node = get_nodes_by_type(container_node_group,
                                        'NodeGroupOutput')[0]
        if len(output_node.inputs[0].links) == 0:
            container_node_group.links.new(mask_node.outputs[0],
                                           output_node.inputs[0])
            move_node_to_node(mask_node, output_node, (-300, 0))
        else:
            move_node_to_node(mask_node, output_node, (0, -100 * (i+1)))

    return container_obj


def obj_to_container(container_obj: bpy.types.Object):
    layer_objs = get_container_layer_objs(container_obj)
    layers = [obj_to_layer(obj) for obj in layer_objs]
    container = Container(name=container_obj.name,
                          layers=layers)
    return container


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

    bpy.ops.node.new_geometry_nodes_modifier()
    container_node_group = container_obj.modifiers[0].node_group
    input_node = get_nodes_by_type(container_node_group,
                                   'NodeGroupInput')[0]
    container_node_group.links.remove(
        input_node.outputs[0].links[0])

    for i, layer in enumerate(container.layers):
        layer_obj = layer_to_obj(layer, container_obj, cache_dir)
        mask_node = custom_nodes.add_node(container_node_group,
                                          NODE_TYPE[layer.kind])
        mask_node.label = layer_obj.name
        mask_node.inputs[0].default_value = layer_obj

        # Connect to output if no output linked
        output_node = get_nodes_by_type(container_node_group,
                                        'NodeGroupOutput')[0]
        if len(output_node.inputs[0].links) == 0:
            container_node_group.links.new(mask_node.outputs[0],
                                           output_node.inputs[0])
            move_node_to_node(mask_node, output_node, (-300, 0))
        else:
            move_node_to_node(mask_node, output_node, (0, -100 * (i+1)))

    return container_obj
