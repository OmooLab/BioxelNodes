import bpy

import bmesh

from ..nodes import custom_nodes
from ..bioxel.io import load_container, save_container
from ..bioxelutils.container import (container_to_obj, obj_to_container,
                                     get_container_objs_from_selection)
from ..bioxelutils.node import get_nodes_by_type, move_node_between_nodes, move_node_to_node
from .utils import get_cache_dir, select_object


class SaveContainer(bpy.types.Operator):
    bl_idname = "bioxelnodes.save_container"
    bl_label = "Save Container (.bioxel) (BETA)"
    bl_description = "Clean all caches saved in temp"

    filepath: bpy.props.StringProperty(
        subtype="FILE_PATH"
    )  # type: ignore

    filename_ext = ".bioxel"

    @classmethod
    def poll(cls, context):
        container_objs = get_container_objs_from_selection()
        return len(container_objs) > 0

    def execute(self, context):
        container_objs = get_container_objs_from_selection()

        if len(container_objs) == 0:
            self.report({"WARNING"}, "Cannot find any bioxel container.")
            return {'FINISHED'}

        container = obj_to_container(container_objs[0])
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
        container_obj = container_to_obj(container,
                                         scene_scale=0.01,
                                         cache_dir=get_cache_dir(context))
        select_object(container_obj)

        self.report({"INFO"}, f"Successfully load {load_path}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class PickObject():
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        container_objs = get_container_objs_from_selection()
        return len(container_objs) > 0

    def execute(self, context):
        container_objs = get_container_objs_from_selection()

        if len(container_objs) == 0:
            self.report({"WARNING"}, "Cannot find any bioxel container.")
            return {'FINISHED'}

        container_obj = container_objs[0]

        bpy.ops.mesh.primitive_cube_add(
            size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        obj = bpy.context.active_object

        obj.name = f"{self.object_type}_{container_obj.name}"

        bpy.ops.node.new_geometry_nodes_modifier()
        modifier = obj.modifiers[0]
        node_group = modifier.node_group

        output_node = get_nodes_by_type(node_group, 'NodeGroupOutput')[0]
        pick_mesh_node = custom_nodes.add_node(node_group,
                                               f"BioxelNodes_Pick{self.object_type}")

        pick_mesh_node.inputs[0].default_value = container_obj
        node_group.links.new(pick_mesh_node.outputs[0], output_node.inputs[0])

        select_object(obj)

        self.report({"INFO"}, f"Successfully picked")

        return {'FINISHED'}


class PickMesh(bpy.types.Operator, PickObject):
    bl_idname = "bioxelnodes.pick_mesh"
    bl_label = "Pick Mesh"
    bl_description = "Pick Container Mesh"
    object_type = "Mesh"


class PickVolume(bpy.types.Operator, PickObject):
    bl_idname = "bioxelnodes.pick_volume"
    bl_label = "Pick Volume"
    bl_description = "Pick Container Volume"
    object_type = "Volume"


class PickBboxWire(bpy.types.Operator, PickObject):
    bl_idname = "bioxelnodes.pick_bbox_wire"
    bl_label = "Pick Bbox Wire"
    bl_description = "Pick Container Bbox Wire"
    object_type = "BboxWire"


class AddCutter():
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        container_objs = get_container_objs_from_selection()
        return len(container_objs) > 0

    def execute(self, context):
        container_objs = get_container_objs_from_selection()

        if len(container_objs) == 0:
            self.report({"WARNING"}, "Cannot find any bioxel container.")
            return {'FINISHED'}

        container_obj = container_objs[0]

        if self.object_type == "plane":
            node_type = "BioxelNodes_PlaneObjectCutter"
            bpy.ops.mesh.primitive_plane_add(
                size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        elif self.object_type == "cylinder":
            node_type = "BioxelNodes_CylinderObjectCutter"
            bpy.ops.mesh.primitive_cylinder_add(
                radius=1, depth=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
            bpy.context.object.rotation_euler[0] = container_obj.rotation_euler[0]
        elif self.object_type == "cube":
            node_type = "BioxelNodes_CubeObjectCutter"
            bpy.ops.mesh.primitive_cube_add(
                size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        elif self.object_type == "sphere":
            node_type = "BioxelNodes_SphereObjectCutter"
            bpy.ops.mesh.primitive_ico_sphere_add(
                radius=1, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        elif self.object_type == "pie":
            node_type = "BioxelNodes_PieObjectCutter"
            # Create mesh
            pie_mesh = bpy.data.meshes.new('Pie')

            # Create object
            pie = bpy.data.objects.new('Pie', pie_mesh)

            # Link object to scene
            bpy.context.scene.collection.objects.link(pie)
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
            bpy.context.view_layer.objects.active = pie

        cutter_obj = bpy.context.active_object
        cutter_obj.visible_camera = False
        cutter_obj.visible_diffuse = False
        cutter_obj.visible_glossy = False
        cutter_obj.visible_transmission = False
        cutter_obj.visible_volume_scatter = False
        cutter_obj.visible_shadow = False
        cutter_obj.hide_render = True
        cutter_obj.display_type = 'WIRE'

        modifier = container_obj.modifiers[0]
        node_group = modifier.node_group
        cutter_node = custom_nodes.add_node(node_group, node_type)
        cutter_node.inputs[0].default_value = cutter_obj

        cut_nodes = get_nodes_by_type(node_group,
                                      'BioxelNodes_Cut')
        output_node = get_nodes_by_type(node_group, 'NodeGroupOutput')[0]
        if len(cut_nodes) == 0:
            cut_node = custom_nodes.add_node(node_group, 'BioxelNodes_Cut')
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
            select_object(cutter_obj)
        else:
            move_node_to_node(cutter_node, output_node, (0, -100))
            select_object(container_obj)

        return {'FINISHED'}


class AddPlaneCutter(bpy.types.Operator, AddCutter):
    bl_idname = "bioxelnodes.add_plane_cutter"
    bl_label = "Add a Plane Cutter"
    bl_description = "Add a Plane Cutter to Container"
    object_type = "plane"


class AddCylinderCutter(bpy.types.Operator, AddCutter):
    bl_idname = "bioxelnodes.add_cylinder_cutter"
    bl_label = "Add a Cylinder Cutter"
    bl_description = "Add a Cylinder Cutter to Container"
    object_type = "cylinder"


class AddCubeCutter(bpy.types.Operator, AddCutter):
    bl_idname = "bioxelnodes.add_cube_cutter"
    bl_label = "Add a Cube Cutter"
    bl_description = "Add a Cube Cutter to Container"
    object_type = "cube"


class AddSphereCutter(bpy.types.Operator, AddCutter):
    bl_idname = "bioxelnodes.add_sphere_cutter"
    bl_label = "Add a Sphere Cutter"
    bl_description = "Add a Sphere Cutter to Container"
    object_type = "sphere"


class AddPieCutter(bpy.types.Operator, AddCutter):
    bl_idname = "bioxelnodes.add_pie_cutter"
    bl_label = "Add a Pie Cutter"
    bl_description = "Add a Pie Cutter to Container"
    object_type = "pie"
