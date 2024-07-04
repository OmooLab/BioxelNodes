from pathlib import Path
import random
import bpy
import pyopenvdb as vdb
import numpy as np

from . import skimage as ski
from . import scipy
from .nodes import custom_nodes
from .utils import (get_container, get_container_from_selection, get_container_layers,
                    get_layer, get_node_by_type, hide_in_ray, lock_transform, save_vdb)


def get_layer_name(layer):
    container = layer.parent
    return layer.name.removeprefix(container.name).replace("_", "")


def get_grids(layer):
    layer_dir = bpy.path.abspath(layer.data.filepath)
    grids, base_metadata = vdb.readAll(layer_dir)
    return grids


def set_volume(grids, index, volume):
    grids[index].clear()
    grids[index].copyFromArray(volume.copy().astype(np.float32))


def get_volume(grids, index, shape):
    volume = np.ndarray(shape, np.float32)
    volume.fill(index)
    grids[0].copyToArray(volume)
    return volume


def get_shape(layer):
    layer_node = layer.modifiers[0].node_group.nodes['BioxelNodes__ConvertToLayer']
    return [int(a)
            for a in layer_node.inputs['Shape'].default_value]


def get_layer_meta(layer, key: str):
    layer_node = layer.modifiers[0].node_group.nodes['BioxelNodes__ConvertToLayer']
    return layer_node.inputs[key].default_value


def set_layer_meta(layer, key: str, value):
    layer_node = layer.modifiers[0].node_group.nodes['BioxelNodes__ConvertToLayer']
    layer_node.inputs[key].default_value = value


def add_mask_node(container, layer, node_type: str, node_label: str):
    modifier = container.modifiers[0]
    node_tree = modifier.node_group
    
    # Deselect all nodes first
    for node in node_tree.nodes:
        if node.select:
            node.select = False
    
    mask_node = custom_nodes.add_node(node_tree.nodes, node_type)
    mask_node.label = node_label
    mask_node.inputs[0].default_value = layer

    # Connect to output if no output linked
    output_node = get_node_by_type(node_tree.nodes,
                                   'NodeGroupOutput')[0]
    if len(output_node.inputs[0].links) == 0:
        node_tree.links.new(mask_node.outputs[0],
                            output_node.inputs[0])

    return mask_node


def deep_copy_layer(vdb_path, base_layer, name):
    # Read VDB
    print(f"Loading the cache to Blender scene...")
    bpy.ops.object.volume_import(
        filepath=str(vdb_path), align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))

    copyed_layer = bpy.context.active_object

    # Set props to VDB object
    copyed_layer.name = name
    copyed_layer.data.name = name

    lock_transform(copyed_layer)
    hide_in_ray(copyed_layer)
    copyed_layer.hide_select = True
    copyed_layer.hide_render = True
    copyed_layer.hide_viewport = True
    copyed_layer.data.display.use_slice = True
    copyed_layer.data.display.density = 1e-05

    copyed_layer['bioxel_layer'] = True
    copyed_layer['bioxel_layer_type'] = base_layer['bioxel_layer_type']
    copyed_layer.parent = base_layer.parent

    for collection in copyed_layer.users_collection:
        collection.objects.unlink(copyed_layer)

    for collection in base_layer.users_collection:
        collection.objects.link(copyed_layer)

    # add convert to layer node
    base_layer_node = base_layer.modifiers[0].node_group.nodes['BioxelNodes__ConvertToLayer']

    bioxel_size = base_layer_node.inputs['Bioxel Size'].default_value
    layer_shape = base_layer_node.inputs['Shape'].default_value
    layer_origin = base_layer_node.inputs['Origin'].default_value
    layer_rotation = base_layer_node.inputs['Rotation'].default_value
    scalar_offset = base_layer_node.inputs['Scalar Offset'].default_value
    scalar_min = base_layer_node.inputs['Scalar Min'].default_value
    scalar_max = base_layer_node.inputs['Scalar Max'].default_value

    bpy.ops.node.new_geometry_nodes_modifier()
    node_tree = copyed_layer.modifiers[0].node_group

    input_node = get_node_by_type(node_tree.nodes, 'NodeGroupInput')[0]
    output_node = get_node_by_type(node_tree.nodes, 'NodeGroupOutput')[0]

    copyed_layer_node = custom_nodes.add_node(node_tree.nodes,
                                              "BioxelNodes__ConvertToLayer")

    node_tree.links.new(input_node.outputs[0], copyed_layer_node.inputs[0])
    node_tree.links.new(copyed_layer_node.outputs[0], output_node.inputs[0])

    copyed_layer_node.inputs['Layer ID'].default_value = random.randint(-200000000,
                                                                        200000000)
    copyed_layer_node.inputs['Bioxel Size'].default_value = bioxel_size
    copyed_layer_node.inputs['Shape'].default_value = layer_shape
    copyed_layer_node.inputs['Origin'].default_value = layer_origin
    copyed_layer_node.inputs['Rotation'].default_value = layer_rotation
    copyed_layer_node.inputs['Scalar Offset'].default_value = scalar_offset
    copyed_layer_node.inputs['Scalar Min'].default_value = scalar_min
    copyed_layer_node.inputs['Scalar Max'].default_value = scalar_max

    return copyed_layer


def get_scalar_layer_selection(self, context):
    items = [("None", "None", "")]
    container = get_container(bpy.context.active_object)
    for layer in get_container_layers(container):
        if layer.get("bioxel_layer_type") == "scalar":
            items.append((
                layer.name,
                layer.name,
                ""
            ))

    return items


def get_label_layer_selection(self, context):
    items = [("None", "None", "")]
    container = get_container(bpy.context.active_object)
    for layer in get_container_layers(container):
        if layer.get("bioxel_layer_type") == "label":
            items.append((
                layer.name,
                layer.name,
                ""
            ))

    return items


# class JoinLayers(bpy.types.Operator):
#     bl_idname = "bioxelnodes.join_layers"
#     bl_label = "Join Bioxel Layers"
#     bl_description = "Join Additional Bioxel Layers"
#     bl_options = {'UNDO'}

#     base_layer: bpy.props.StringProperty(
#         options={"HIDDEN"}
#     )   # type: ignore

#     scalar_layer: bpy.props.EnumProperty(
#         name="Scalar Layer",
#         items=get_scalar_layer_selection
#     )  # type: ignore

#     label_layer: bpy.props.EnumProperty(
#         name="Label Layer",
#         items=get_label_layer_selection
#     )  # type: ignore
#     # color_layer: bpy.props.StringProperty()   # type: ignore

#     @classmethod
#     def poll(cls, context):
#         layer = get_layer(bpy.context.active_object)
#         return True if layer else False

#     def execute(self, context):
#         base_layer = bpy.data.objects[self.base_layer]

#         if not base_layer:
#             self.report({"WARNING"}, "Cannot find any bioxel layer as base.")
#             return {'FINISHED'}

#         base_layer_dir = bpy.path.abspath(base_layer.data.filepath)
#         base_grids, base_metadata = vdb.readAll(base_layer_dir)

#         layers = []
#         if self.scalar_layer != "None":
#             scalar_layer = bpy.data.objects[self.scalar_layer]
#             layers.append(scalar_layer)

#         if self.label_layer != "None":
#             label_layer = bpy.data.objects[self.label_layer]
#             layers.append(label_layer)

#         # TODO: add color and vector

#         if len(layers) == 0:
#             self.report({"WARNING"}, "No additinal layers setted.")
#             return {'FINISHED'}

#         for layer in layers:
#             layer_dir = bpy.path.abspath(layer.data.filepath)
#             grids, metadata = vdb.readAll(layer_dir)
#             base_grids.extend(grids)

#         vdb_path = save_vdb(base_grids, context)

#         joined_layer = deep_copy_layer(vdb_path,
#                                        base_layer,
#                                        f"{base_layer.name}_Joined")

#         return {'FINISHED'}

#     def invoke(self, context, event):
#         base_layer = get_layer(bpy.context.active_object)
#         self.base_layer = base_layer.name
#         context.window_manager.invoke_props_dialog(self, width=400)
#         return {'RUNNING_MODAL'}


class InvertScalar(bpy.types.Operator):
    bl_idname = "bioxelnodes.invert_scalar"
    bl_label = "Invert Scalar"
    bl_description = "Invert the scalar value"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        layer = get_layer(bpy.context.active_object)
        if layer:
            return layer.get("bioxel_layer_type") == "scalar"
        else:
            return False

    def execute(self, context):
        base_layer = get_layer(bpy.context.active_object)

        container = base_layer.parent
        inverted_layer_name = f"{get_layer_name(base_layer)}_Inverted"

        base_shape = get_shape(base_layer)
        scalar_offset = get_layer_meta(base_layer, "Scalar Offset")

        base_grids = get_grids(base_layer)
        base_volume = get_volume(base_grids, 0, base_shape)

        base_volume = -(base_volume - scalar_offset)

        base_min = float(np.min(base_volume))
        base_max = float(np.max(base_volume))

        scalar_offset = 0
        if base_min < 0:
            scalar_offset = -base_min
            base_volume = base_volume + scalar_offset

        set_volume(base_grids, 0, base_volume)
        vdb_path = save_vdb(base_grids, context)
        inverted_layer = deep_copy_layer(vdb_path,
                                         base_layer,
                                         f"{container.name}_{inverted_layer_name}")
        set_layer_meta(inverted_layer, 'Scalar Offset', scalar_offset)
        set_layer_meta(inverted_layer, 'Scalar Min', base_min)
        set_layer_meta(inverted_layer, 'Scalar Max', base_max)

        add_mask_node(container,
                      inverted_layer,
                      "BioxelNodes_MaskByThreshold",
                      inverted_layer_name)

        bpy.context.view_layer.objects.active = container

        return {'FINISHED'}


class FillByThreshold(bpy.types.Operator):
    bl_idname = "bioxelnodes.fill_by_threshold"
    bl_label = "Fill by Threshold"
    bl_description = "Fill Value by Threshold"
    bl_options = {'UNDO'}

    threshold: bpy.props.FloatProperty(
        name="Threshold",
        soft_min=0, soft_max=1024,
        default=128,
    )  # type: ignore

    fill_value: bpy.props.FloatProperty(
        name="Fill Value",
        soft_min=0, soft_max=1024.0,
        default=0,
    )  # type: ignore

    invert: bpy.props.BoolProperty(
        name="Invert Area",
        default=True,
    )  # type: ignore

    @classmethod
    def poll(cls, context):
        layer = get_layer(bpy.context.active_object)
        if layer:
            return layer.get("bioxel_layer_type") == "scalar"
        else:
            return False

    def execute(self, context):
        base_layer = get_layer(bpy.context.active_object)

        container = base_layer.parent
        filled_layer_name = f"{get_layer_name(base_layer)}_{self.threshold}-Filled"
        scalar_offset = get_layer_meta(base_layer, "Scalar Offset")
        base_shape = get_shape(base_layer)

        base_grids = get_grids(base_layer)
        base_volume = get_volume(base_grids, 0, base_shape)
        mask = base_volume > (self.threshold + scalar_offset)
        mask = scipy.median_filter(mask.astype(np.float32), size=2)
        if self.invert:
            base_volume = mask * base_volume + \
                (1-mask) * (self.fill_value + scalar_offset)
        else:
            base_volume = (1-mask) * base_volume + \
                mask * (self.fill_value + scalar_offset)

        set_volume(base_grids, 0, base_volume)
        vdb_path = save_vdb(base_grids, context)
        filled_layer = deep_copy_layer(vdb_path,
                                       base_layer,
                                       f"{container.name}_{filled_layer_name}")
        mask_node = add_mask_node(container,
                                  filled_layer,
                                  "BioxelNodes_MaskByThreshold",
                                  filled_layer_name)

        mask_node.inputs[1].default_value = self.threshold

        bpy.context.view_layer.objects.active = container

        return {'FINISHED'}

    def invoke(self, context, event):
        base_layer = get_layer(bpy.context.active_object)
        scalar_min = get_layer_meta(base_layer, "Scalar Min")
        self.fill_value = scalar_min
        context.window_manager.invoke_props_dialog(self, width=400)
        return {'RUNNING_MODAL'}


class FillByRange(bpy.types.Operator):
    bl_idname = "bioxelnodes.fill_by_range"
    bl_label = "Fill by Range"
    bl_description = "Fill Value by Range"
    bl_options = {'UNDO'}

    from_min: bpy.props.FloatProperty(
        name="From Min",
        soft_min=0, soft_max=1024,
        default=128,
    )  # type: ignore

    from_max: bpy.props.FloatProperty(
        name="From Max",
        soft_min=0, soft_max=1024,
        default=256,
    )  # type: ignore

    fill_value: bpy.props.FloatProperty(
        name="Fill Value",
        soft_min=0, soft_max=1024.0,
        default=0,
    )  # type: ignore

    invert: bpy.props.BoolProperty(
        name="Invert Area",
        default=True,
    )  # type: ignore

    @classmethod
    def poll(cls, context):
        layer = get_layer(bpy.context.active_object)
        if layer:
            return layer.get("bioxel_layer_type") == "scalar"
        else:
            return False

    def execute(self, context):
        base_layer = get_layer(bpy.context.active_object)

        container = base_layer.parent
        filled_layer_name = f"{get_layer_name(base_layer)}_{self.from_min}-{self.from_max}-Filled"
        scalar_offset = get_layer_meta(base_layer, "Scalar Offset")
        base_shape = get_shape(base_layer)

        base_grids = get_grids(base_layer)
        base_volume = get_volume(base_grids, 0, base_shape)

        mask = (base_volume > self.from_min + scalar_offset) \
            & (base_volume < self.from_max + scalar_offset)
        mask = scipy.median_filter(mask.astype(np.float32), size=2)

        if self.invert:
            base_volume = mask * base_volume + \
                (1-mask) * (self.fill_value + scalar_offset)
        else:
            base_volume = (1-mask) * base_volume + \
                mask * (self.fill_value + scalar_offset)

        set_volume(base_grids, 0, base_volume)
        vdb_path = save_vdb(base_grids, context)
        filled_layer = deep_copy_layer(vdb_path,
                                       base_layer,
                                       f"{container.name}_{filled_layer_name}")
        mask_node = add_mask_node(container,
                                  filled_layer,
                                  "BioxelNodes_MaskByThreshold",
                                  filled_layer_name)

        mask_node.inputs[1].default_value = self.from_min

        bpy.context.view_layer.objects.active = container

        return {'FINISHED'}

    def invoke(self, context, event):
        base_layer = get_layer(bpy.context.active_object)
        scalar_min = get_layer_meta(base_layer, "Scalar Min")
        self.fill_value = scalar_min
        context.window_manager.invoke_props_dialog(self, width=400)
        return {'RUNNING_MODAL'}


class FillByLabel(bpy.types.Operator):
    bl_idname = "bioxelnodes.fill_by_label"
    bl_label = "Fill by Label"
    bl_description = "Fill Value by Label Area"
    bl_options = {'UNDO'}

    label_layer: bpy.props.EnumProperty(
        name="Label Layer",
        items=get_label_layer_selection
    )  # type: ignore

    fill_value: bpy.props.FloatProperty(
        name="Fill Value",
        soft_min=0, soft_max=1024.0,
        default=0,
    )  # type: ignore

    invert: bpy.props.BoolProperty(
        name="Invert Label",
        default=True,
    )  # type: ignore

    @classmethod
    def poll(cls, context):
        layer = get_layer(bpy.context.active_object)
        if layer:
            return layer.get("bioxel_layer_type") == "scalar"
        else:
            return False

    def execute(self, context):
        base_layer = get_layer(bpy.context.active_object)
        label_layer = bpy.data.objects[self.label_layer]

        if not label_layer:
            self.report({"WARNING"}, "Cannot find any label layer.")
            return {'FINISHED'}

        container = base_layer.parent
        filled_layer_name = f"{get_layer_name(base_layer)}_{get_layer_name(label_layer)}-Filled"
        scalar_offset = get_layer_meta(base_layer, "Scalar Offset")
        base_shape = get_shape(base_layer)
        label_shape = get_shape(label_layer)

        base_grids = get_grids(base_layer)
        base_volume = get_volume(base_grids, 0, base_shape)

        label_grids = get_grids(label_layer)
        mask = get_volume(label_grids, 0, label_shape)
        mask = ski.resize(mask,
                          base_shape,
                          anti_aliasing=True)
        mask = scipy.median_filter(mask.astype(np.float32), size=2)

        if self.invert:
            base_volume = mask * base_volume + \
                (1-mask) * (self.fill_value + scalar_offset)
        else:
            base_volume = (1-mask) * base_volume + \
                mask * (self.fill_value + scalar_offset)

        set_volume(base_grids, 0, base_volume)
        vdb_path = save_vdb(base_grids, context)
        filled_layer = deep_copy_layer(vdb_path,
                                       base_layer,
                                       f"{container.name}_{filled_layer_name}")
        add_mask_node(container,
                      filled_layer,
                      "BioxelNodes_MaskByThreshold",
                      filled_layer_name)

        bpy.context.view_layer.objects.active = container

        return {'FINISHED'}

    def invoke(self, context, event):
        base_layer = get_layer(bpy.context.active_object)
        scalar_min = get_layer_meta(base_layer, "Scalar Min")
        self.fill_value = scalar_min
        context.window_manager.invoke_props_dialog(self, width=400)
        return {'RUNNING_MODAL'}


class CombineLabels(bpy.types.Operator):
    bl_idname = "bioxelnodes.combine_labels"
    bl_label = "Combine Labels"
    bl_description = "Combine all selected labels"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        labels = [obj for obj in context.selected_ids
                  if obj.get("bioxel_layer_type") == "label"]
        return True if len(labels) > 1 else False

    def execute(self, context):
        labels = [obj for obj in context.selected_ids
                  if obj.get("bioxel_layer_type") == "label"]
        base_layer = labels[0]
        labels = labels[1:]
        container = base_layer.parent
        label_names = [get_layer_name(base_layer)]
        base_shape = get_shape(base_layer)

        base_grids = get_grids(base_layer)
        base_volume = get_volume(base_grids, 0, base_shape)
        base_volume = base_volume

        for label in labels:
            label_shape = get_shape(label)
            label_grids = get_grids(label)
            label_volume = get_volume(label_grids, 0, label_shape)
            label_volume = ski.resize(label_volume,
                                      base_shape,
                                      anti_aliasing=True)
            base_volume = np.maximum(base_volume, label_volume)
            label_names.append(get_layer_name(label))

        set_volume(base_grids, 0, base_volume)

        combined_layer_name = f"{'-'.join(label_names)}-Combined"
        vdb_path = save_vdb(base_grids, context)
        combined_layer = deep_copy_layer(vdb_path,
                                         base_layer,
                                         f"{container.name}_{combined_layer_name}")
        add_mask_node(container,
                      combined_layer,
                      "BioxelNodes_MaskByLabel",
                      combined_layer_name)

        bpy.context.view_layer.objects.active = container
        return {'FINISHED'}


class ConvertToMesh(bpy.types.Operator):
    bl_idname = "bioxelnodes.convert_to_mesh"
    bl_label = "Convert To Mesh"
    bl_description = "Convert Bioxel Components To Mesh"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        containers = get_container_from_selection()
        return len(containers) > 0

    def execute(self, context):
        containers = get_container_from_selection()

        if len(containers) == 0:
            self.report({"WARNING"}, "Cannot find any bioxel container.")
            return {'FINISHED'}

        container = containers[0]

        bpy.ops.mesh.primitive_cube_add(
            size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        mesh = bpy.context.active_object

        mesh.name = f"Mesh_{container.name}"

        # bpy.ops.object.constraint_add(type='COPY_TRANSFORMS')
        # mesh.constraints[0].target = container

        bpy.ops.node.new_geometry_nodes_modifier()
        modifier = mesh.modifiers[0]
        node_tree = modifier.node_group

        output_node = get_node_by_type(node_tree.nodes, 'NodeGroupOutput')[0]
        to_mesh_node = custom_nodes.add_node(node_tree.nodes,
                                              "BioxelNodes_ToMesh")

        to_mesh_node.inputs[0].default_value = container
        node_tree.links.new(to_mesh_node.outputs[0], output_node.inputs[0])

        bpy.ops.object.convert(target='MESH')
        # bpy.ops.constraint.apply(
        #     constraint=mesh.constraints[0].name, owner='OBJECT')
        bpy.context.object.active_material_index = 1
        bpy.ops.object.material_slot_remove()

        self.report({"INFO"}, f"Successfully convert to mesh")

        return {'FINISHED'}


class AddCutter():
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        containers = get_container_from_selection()
        return len(containers) > 0

    def execute(self, context):
        containers = get_container_from_selection()

        if len(containers) == 0:
            self.report({"WARNING"}, "Cannot find any bioxel container.")
            return {'FINISHED'}

        container = containers[0]

        if self.object_type == "plane":
            node_type = "BioxelNodes_PlaneObjectCutter"
            bpy.ops.mesh.primitive_plane_add(
                size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        elif self.object_type == "cylinder":
            node_type = "BioxelNodes_CylinderObjectCutter"
            bpy.ops.mesh.primitive_cylinder_add(
                radius=1, depth=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
            bpy.context.object.rotation_euler[0] = container.rotation_euler[0]
        elif self.object_type == "cube":
            node_type = "BioxelNodes_CubeObjectCutter"
            bpy.ops.mesh.primitive_cube_add(
                size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        elif self.object_type == "sphere":
            node_type = "BioxelNodes_SphereObjectCutter"
            bpy.ops.mesh.primitive_ico_sphere_add(
                radius=1, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))

        cutter = bpy.context.active_object
        cutter.visible_camera = False
        cutter.visible_diffuse = False
        cutter.visible_glossy = False
        cutter.visible_transmission = False
        cutter.visible_volume_scatter = False
        cutter.visible_shadow = False
        cutter.hide_render = True
        cutter.display_type = 'WIRE'

        modifier = container.modifiers[0]
        node_tree = modifier.node_group
        cutter_node = custom_nodes.add_node(node_tree.nodes, node_type)
        cutter_node.inputs[0].default_value = cutter

        bpy.context.view_layer.objects.active = container

        return {'FINISHED'}


class AddPlaneCutter(bpy.types.Operator, AddCutter):
    bl_idname = "bioxelnodes.add_plane_cutter"
    bl_label = "Add Plane Cutter"
    bl_description = "Add Plane Cutter to Container"
    bl_options = {'UNDO'}
    object_type = "plane"


class AddCylinderCutter(bpy.types.Operator, AddCutter):
    bl_idname = "bioxelnodes.add_cylinder_cutter"
    bl_label = "Add Cylinder Cutter"
    bl_description = "Add Cylinder Cutter to Container"
    bl_options = {'UNDO'}
    object_type = "cylinder"


class AddCubeCutter(bpy.types.Operator, AddCutter):
    bl_idname = "bioxelnodes.add_cube_cutter"
    bl_label = "Add Cube Cutter"
    bl_description = "Add Cube Cutter to Container"
    bl_options = {'UNDO'}
    object_type = "cube"


class AddSphereCutter(bpy.types.Operator, AddCutter):
    bl_idname = "bioxelnodes.add_sphere_cutter"
    bl_label = "Add Sphere Cutter"
    bl_description = "Add Sphere Cutter to Container"
    bl_options = {'UNDO'}
    object_type = "sphere"
