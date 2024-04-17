import bpy
import shutil
from bpy_extras.io_utils import axis_conversion
import pyopenvdb as vdb
import numpy as np
from pathlib import Path
from uuid import uuid4
import mathutils
from .utils import calc_bbox_verts, extract_last_number, get_bioxels_obj, show_message
from .nodes import custom_nodes

SUPPORT_EXTS = ['.dcm', '.tif', '.tiff', '.png', '.bmp', '', '.jpg']


def get_data_files(filepath: str):
    file_path = Path(filepath).resolve()
    suffix = file_path.suffix

    files = list(file_path.parent.iterdir())
    files = [f for f in files if f.is_file() and f.suffix == suffix]

    def last_number(file: Path):
        return extract_last_number(file.stem)

    files.sort(key=last_number)
    files = [f.as_posix() for f in files]
    return files


def on_orig_spacing_changed(self, context):
    if self.auto:
        self.auto = False
        new_orig_spacing = tuple(self.orig_spacing)

        orig_shape = tuple(self.orig_shape)
        bioxel_size = float(self.bioxel_size)

        self.bioxels_shape = (
            int(orig_shape[0] / bioxel_size * new_orig_spacing[0]),
            int(orig_shape[1] / bioxel_size * new_orig_spacing[1]),
            int(orig_shape[2] / bioxel_size * new_orig_spacing[2]),
        )
    else:
        self.auto = True


def on_bioxel_size_changed(self, context):
    if self.auto:
        self.auto = False
        new_bioxel_size = float(self.bioxel_size)

        orig_shape = tuple(self.orig_shape)
        orig_spacing = tuple(self.orig_spacing)

        self.bioxels_shape = (
            int(orig_shape[0] / new_bioxel_size * orig_spacing[0]),
            int(orig_shape[1] / new_bioxel_size * orig_spacing[1]),
            int(orig_shape[2] / new_bioxel_size * orig_spacing[2]),
        )
    else:
        self.auto = True


def on_info_changed(self, context):
    for region in context.area.regions:
        if region.type == "UI":
            region.tag_redraw()


class ImportDICOMDialog(bpy.types.Operator):
    bl_idname = "bioxelnodes.import_dicom_dialog"
    bl_label = "Volume Data as Biovels"
    bl_description = "Import Volume Data as Biovels (VDB)."
    bl_options = {'UNDO'}

    filepath: bpy.props.StringProperty(
        subtype="FILE_PATH",
        options={'HIDDEN'}
    )  # type: ignore

    bioxels_shape: bpy.props.IntVectorProperty(
        name="Bioxels Shape",
        min=0,
        default=(100, 100, 100)
    )  # type: ignore

    bioxel_size: bpy.props.FloatProperty(
        name="Bioxel Size",
        soft_min=0.1, soft_max=10.0,
        min=1e-2, max=1e2,
        default=1,
        update=on_bioxel_size_changed
    )  # type: ignore

    orig_spacing: bpy.props.FloatVectorProperty(
        name="Original Spacing",
        default=(1, 1, 1),
        update=on_orig_spacing_changed
    )  # type: ignore

    orig_shape: bpy.props.IntVectorProperty(
        name="Original Shape",
        default=(100, 100, 100),
        options={'HIDDEN'}
    )  # type: ignore

    auto: bpy.props.BoolProperty(
        name="Auto Setting",
        default=False,
        options={'HIDDEN'}
    )  # type: ignore

    scene_scale: bpy.props.FloatProperty(
        name="Scene Scale",
        soft_min=0.001, soft_max=100.0,
        min=1e-6, max=1e6,
        default=0.01,
    )  # type: ignore

    do_add_segmentnode: bpy.props.BoolProperty(
        name="Add Segment Node",
        default=True,
    )  # type: ignore

    do_change_render_setting: bpy.props.BoolProperty(
        name="Change Render Setting",
        default=True,
    )  # type: ignore

    def execute(self, context):
        if not self.filepath:
            self.report({"WARNING"}, "Get no file path.")
            return {'CANCELLED'}

        if Path(self.filepath).suffix not in SUPPORT_EXTS:
            self.report({"WARNING"}, "Not Supported extension.")
            return {'CANCELLED'}

        file_path = Path(self.filepath).resolve()
        name = file_path.parent.name
        files = get_data_files(self.filepath)

        import SimpleITK as sitk
        image = sitk.ReadImage(files)

        bioxel_size = float(self.bioxel_size)

        orig_spacing = tuple(self.orig_spacing)
        image_spacing = image.GetSpacing()
        image_shape = image.GetSize()

        bioxels_spacing = (
            image_spacing[0] / orig_spacing[0] * bioxel_size,
            image_spacing[1] / orig_spacing[1] * bioxel_size,
            image_spacing[2] / orig_spacing[2] * bioxel_size
        )

        bioxels_shape = (
            int(image_shape[0] / bioxel_size * orig_spacing[0]),
            int(image_shape[1] / bioxel_size * orig_spacing[1]),
            int(image_shape[2] / bioxel_size * orig_spacing[2]),
        )

        print("Bioxel Size:", bioxel_size)
        print("Bioxels Shape:", bioxels_shape)

        print("Resampling...")
        image = sitk.Resample(
            image1=image,
            size=bioxels_shape,
            transform=sitk.Transform(),
            interpolator=sitk.sitkLinear,
            outputOrigin=image.GetOrigin(),
            outputSpacing=bioxels_spacing,
            outputDirection=image.GetDirection(),
            defaultPixelValue=0,
            outputPixelType=image.GetPixelID(),
        )

        try:
            image = sitk.DICOMOrient(image, 'RAS')
        except:
            ...

        array = sitk.GetArrayFromImage(image)
        orig_dtype = str(array.dtype)
        print(f"Coverting Dtype {orig_dtype} -> float")
        array = array.astype(float)

        # ITK indices, by convention, are [i,j,k] while NumPy indices are [k,j,i]
        # https://www.slicer.org/wiki/Coordinate_systems

        # ITK                  Numpy      3D
        # R (ight)     i   ->    k   ->   x
        # A (nterior)  j   ->    j   ->   y
        # S (uperior)  k   ->    i   ->   z

        array = np.transpose(array)
        bioxels_max = float(np.max(array))
        bioxels_min = float(np.min(array))

        bioxels_offset = 0.0
        if bioxels_min < 0 and orig_dtype[0] != "u":
            bioxels_offset = -bioxels_min
            array = array + np.full_like(array, bioxels_offset)
            bioxels_max = float(np.max(array))
            bioxels_min = float(np.min(array))
            print("Offseted Max:", bioxels_max)
            print("Offseted Min:", bioxels_min)

        # Build VDB
        grid = vdb.FloatGrid()
        grid.copyFromArray(array.copy())

        # After sitk.DICOMOrient(), origin and direction will also orient base on LPS
        # so we need to convert them into RAS
        mat_lps2ras = axis_conversion(
            from_forward='-Z',
            from_up='-Y',
            to_forward='-Z',
            to_up='Y'
        ).to_4x4()

        mat_location = mathutils.Matrix.Translation(
            mathutils.Vector(image.GetOrigin())
        )

        mat_rotation = mathutils.Matrix(
            np.array(image.GetDirection()).reshape((3, 3))
        ).to_4x4()

        mat_scale = mathutils.Matrix.Scale(
            bioxel_size, 4
        )

        transfrom = mat_lps2ras @ mat_location @ mat_rotation @ mat_scale

        grid.transform = vdb.createLinearTransform(transfrom.transposed())
        grid.name = "value"

        preferences = context.preferences.addons[__package__].preferences
        vdb_dirpath = Path(preferences.cache_dir, 'VDBs')
        vdb_dirpath.mkdir(parents=True, exist_ok=True)
        vdb_path = Path(vdb_dirpath, f"{uuid4()}.vdb")

        print(f"Storing the VDB file ({vdb_path.as_posix()})...")
        vdb.write(vdb_path.as_posix(), grids=[grid])

        # Read VDB
        print(f"Importing the VDB file to Blender scene...")
        bpy.ops.object.volume_import(
            filepath=vdb_path.as_posix(), align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))

        bioxels_obj = bpy.context.active_object

        # Set props to VDB object
        bioxels_obj.name = f"{name}_Bioxels"
        bioxels_obj.data.name = f"{name}_Bioxels"

        # Make transformation
        scene_scale = float(self.scene_scale)

        # (S)uperior  -Z -> Y
        # (A)osterior  Y -> Z
        mat_ras2blender = axis_conversion(
            from_forward='-Z',
            from_up='Y',
            to_forward='Y',
            to_up='Z'
        ).to_4x4()

        mat_scene_scale = mathutils.Matrix.Scale(
            scene_scale, 4
        )

        bioxels_obj.matrix_world = mat_ras2blender @ mat_scene_scale

        bioxels_obj.lock_location[0] = True
        bioxels_obj.lock_location[1] = True
        bioxels_obj.lock_location[2] = True
        bioxels_obj.lock_rotation[0] = True
        bioxels_obj.lock_rotation[1] = True
        bioxels_obj.lock_rotation[2] = True
        bioxels_obj.lock_scale[0] = True
        bioxels_obj.lock_scale[1] = True
        bioxels_obj.lock_scale[2] = True
        bioxels_obj.hide_select = True
        bioxels_obj['bioxels'] = True

        bpy.ops.node.new_geometry_nodes_modifier()
        node_tree = bioxels_obj.modifiers[0].node_group

        # Wrapper a Container
        bpy.ops.mesh.primitive_cube_add(
            enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1)
        )
        container_obj = bpy.context.active_object
        bbox_verts = calc_bbox_verts((0, 0, 0), bioxels_shape)
        for index, vert in enumerate(container_obj.data.vertices):
            co = transfrom @ mathutils.Vector(bbox_verts[index])
            co = mat_ras2blender @ co
            co = mat_scene_scale @ co
            vert.co = co

        bioxels_obj.parent = container_obj
        container_obj.name = name
        container_obj.data.name = name
        container_obj.visible_camera = False
        container_obj.visible_diffuse = False
        container_obj.visible_glossy = False
        container_obj.visible_transmission = False
        container_obj.visible_volume_scatter = False
        container_obj.visible_shadow = False
        container_obj.display_type = 'WIRE'
        container_obj['bioxels_container'] = True
        container_obj['scene_scale'] = scene_scale
        container_obj['bioxel_size'] = bioxel_size
        container_obj['bioxels_max'] = bioxels_max
        container_obj['bioxels_min'] = bioxels_min
        container_obj['bioxels_offset'] = bioxels_offset
        container_obj['bioxels_shape'] = bioxels_shape

        bpy.ops.object.modifier_add(type='NODES')
        container_obj.modifiers[0].node_group = node_tree
        container_obj.modifiers[0].show_in_editmode = False
        container_obj.modifiers[0].show_viewport = False
        container_obj.modifiers[0].show_render = False

        # Create BioxelNodes to VDB object
        print(f"Creating BioxelNodes to the VDB...")

        if self.do_add_segmentnode:
            nodes = node_tree.nodes
            links = node_tree.links

            input_node = nodes.get("Group Input")
            output_node = nodes.get("Group Output")
            segment_node = custom_nodes.add_node(nodes, 'BioxelNodes_Segment')

            links.new(input_node.outputs[0], segment_node.inputs[0])
            links.new(segment_node.outputs[0], output_node.inputs[0])

        # Change render setting for better result
        if self.do_change_render_setting:
            bpy.context.scene.render.engine = 'CYCLES'
            bpy.context.scene.cycles.volume_bounces = 12
            bpy.context.scene.cycles.transparent_max_bounces = 64

        self.report({"INFO"}, "Successfully Imported")

        return {'FINISHED'}

    def invoke(self, context, event):
        # print(tuple(self.orig_shape))
        self.auto = True
        self.bioxel_size = 1
        context.window_manager.invoke_props_dialog(self)
        return {'RUNNING_MODAL'}


class ReadDICOM(bpy.types.Operator):
    bl_idname = "bioxelnodes.read_dicom"
    bl_label = "Volume Data as Biovels"
    bl_description = "Import Volume Data as Biovels (VDB)."
    bl_options = {'UNDO'}

    filepath: bpy.props.StringProperty(
        subtype="FILE_PATH"
    )  # type: ignore

    ok: bpy.props.BoolProperty(
        default=True
    )  # type: ignore

    def execute(self, context):
        files = get_data_files(self.filepath)

        import SimpleITK as sitk
        image = sitk.ReadImage(files)

        print("Collecting Meta Data...")
        print("Original Shape:", image.GetSize())
        print("Original Spacing:", image.GetSpacing())
        print("Original Origin:", image.GetOrigin())
        print("Original Direction:", image.GetDirection())

        bpy.ops.bioxelnodes.import_dicom_dialog(
            'INVOKE_DEFAULT',
            filepath=self.filepath,
            orig_shape=image.GetSize(),
            orig_spacing=image.GetSpacing()
        )

        self.report({"INFO"}, "Successfully Readed.")

        return {'FINISHED'}

    def modal(self, context, event):
        self.execute(context)
        return {'FINISHED'}

    def invoke(self, context, event):
        if not self.filepath:
            return {'CANCELLED'}

        if Path(self.filepath).suffix not in SUPPORT_EXTS:
            return {'CANCELLED'}

        show_message('Reading image data, it may take a while',
                     'Please be patient...')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class ImportDICOM(bpy.types.Operator):
    bl_idname = "bioxelnodes.import_dicom"
    bl_label = "Volume Data as Biovels"
    bl_description = "Import Volume Data as Biovels (VDB)."
    bl_options = {'UNDO'}

    filepath: bpy.props.StringProperty(
        subtype="FILE_PATH"
    )  # type: ignore

    def execute(self, context):
        bpy.ops.bioxelnodes.read_dicom(
            'INVOKE_DEFAULT',
            filepath=self.filepath
        )
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class BIOXELNODES_FH_ImportDicom(bpy.types.FileHandler):
    bl_idname = "BIOXELNODES_FH_ImportDicom"
    bl_label = "File handler for dicom import"
    bl_import_operator = "bioxelnodes.read_dicom"
    bl_file_extensions = ".dcm"

    @classmethod
    def poll_drop(cls, context):
        return (context.area and context.area.type == 'VIEW_3D')


class ExportVDB(bpy.types.Operator):
    bl_idname = "bioxelnodes.export_vdb"
    bl_label = "Bioxels as VDB"
    bl_description = "Export Bioxels original VDB data."
    bl_options = {'UNDO'}

    filepath: bpy.props.StringProperty(
        subtype="FILE_PATH"
    )  # type: ignore

    filename_ext = ".vdb"

    def invoke(self, context, event):
        bioxels_obj = None
        for obj in bpy.context.selected_objects:
            bioxels_obj = get_bioxels_obj(obj)
            break

        if bioxels_obj:
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({"WARNING"}, "Cannot find any bioxels.")
            return {'CANCELLED'}

    def execute(self, context):
        bioxels_obj = None
        for obj in bpy.context.selected_objects:
            bioxels_obj = get_bioxels_obj(obj)
            break

        filepath = f"{self.filepath.split('.')[0]}.vdb"
        output_path: Path = Path(filepath).resolve()
        source_path: Path = Path(bioxels_obj.data.filepath).resolve()
        # print('output_path', output_path)
        # print('source_path', source_path)
        shutil.copy(source_path, output_path)

        return {'FINISHED'}
