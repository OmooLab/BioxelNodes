import bpy


import bmesh

from ..constants import COMPONENT_OUTPUT_NODES
from ..utils import get_cache_dir, get_use_link, select_object
from ..bioxel.io import load_container, save_container
from ..bioxelutils.container import container_to_obj, obj_to_container
from ..bioxelutils.node import add_node_to_graph
from ..bioxelutils.common import (get_container_layer_objs, get_container_obj, get_node_type,
                                  get_nodes_by_type, get_output_node, is_missing_layer,
                                  move_node_between_nodes,
                                  move_node_to_node,
                                  get_all_layer_objs)
from .layer import RemoveLayers, SaveLayersCache


class SaveContainer(bpy.types.Operator):
    bl_idname = "bioxelnodes.save_container"
    bl_label = "Save Container (.bioxel) (BETA)"
    bl_description = "Clean all caches saved in temp"

    filepath: bpy.props.StringProperty(
        subtype="FILE_PATH"
    )  # type: ignore

    filename_ext = ".bioxel"

    def execute(self, context):
        container_obj = get_container_obj(context.object)

        if container_obj is None:
            self.report({"WARNING"}, "Cannot find any bioxel container.")
            return {'FINISHED'}

        container = obj_to_container(container_obj)
        save_path = f"{self.filepath.split('.')[0]}.bioxel"
        save_container(container, save_path, overwrite=True)

        self.report({"INFO"}, f"Successfully save to {save_path}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class LoadContainer(bpy.types.Operator):
    bl_idname = "bioxelnodes.load_container"
    bl_label = "Load Container (.bioxel) (BETA)"
    bl_description = "Clean all caches saved in temp"

    filepath: bpy.props.StringProperty(
        subtype="FILE_PATH"
    )  # type: ignore

    filename_ext = ".bioxel"

    def execute(self, context):
        load_path = self.filepath
        container = load_container(self.filepath)
        is_first_import = len(get_all_layer_objs()) == 0

        container_obj = container_to_obj(container,
                                         scene_scale=0.01,
                                         cache_dir=get_cache_dir())
        select_object(container_obj)

        if is_first_import:
            bpy.ops.bioxelnodes.render_setting_preset('EXEC_DEFAULT',
                                                      preset="preview_c")

        self.report({"INFO"}, f"Successfully load {load_path}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class ExtractNodeObject():
    bl_options = {'UNDO'}

    def execute(self, context):
        container_obj = get_container_obj(context.object)

        if container_obj is None:
            self.report({"WARNING"}, "Cannot find any bioxel container.")
            return {'FINISHED'}

        # nodes = [node for node in context.selected_nodes
        #          if get_node_type(node).removeprefix("BioxelNodes_") in COMPONENT_OUTPUT_NODES]

        if len(context.selected_nodes) == 0:
            self.report({"WARNING"}, "No node selected.")
            return {'FINISHED'}

        selected_node = context.selected_nodes[0]
        container_node_group = container_obj.modifiers[0].node_group

        container_output_node = get_output_node(container_node_group)

        if len(container_output_node.inputs[0].links) == 0:
            pre_socket = None
        else:
            pre_socket = container_output_node.inputs[0].links[0].from_socket

        container_node_group.links.new(selected_node.outputs[0],
                                       container_output_node.inputs[0])

        bpy.ops.mesh.primitive_cube_add(
            size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        obj = bpy.context.active_object

        obj.name = f"{container_obj.name}_{self.object_type}"

        bpy.ops.node.new_geometry_nodes_modifier()
        modifier = obj.modifiers[0]
        node_group = modifier.node_group

        output_node = get_nodes_by_type(node_group, 'NodeGroupOutput')[0]
        fetch_mesh_node = add_node_to_graph(f"Fetch{self.object_type}",
                                            node_group,
                                            node_label=f"Fetch {self.object_type}",
                                            use_link=get_use_link())

        fetch_mesh_node.inputs[0].default_value = container_obj
        node_group.links.new(fetch_mesh_node.outputs[0], output_node.inputs[0])

        for modifier in obj.modifiers:
            bpy.ops.object.modifier_apply(modifier=modifier.name)

        obj.data.materials.clear()

        if pre_socket:
            container_node_group.links.new(pre_socket,
                                           container_output_node.inputs[0])

        select_object(obj)

        self.report({"INFO"}, f"Successfully picked")

        return {'FINISHED'}


class ExtractNodeMesh(bpy.types.Operator, ExtractNodeObject):
    bl_idname = "bioxelnodes.extract_node_mesh"
    bl_label = "Extract Mesh"
    bl_description = "Extract Mesh"
    bl_icon = "OUTLINER_OB_MESH"
    object_type = "Mesh"


class ExtractNodeShapeWire(bpy.types.Operator, ExtractNodeObject):
    bl_idname = "bioxelnodes.extract_node_shape_wire"
    bl_label = "Extract Shape Wire"
    bl_description = "Extract Shape Wire"
    bl_icon = "FILE_VOLUME"
    object_type = "ShapeWire"


class ExtractNodeBboxWire(bpy.types.Operator, ExtractNodeObject):
    bl_idname = "bioxelnodes.extract_node_bbox_wire"
    bl_label = "Extract Bbox Wire"
    bl_description = "Extract Bbox Wire"
    bl_icon = "MESH_CUBE"
    object_type = "BboxWire"


class ExtractObject():
    bl_options = {'UNDO'}

    def execute(self, context):
        container_obj = get_container_obj(context.object)

        if container_obj is None:
            self.report({"WARNING"}, "Cannot find any bioxel container.")
            return {'FINISHED'}

        bpy.ops.mesh.primitive_cube_add(
            size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        obj = bpy.context.active_object

        obj.name = f"{container_obj.name}_{self.object_type}"

        bpy.ops.node.new_geometry_nodes_modifier()
        modifier = obj.modifiers[0]
        node_group = modifier.node_group

        output_node = get_output_node(node_group)

        fetch_mesh_node = add_node_to_graph(f"Fetch{self.object_type}",
                                            node_group,
                                            node_label=f"Fetch {self.object_type}",
                                            use_link=get_use_link())

        fetch_mesh_node.inputs[0].default_value = container_obj

        if self.object_type == "Mesh":
            node_group.links.new(
                fetch_mesh_node.outputs[0], output_node.inputs[0])
        else:
            curve_to_mesh_node = node_group.nodes.new(
                "GeometryNodeCurveToMesh")
            node_group.links.new(
                fetch_mesh_node.outputs[0], curve_to_mesh_node.inputs[0])
            node_group.links.new(
                curve_to_mesh_node.outputs[0], output_node.inputs[0])

        for modifier in obj.modifiers:
            bpy.ops.object.modifier_apply(modifier=modifier.name)

        obj.data.materials.clear()

        select_object(obj)

        self.report({"INFO"}, f"Successfully picked")

        return {'FINISHED'}


class ExtractMesh(bpy.types.Operator, ExtractObject):
    bl_idname = "bioxelnodes.extract_mesh"
    bl_label = "Extract Mesh"
    bl_description = "Extract Mesh"
    bl_icon = "OUTLINER_OB_MESH"
    object_type = "Mesh"


class ExtractShapeWire(bpy.types.Operator, ExtractObject):
    bl_idname = "bioxelnodes.extract_shape_wire"
    bl_label = "Extract Shape Wire"
    bl_description = "Extract Shape Wire"
    bl_icon = "FILE_VOLUME"
    object_type = "ShapeWire"


class ExtractBboxWire(bpy.types.Operator, ExtractObject):
    bl_idname = "bioxelnodes.extract_bbox_wire"
    bl_label = "Extract Bbox Wire"
    bl_description = "Extract Bbox Wire"
    bl_icon = "MESH_CUBE"
    object_type = "BboxWire"


class AddCutter():
    bl_options = {'UNDO'}

    def execute(self, context):
        container_obj = get_container_obj(context.object)

        if container_obj is None:
            self.report({"WARNING"}, "Cannot find any bioxel container.")
            return {'FINISHED'}
        # TODO: do not use operator to create obj
        if self.cutter_type == "plane":
            bpy.ops.mesh.primitive_plane_add(
                size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        elif self.cutter_type == "cylinder":
            bpy.ops.mesh.primitive_cylinder_add(
                radius=1, depth=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
            bpy.context.object.rotation_euler[0] = container_obj.rotation_euler[0]
        elif self.cutter_type == "cube":
            bpy.ops.mesh.primitive_cube_add(
                size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        elif self.cutter_type == "sphere":
            bpy.ops.mesh.primitive_ico_sphere_add(
                radius=1, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        elif self.cutter_type == "pie":
            bpy.ops.mesh.primitive_plane_add(
                size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
            pie_obj = bpy.context.active_object
            orig_data = pie_obj.data

            # Create mesh
            pie_mesh = bpy.data.meshes.new('Pie')
            pie_obj.data = pie_mesh
            bpy.data.meshes.remove(orig_data)

            # # Create object
            # pie = bpy.data.objects.new('Pie', pie_mesh)

            # # Link object to scene
            # bpy.context.scene.collection.objects.link(pie)

            # Get a BMesh representation
            bm = bmesh.new()   # create an empty BMesh
            bm.from_mesh(pie_mesh)   # fill it in from a Mesh

            # Hot to create vertices
            v_0 = bm.verts.new((0.0, -1.0, 0.0))
            v_1 = bm.verts.new((-1.0, -1.0, 1.0))
            v_2 = bm.verts.new((0.0, 1.0, 0.0))
            v_3 = bm.verts.new((-1.0, 1.0, 1.0))
            v_4 = bm.verts.new((1.0, -1.0, 1.0))
            v_5 = bm.verts.new((1.0, 1.0, 1.0))

            # Initialize the index values of this sequence.
            bm.verts.index_update()

            # How to create a face
            # it's not necessary to create the edges before, I made it only to show how create
            # edges too
            bm.faces.new((v_0, v_1, v_3, v_2))
            bm.faces.new((v_0, v_2, v_5, v_4))

            # Finish up, write the bmesh back to the mesh
            bm.to_mesh(pie_mesh)
            # bpy.context.view_layer.objects.active = pie

        cutter_obj = bpy.context.active_object

        # vcos = [container_obj.matrix_world @
        #         v.co for v in container_obj.data.vertices]

        # def find_center(l): return (max(l) + min(l)) / 2

        # x, y, z = [[v[i] for v in vcos] for i in range(3)]
        # center = [find_center(axis) for axis in [x, y, z]]

        # cutter_obj.location = center
        name = f"{self.cutter_type.capitalize()}_Cutter"
        cutter_obj.name = name
        cutter_obj.data.name = name
        cutter_obj.visible_camera = False
        cutter_obj.visible_diffuse = False
        cutter_obj.visible_glossy = False
        cutter_obj.visible_transmission = False
        cutter_obj.visible_volume_scatter = False
        cutter_obj.visible_shadow = False
        cutter_obj.hide_render = True
        cutter_obj.display_type = 'WIRE'
        cutter_obj.lineart.usage = 'EXCLUDE'

        select_object(container_obj)

        modifier = container_obj.modifiers[0]
        node_group = modifier.node_group

        cut_nodes = get_nodes_by_type(node_group,
                                      'BioxelNodes_Cut')
        if len(cut_nodes) == 0:
            cutter_node = add_node_to_graph("ObjectCutter",
                                            node_group,
                                            node_label=f"{self.cutter_type.capitalize()} Cutter",
                                            use_link=get_use_link())
            cutter_node.inputs[0].default_value = self.cutter_type.capitalize()
            cutter_node.inputs[1].default_value = cutter_obj

            cut_node = add_node_to_graph("Cut",
                                         node_group,
                                         use_link=get_use_link())

            output_node = get_output_node(node_group)

            if len(output_node.inputs[0].links) == 0:
                node_group.links.new(cut_node.outputs[0],
                                     output_node.inputs[0])
                move_node_to_node(cut_node, output_node, (-300, 0))
            else:
                pre_output_node = output_node.inputs[0].links[0].from_node
                node_group.links.new(pre_output_node.outputs[0],
                                     cut_node.inputs[0])
                node_group.links.new(cut_node.outputs[0],
                                     output_node.inputs[0])
                move_node_between_nodes(cut_node,
                                        [pre_output_node, output_node])

            node_group.links.new(cutter_node.outputs[0],
                                 cut_node.inputs[1])

            move_node_to_node(cutter_node, cut_node, (-300, -300))
        else:
            bpy.ops.bioxelnodes.add_node('EXEC_DEFAULT',
                                         node_name="ObjectCutter",
                                         node_label=name)
            node = bpy.context.active_node
            node.inputs[0].default_value = self.cutter_type.capitalize()
            node.inputs[1].default_value = cutter_obj

        return {'FINISHED'}


class AddPlaneCutter(bpy.types.Operator, AddCutter):
    bl_idname = "bioxelnodes.add_plane_cutter"
    bl_label = "Add a Plane Cutter"
    bl_description = "Add a plane cutter to current container"
    bl_icon = "MESH_PLANE"
    cutter_type = "plane"


class AddCylinderCutter(bpy.types.Operator, AddCutter):
    bl_idname = "bioxelnodes.add_cylinder_cutter"
    bl_label = "Add a Cylinder Cutter"
    bl_description = "Add a cylinder cutter to current container"
    bl_icon = "MESH_CYLINDER"
    cutter_type = "cylinder"


class AddCubeCutter(bpy.types.Operator, AddCutter):
    bl_idname = "bioxelnodes.add_cube_cutter"
    bl_label = "Add a Cube Cutter"
    bl_description = "Add a cube cutter to current container"
    bl_icon = "MESH_CUBE"
    cutter_type = "cube"


class AddSphereCutter(bpy.types.Operator, AddCutter):
    bl_idname = "bioxelnodes.add_sphere_cutter"
    bl_label = "Add a Sphere Cutter"
    bl_description = "Add a sphere cutter to current container"
    bl_icon = "MESH_UVSPHERE"
    cutter_type = "sphere"


class AddPieCutter(bpy.types.Operator, AddCutter):
    bl_idname = "bioxelnodes.add_pie_cutter"
    bl_label = "Add a Pie Cutter"
    bl_description = "Add a pie cutter to current container"
    bl_icon = "MESH_CONE"
    cutter_type = "pie"


class AddSlicer(bpy.types.Operator):
    bl_idname = "bioxelnodes.add_slicer"
    bl_label = "Add a Slicer"
    bl_description = "Add a slicer to current container"
    bl_icon = "TEXTURE"
    bl_options = {'UNDO'}

    def execute(self, context):
        container_obj = get_container_obj(context.object)

        if container_obj is None:
            self.report({"WARNING"}, "Cannot find any bioxel container.")
            return {'FINISHED'}

        bpy.ops.mesh.primitive_plane_add(size=2,
                                         enter_editmode=False,
                                         align='WORLD',
                                         location=(0, 0, 0),
                                         scale=(1, 1, 1))

        slicer_obj = bpy.context.active_object
        slicer_obj.name = "Slicer"
        slicer_obj.data.name = "Slicer"

        slicer_obj.visible_camera = False
        slicer_obj.visible_diffuse = False
        slicer_obj.visible_glossy = False
        slicer_obj.visible_transmission = False
        slicer_obj.visible_volume_scatter = False
        slicer_obj.visible_shadow = False
        slicer_obj.hide_render = True
        slicer_obj.display_type = 'WIRE'
        slicer_obj.lineart.usage = 'EXCLUDE'

        select_object(container_obj)

        modifier = container_obj.modifiers[0]
        node_group = modifier.node_group

        slice_node = add_node_to_graph("Slice",
                                       node_group,
                                       use_link=get_use_link())

        slice_node.inputs[1].default_value = slicer_obj

        output_node = get_output_node(node_group)

        if len(output_node.inputs[0].links) == 0:
            node_group.links.new(slice_node.outputs[0],
                                 output_node.inputs[0])
            move_node_to_node(slice_node, output_node, (-300, 0))
        else:
            pre_output_node = output_node.inputs[0].links[0].from_node
            node_group.links.new(pre_output_node.outputs[0],
                                 slice_node.inputs[0])
            node_group.links.new(slice_node.outputs[0],
                                 output_node.inputs[0])
            move_node_between_nodes(slice_node,
                                    [pre_output_node, output_node])

        return {'FINISHED'}


class AddLocator(bpy.types.Operator):
    bl_idname = "bioxelnodes.add_locator"
    bl_label = "Add a Locator"
    bl_description = "Add a locator to current container"
    bl_icon = "EMPTY_AXIS"
    bl_options = {'UNDO'}

    def execute(self, context):
        container_obj = get_container_obj(context.object)

        if container_obj is None:
            self.report({"WARNING"}, "Cannot find any bioxel container.")
            return {'FINISHED'}

        bpy.ops.object.empty_add(type='ARROWS',
                                 align='WORLD',
                                 location=(0, 0, 0),
                                 scale=(1, 1, 1))

        locator_obj = bpy.context.active_object
        locator_obj.name = "Locator"
        select_object(container_obj)

        modifier = container_obj.modifiers[0]
        node_group = modifier.node_group

        parent_node = add_node_to_graph("TransformParent",
                                        node_group,
                                        node_label="Transform Parent",
                                        use_link=get_use_link())

        parent_node.inputs[1].default_value = locator_obj

        output_node = get_output_node(node_group)

        if len(output_node.inputs[0].links) == 0:
            node_group.links.new(parent_node.outputs[0],
                                 output_node.inputs[0])
            move_node_to_node(parent_node, output_node, (-300, 0))
        else:
            pre_output_node = output_node.inputs[0].links[0].from_node
            node_group.links.new(pre_output_node.outputs[0],
                                 parent_node.inputs[0])
            node_group.links.new(parent_node.outputs[0],
                                 output_node.inputs[0])
            move_node_between_nodes(parent_node,
                                    [pre_output_node, output_node])

        return {'FINISHED'}


class ContainerProps(bpy.types.Operator):
    bl_idname = "bioxelnodes.container_props"
    bl_label = "Change Container Properties"
    bl_description = "Change current ontainer properties"
    bl_icon = "FILE_TICK"
    bl_options = {'UNDO'}

    scene_scale: bpy.props.FloatProperty(name="Scene Scale",
                                         soft_min=0.0001, soft_max=10.0,
                                         min=1e-6, max=1e6,
                                         default=0.01)  # type: ignore

    step_size: bpy.props.FloatProperty(name="Step Size",
                                       soft_min=0.1, soft_max=100.0,
                                       min=0.1, max=1e2,
                                       default=1)  # type: ignore

    def execute(self, context):
        container_obj = get_container_obj(context.object)

        if container_obj is None:
            self.report({"WARNING"}, "Cannot find any bioxel container.")
            return {'FINISHED'}

        container_obj.scale[0] = self.scene_scale
        container_obj.scale[1] = self.scene_scale
        container_obj.scale[2] = self.scene_scale
        container_obj["scene_scale"] = self.scene_scale
        container_obj["step_size"] = self.step_size

        for layer_obj in get_container_layer_objs(container_obj):
            layer_obj.data.render.space = 'WORLD'
            layer_obj.data.render.step_size = self.scene_scale * self.step_size

        return {'FINISHED'}

    def invoke(self, context, event):
        container_obj = get_container_obj(context.object)

        if container_obj is None:
            return self.execute(context)
        else:
            self.scene_scale = container_obj.get("scene_scale") or 0.01
            self.step_size = container_obj.get("step_size") or 1
            context.window_manager.invoke_props_dialog(self)
            return {'RUNNING_MODAL'}


def get_container_layers(context, layer_filter=None):
    def _layer_filter(layer_obj, context):
        return True

    layer_filter = layer_filter or _layer_filter
    container_obj = context.object
    layer_objs = get_container_layer_objs(container_obj)
    return [obj for obj in layer_objs if layer_filter(obj, context)]


class SaveContainerLayersCache(bpy.types.Operator, SaveLayersCache):
    bl_idname = "bioxelnodes.save_container_layers_cache"
    bl_label = "Save Container Layers' Cache"
    bl_description = "Save all current container layers' cache to directory."
    bl_icon = "FILE_TICK"

    success_msg = "Successfully saved all container layers."

    def get_layers(self, context):
        def is_not_missing(layer_obj, context):
            return not is_missing_layer(layer_obj)
        return get_container_layers(context, is_not_missing)


class RemoveContainerMissingLayers(bpy.types.Operator, RemoveLayers):
    bl_idname = "bioxelnodes.remove_container_missing_layers"
    bl_label = "Remove Container Missing Layers"
    bl_description = "Remove all current container missing layers"
    bl_icon = "BRUSH_DATA"

    success_msg = "Successfully removed all container missing layers."

    def get_layers(self, context):
        def is_missing(layer_obj, context):
            return is_missing_layer(layer_obj)
        return get_container_layers(context, is_missing)

    def invoke(self, context, event):
        context.window_manager.invoke_confirm(self,
                                              event,
                                              message=f"Are you sure to remove all **Missing** layers?")
        return {'RUNNING_MODAL'}
