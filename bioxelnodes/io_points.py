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


# class ImportDICOMPointsDialog(bpy.types.Operator):
#     bl_idname = "bioxelnodes.import_dicom_points_dialog"
#     bl_label = "Volume Data as Bioxels"
#     bl_description = "Import Volume Data as Bioxels (VDB)"
#     bl_options = {'UNDO'}

#     filepath: bpy.props.StringProperty(
#         subtype="FILE_PATH",
#         options={'HIDDEN'}
#     )  # type: ignore

#     bioxels_shape: bpy.props.IntVectorProperty(
#         name="Bioxels Shape (ReadOnly)",
#         min=0,
#         default=(100, 100, 100)
#     )  # type: ignore

#     bioxel_size: bpy.props.FloatProperty(
#         name="Bioxel Size",
#         soft_min=0.1, soft_max=10.0,
#         min=1e-2, max=1e2,
#         default=1,
#         update=on_bioxel_size_changed
#     )  # type: ignore

#     orig_spacing: bpy.props.FloatVectorProperty(
#         name="Original Spacing",
#         default=(1, 1, 1),
#         update=on_orig_spacing_changed
#     )  # type: ignore

#     orig_shape: bpy.props.IntVectorProperty(
#         name="Original Shape",
#         default=(100, 100, 100),
#         options={'HIDDEN'}
#     )  # type: ignore

#     auto: bpy.props.BoolProperty(
#         name="Auto Setting",
#         default=False,
#         options={'HIDDEN'}
#     )  # type: ignore

#     scene_scale: bpy.props.FloatProperty(
#         name="Scene Scale",
#         soft_min=0.001, soft_max=100.0,
#         min=1e-6, max=1e6,
#         default=0.01,
#     )  # type: ignore

#     do_add_segmentnode: bpy.props.BoolProperty(
#         name="Add Segment Node",
#         default=True,
#     )  # type: ignore

#     do_change_render_setting: bpy.props.BoolProperty(
#         name="Change Render Setting",
#         default=True,
#     )  # type: ignore

#     def execute(self, context):
#         files = get_data_files(self.filepath)
#         name = Path(self.filepath).parent.name

#         image = sitk.ReadImage(files)

#         bioxel_size = float(self.bioxel_size)
#         orig_spacing = tuple(self.orig_spacing)
#         image_spacing = image.GetSpacing()
#         image_shape = image.GetSize()

#         bioxels_spacing = (
#             image_spacing[0] / orig_spacing[0] * bioxel_size,
#             image_spacing[1] / orig_spacing[1] * bioxel_size,
#             image_spacing[2] / orig_spacing[2] * bioxel_size
#         )

#         bioxels_shape = (
#             int(image_shape[0] / bioxel_size * orig_spacing[0]),
#             int(image_shape[1] / bioxel_size * orig_spacing[1]),
#             int(image_shape[2] / bioxel_size * orig_spacing[2]),
#         )

#         print("Resampling...")
#         image = sitk.Resample(
#             image1=image,
#             size=bioxels_shape,
#             transform=sitk.Transform(),
#             interpolator=sitk.sitkLinear,
#             outputOrigin=image.GetOrigin(),
#             outputSpacing=bioxels_spacing,
#             outputDirection=image.GetDirection(),
#             defaultPixelValue=0,
#             outputPixelType=image.GetPixelID(),
#         )

#         print("Orienting to RAS...")
#         image = sitk.DICOMOrient(image, 'RAS')

#         array = sitk.GetArrayFromImage(image)
#         orig_dtype = str(array.dtype)
#         print(f"Coverting Dtype from {orig_dtype} to float...")
#         array = array.astype(float)

#         # ITK indices, by convention, are [i,j,k] while NumPy indices are [k,j,i]
#         # https://www.slicer.org/wiki/Coordinate_systems

#         # ITK                  Numpy      3D
#         # R (ight)     i   ->    k   ->   x
#         # A (nterior)  j   ->    j   ->   y
#         # S (uperior)  k   ->    i   ->   z

#         array = np.transpose(array)
#         bioxels_max = float(np.max(array))
#         bioxels_min = float(np.min(array))
#         bioxels_shape = array.shape

#         print("Bioxel Size:", bioxel_size)
#         print("Bioxels Shape:", bioxels_shape)

#         bioxels_offset = 0.0
#         if bioxels_min < 0 and orig_dtype[0] != "u":
#             bioxels_offset = -bioxels_min
#             array = array + np.full_like(array, bioxels_offset)
#             bioxels_max = float(np.max(array))
#             bioxels_min = float(np.min(array))
#             print("Offseted Max:", bioxels_max)
#             print("Offseted Min:", bioxels_min)

#         points = []
#         for x in range(array.shape[0]):
#             for y in range(array.shape[1]):
#                 for z in range(array.shape[2]):
#                     points.append({
#                         "pos": (x, y, z),
#                         "value": array[x, y, z],
#                     })

#         # # Build VDB
#         # grid = vdb.FloatGrid()
#         # grid.copyFromArray(array.copy())

#         # # After sitk.DICOMOrient(), origin and direction will also orient base on LPS
#         # # so we need to convert them into RAS
#         # mat_lps2ras = axis_conversion(
#         #     from_forward='-Z',
#         #     from_up='-Y',
#         #     to_forward='-Z',
#         #     to_up='Y'
#         # ).to_4x4()

#         # mat_location = mathutils.Matrix.Translation(
#         #     mathutils.Vector(image.GetOrigin())
#         # )

#         # mat_rotation = mathutils.Matrix(
#         #     np.array(image.GetDirection()).reshape((3, 3))
#         # ).to_4x4()

#         # mat_scale = mathutils.Matrix.Scale(
#         #     bioxel_size, 4
#         # )

#         # transfrom = mat_lps2ras @ mat_location @ mat_rotation @ mat_scale

#         obj = create_points_obj(points)

#         # Make transformation
#         scene_scale = float(self.scene_scale)
#         # (S)uperior  -Z -> Y
#         # (A)osterior  Y -> Z
#         mat_ras2blender = axis_conversion(
#             from_forward='-Z',
#             from_up='Y',
#             to_forward='Y',
#             to_up='Z'
#         ).to_4x4()

#         mat_scene_scale = mathutils.Matrix.Scale(
#             scene_scale, 4
#         )

#         obj.matrix_world = mat_ras2blender @ mat_scene_scale

#         self.report({"INFO"}, "Successfully Imported")

#         return {'FINISHED'}

#     def invoke(self, context, event):
#         # print(tuple(self.orig_shape))
#         self.auto = True
#         self.bioxel_size = 1
#         context.window_manager.invoke_props_dialog(self)
#         return {'RUNNING_MODAL'}
