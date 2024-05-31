from pathlib import Path
import bpy
import pyopenvdb as vdb
from uuid import uuid4
from .nodes import custom_nodes
from .utils import (get_container, get_container_layers,
                    get_layer, get_node_by_type, hide_in_ray, lock_transform)


def get_scalar_layer_selection(self, context):
    items = [("None", "None", "")]
    base_layer = bpy.data.objects[self.base_layer]
    container = base_layer.parent
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
    base_layer = bpy.data.objects[self.base_layer]
    container = base_layer.parent
    for layer in get_container_layers(container):
        if layer.get("bioxel_layer_type") == "label":
            items.append((
                layer.name,
                layer.name,
                ""
            ))

    return items


class JoinLayers(bpy.types.Operator):
    bl_idname = "bioxelnodes.join_layers"
    bl_label = "Join Additinal Layers"
    bl_description = "Join Layers"
    bl_options = {'UNDO'}

    base_layer: bpy.props.StringProperty(
        options={"HIDDEN"}
    )   # type: ignore

    scalar_layer: bpy.props.EnumProperty(
        name="Scaler Layer",
        items=get_scalar_layer_selection
    )  # type: ignore

    label_layer: bpy.props.EnumProperty(
        name="Label Layer",
        items=get_label_layer_selection
    )  # type: ignore
    # color_layer: bpy.props.StringProperty()   # type: ignore

    @classmethod
    def poll(cls, context):
        layer = get_layer(bpy.context.active_object)
        return True if layer else False

    def execute(self, context):
        base_layer = bpy.data.objects[self.base_layer]

        if not base_layer:
            self.report({"WARNING"}, "Cannot find any bioxel layer as base.")
            return {'FINISHED'}

        base_layer_dir = bpy.path.abspath(base_layer.data.filepath)
        base_grids, base_metadata = vdb.readAll(base_layer_dir)

        preferences = context.preferences.addons[__package__].preferences
        cache_dir = Path(preferences.cache_dir, 'VDBs')
        cache_dir.mkdir(parents=True, exist_ok=True)

        layers = []
        if self.scalar_layer != "None":
            scalar_layer = bpy.data.objects[self.scalar_layer]
            layers.append(scalar_layer)

        if self.label_layer != "None":
            label_layer = bpy.data.objects[self.label_layer]
            layers.append(label_layer)

        # TODO: add color and vector

        if len(layers) == 0:
            self.report({"WARNING"}, "No additinal layers setted.")
            return {'FINISHED'}

        for layer in layers:
            layer_dir = bpy.path.abspath(layer.data.filepath)
            grids, metadata = vdb.readAll(layer_dir)
            base_grids.extend(grids)

        vdb_path = Path(cache_dir, f"{uuid4()}.vdb")
        print(f"Storing the VDB file ({str(vdb_path)})...")
        vdb.write(str(vdb_path), grids=base_grids)

        # Read VDB
        print(f"Loading the cache to Blender scene...")
        bpy.ops.object.volume_import(
            filepath=str(vdb_path), align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))

        joined_layer = bpy.context.active_object
        
        base_layer_node = base_layer.modifiers[0].node_group.nodes['BioxelNodes__ConvertToLayer']
        bioxel_size = base_layer_node.inputs['Bioxel Size'].default_value
        layer_shape = base_layer_node.inputs['Shape'].default_value
        layer_origin = base_layer_node.inputs['Origin'].default_value
        layer_rotation = base_layer_node.inputs['Rotation'].default_value
        scalar_offset = base_layer_node.inputs['Scalar Offset'].default_value
        scalar_min = base_layer_node.inputs['Scalar Min'].default_value
        scalar_max = base_layer_node.inputs['Scalar Max'].default_value
        
        if self.scalar_layer != "None":
            scalar_layer_node = scalar_layer.modifiers[0].node_group.nodes['BioxelNodes__ConvertToLayer']
            scalar_offset = scalar_layer_node.inputs['Scalar Offset'].default_value
            scalar_min = scalar_layer_node.inputs['Scalar Min'].default_value
            scalar_max = scalar_layer_node.inputs['Scalar Max'].default_value

        bpy.ops.node.new_geometry_nodes_modifier()
        node_tree = joined_layer.modifiers[0].node_group
        nodes = node_tree.nodes
        links = node_tree.links

        input_node = get_node_by_type(nodes, 'NodeGroupInput')[0]
        output_node = get_node_by_type(nodes, 'NodeGroupOutput')[0]
        

        joined_layer_node = custom_nodes.add_node(
            nodes, "BioxelNodes__ConvertToLayer")

        
        links.new(input_node.outputs[0], joined_layer_node.inputs[0])
        links.new(joined_layer_node.outputs[0], output_node.inputs[0])

        joined_layer_node.inputs['Bioxel Size'].default_value = bioxel_size
        joined_layer_node.inputs['Shape'].default_value = layer_shape
        joined_layer_node.inputs['Origin'].default_value = layer_origin
        joined_layer_node.inputs['Rotation'].default_value = layer_rotation
        joined_layer_node.inputs['Scalar Offset'].default_value = scalar_offset
        joined_layer_node.inputs['Scalar Min'].default_value = scalar_min
        joined_layer_node.inputs['Scalar Max'].default_value = scalar_max

        # Set props to VDB object
        joined_layer.name = f"{base_layer.name}_Joined"
        joined_layer.data.name = f"{base_layer.name}_Joined"

        lock_transform(joined_layer)
        hide_in_ray(joined_layer)
        joined_layer.hide_select = True
        joined_layer.hide_render = True
        joined_layer.hide_viewport = True
        joined_layer.data.display.use_slice = True
        joined_layer.data.display.density = 1e-05

        joined_layer['bioxel_layer'] = True
        joined_layer.parent = base_layer.parent

        return {'FINISHED'}

    def invoke(self, context, event):
        base_layer = get_layer(bpy.context.active_object)
        self.base_layer = base_layer.name
        context.window_manager.invoke_props_dialog(self, width=400)
        return {'RUNNING_MODAL'}


class ConvertToMesh(bpy.types.Operator):
    bl_idname = "bioxelnodes.convert_to_mesh"
    bl_label = "Bioxel Components To Mesh"
    bl_description = "Convert Bioxel Components To Mesh"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        container = get_container(bpy.context.active_object)
        return True if container else False

    def execute(self, context):
        container = get_container(bpy.context.active_object)

        if not container:
            self.report({"WARNING"}, "Cannot find any bioxel container.")
            return {'FINISHED'}

        bpy.ops.mesh.primitive_cube_add(
            size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        mesh = bpy.context.active_object

        mesh.name = f"Mesh_{container.name}"

        bpy.ops.object.constraint_add(type='COPY_TRANSFORMS')
        mesh.constraints["Copy Transforms"].target = container

        bpy.ops.node.new_geometry_nodes_modifier()
        modifier = mesh.modifiers[0]
        nodes = modifier.node_group.nodes
        links = modifier.node_group.links

        output_node = get_node_by_type(nodes, 'NodeGroupOutput')[0]
        object_node = nodes.new("GeometryNodeObjectInfo")
        realize_nodes = nodes.new("GeometryNodeRealizeInstances")
        separate_node = custom_nodes.add_node(
            nodes, "BioxelNodes__SeparateComponent")

        object_node.inputs[0].default_value = container
        separate_node.inputs[1].default_value = 1

        links.new(object_node.outputs['Geometry'], separate_node.inputs[0])
        links.new(separate_node.outputs[0], realize_nodes.inputs[0])
        links.new(realize_nodes.outputs[0], output_node.inputs[0])

        bpy.ops.object.convert(target='MESH')
        bpy.ops.constraint.apply(constraint="Copy Transforms", owner='OBJECT')
        bpy.context.object.active_material_index = 1
        bpy.ops.object.material_slot_remove()

        self.report({"INFO"}, f"Successfully convert to mesh")

        return {'FINISHED'}
