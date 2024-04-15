import bpy
from .utils import get_bioxels_obj


class ConvertToMesh(bpy.types.Operator):
    bl_idname = "bioxelnodes.convert_to_mesh"
    bl_label = "Bioxels To Mesh"
    bl_description = "Convert Bioxels To Mesh."
    bl_options = {'UNDO'}

    def execute(self, context):
        bioxels_objs = []
        for obj in bpy.context.selected_objects:
            bioxels_obj = get_bioxels_obj(obj)
            if bioxels_obj:
                bioxels_objs.append(bioxels_obj)

        if len(bioxels_objs)==0:
            self.report({"WARNING"}, "Cannot find any bioxels.")
            return {'FINISHED'}

        for bioxels_obj in bioxels_objs:
            bpy.ops.mesh.primitive_cube_add(
                size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
            mesh_obj = bpy.context.active_object

            mesh_obj.name = f"{bioxels_obj.parent.name}_Mesh"
            bpy.ops.node.new_geometry_nodes_modifier()
            modifier = mesh_obj.modifiers[0]
            nodes = modifier.node_group.nodes
            links = modifier.node_group.links

            output_node = nodes.get("Group Output")
            object_node = nodes.new("GeometryNodeObjectInfo")
            realize_nodes = nodes.new("GeometryNodeRealizeInstances")
            object_node.inputs[0].default_value = bioxels_obj
            object_node.transform_space = 'RELATIVE'

            links.new(object_node.outputs['Geometry'], realize_nodes.inputs[0])
            links.new(realize_nodes.outputs[0], output_node.inputs[0])
            bpy.ops.object.convert(target='MESH')
            bpy.context.object.active_material_index = 1
            bpy.ops.object.material_slot_remove()

        return {'FINISHED'}
