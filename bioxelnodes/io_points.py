# TODO: WIP
import bpy
import bmesh


def create_points_obj(points, name="points"):
    bpy.ops.mesh.primitive_cube_add(
        enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1)
    )
    obj = bpy.context.active_object
    mesh = obj.data

    bm = bmesh.new()
    value_layer = bm.verts.layers.float.new('value')

    for point in points:
        pos = point['pos']
        value = point['value']
        vert = bm.verts.new(pos)  # add a new vert
        vert[value_layer] = value

    # make the bmesh the object's mesh
    bm.to_mesh(mesh)
    bm.free()  # always do this when finished
    return obj