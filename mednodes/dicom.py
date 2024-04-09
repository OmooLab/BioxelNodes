import bpy
from bpy_extras.io_utils import axis_conversion, ImportHelper
import pyopenvdb as vdb
import numpy as np
from pathlib import Path
from uuid import uuid4
import mathutils
from .nodes import custom_nodes


class ImportDICOM(bpy.types.Operator, ImportHelper):
    bl_idname = "mednodes.import_dicom"
    bl_label = "DICOM as VDB (.dcm)"
    bl_description = "Load DICOM as VDB"
    bl_options = {'UNDO'}

    filepath: bpy.props.StringProperty(
        subtype="FILE_PATH"
    )  # type: ignore

    global_scale: bpy.props.FloatProperty(
        name="Scale",
        soft_min=0.001, soft_max=100.0,
        min=1e-6, max=1e6,
        default=0.01,
    )  # type: ignore

    do_resample: bpy.props.BoolProperty(
        name="Uniform Spacing (Resample)",
        default=True,
    )  # type: ignore

    do_change_render_setting: bpy.props.BoolProperty(
        name="Change Render Setting",
        default=True,
    )  # type: ignore

    def execute(self, context):
        import SimpleITK as sitk

        preferences = context.preferences.addons[__package__].preferences

        file_path: Path = Path(self.filepath).resolve()
        name = file_path.parent.stem

        reader = sitk.ImageSeriesReader()
        dicom_names = reader.GetGDCMSeriesFileNames(
            file_path.parent.as_posix())
        reader.SetFileNames(dicom_names)
        image = reader.Execute()

        print("Spacing:", image.GetSpacing())
        print("Origin:", image.GetOrigin())
        print("Direction:", image.GetDirection())

        image = sitk.DICOMOrient(image, 'LPS')

        size = image.GetSize()
        spacing = image.GetSpacing()
        origin = image.GetOrigin()
        direction = image.GetDirection()

        print("Size:", size)
        print("Spacing:", spacing)
        print("Origin:", origin)
        print("Direction:", direction)

        if self.do_resample:
            resampled_spacing = (1, 1, 1)
            resampled_size = (
                int(size[0]*spacing[0]),
                int(size[1]*spacing[1]),
                int(size[2]*spacing[2]),
            )

            print("Resampling...")
            image = sitk.Resample(
                image1=image,
                size=resampled_size,
                transform=sitk.Transform(),
                interpolator=sitk.sitkLinear,
                outputOrigin=origin,
                outputSpacing=resampled_spacing,
                outputDirection=direction,
                defaultPixelValue=0,
                outputPixelType=image.GetPixelID(),
            )
            print("Resampled Size:", resampled_size)

            spacing = resampled_spacing
            size = resampled_size

        array = sitk.GetArrayFromImage(image)

        # ITK indices, by convention, are [i,j,k] while NumPy indices are [k,j,i]
        # https://www.slicer.org/wiki/Coordinate_systems

        # ITK                  Numpy      3D
        # L (eft)      i   ->    k   ->   x
        # P (osterior) j   ->    j   ->   y
        # S (uperior)  k   ->    i   ->   z

        array = np.transpose(array)
        value_max = float(np.max(array))
        value_min = float(np.min(array))

        value_offset = 0.0
        if value_min < 0:
            value_offset = -value_min
            array = array + np.full_like(array, value_offset)
            value_max = float(np.max(array))
            value_min = float(np.min(array))
            print("offset max value:", value_max)
            print("offset min value:", value_min)

        # Build VDB
        grid = vdb.FloatGrid()
        grid.copyFromArray(array.copy())
        grid.name = "density"

        vdb_dirpath = Path(preferences.cache_dir, 'VDBs')
        vdb_dirpath.mkdir(parents=True, exist_ok=True)
        vdb_path = Path(vdb_dirpath, f"{uuid4()}.vdb")
        vdb.write(vdb_path.as_posix(), grids=[grid])

        # Read VDB
        bpy.ops.object.volume_import(
            filepath=vdb_path.as_posix(), align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))

        vdb_obj = bpy.context.active_object

        # Set props to VDB object
        vdb_obj.name = name
        vdb_obj.data.name = name

        vdb_obj['value_max'] = value_max
        vdb_obj['value_min'] = value_min
        vdb_obj['value_offset'] = value_offset

        vdb_obj['size'] = size
        vdb_obj['spacing'] = spacing
        vdb_obj['origin'] = origin

        # Make transformation
        
        # (S)uperior  -Z -> Y
        # (P)osterior -Y -> Z
        axis_rot = axis_conversion(
            from_forward='-Z',
            from_up='-Y',
            to_forward='Y',
            to_up='Z'
        ).to_4x4()

        mat_loc = mathutils.Matrix.Translation(
            mathutils.Vector(origin) * self.global_scale)
        mat_sca = mathutils.Matrix.Scale(self.global_scale, 4)
        mat_rot = mathutils.Matrix(
            np.array(direction).reshape((3, 3))
        ).to_4x4()

        vdb_obj.matrix_world = axis_rot @ mat_loc @ mat_rot @ mat_sca

        # Wrapper a Locator
        bpy.ops.object.empty_add(
            type='PLAIN_AXES',
            align='WORLD',
            location=(0, 0, 0),
            scale=(1, 1, 1)
        )
        loc_obj = bpy.context.active_object
        loc_obj.name = f"LOC_{name}"
        vdb_obj.parent = loc_obj

        # Create MedNodes to VDB object
        bpy.context.view_layer.objects.active = vdb_obj
        bpy.ops.node.new_geometry_nodes_modifier()
        modifier = vdb_obj.modifiers[0]
        nodes = modifier.node_group.nodes
        links = modifier.node_group.links

        input_node = nodes.get("Group Input")
        output_node = nodes.get("Group Output")
        segment_node = custom_nodes.add_node(nodes, 'MedNodes_Segment')

        links.new(input_node.outputs[0], segment_node.inputs[0])
        links.new(segment_node.outputs[0], output_node.inputs[0])

        # Change render setting for better result
        if self.do_change_render_setting:
            bpy.context.scene.render.engine = 'CYCLES'
            bpy.context.scene.cycles.volume_bounces = 12
            bpy.context.scene.cycles.transparent_max_bounces = 64

        return {'FINISHED'}


def MEDNODES_add_topbar_menu(self, context):
    layout = self.layout
    layout.operator(ImportDICOM.bl_idname)
