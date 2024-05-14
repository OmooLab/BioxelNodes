import bpy
import shutil
from bpy_extras.io_utils import axis_conversion
import pyopenvdb as vdb
import numpy as np
from pathlib import Path
from uuid import uuid4
import mathutils
import math
from .utils import calc_bbox_verts, get_text_index_str, get_bioxels_obj, get_node_by_type, show_message
from .nodes import custom_nodes
from .props import BIOXELNODES_Series
try:
    import SimpleITK as sitk
except:
    ...

SUPPORT_EXTS = ['.dcm', '.DICOM',
                '.bmp', '.BMP',
                '.PIC', '.pic',
                '.gipl', '.gipl.gz',
                '.jpg', '.JPG', '.jpeg', '.JPEG',
                '.lsm', '.LSM',
                '.tif', '.TIF', '.tiff', '.TIFF',
                '.mnc', '.MNC',
                '.mrc', '.rec',
                '.mha', '.mhd',
                '.hdf', '.h4', '.hdf4', '.he2', '.h5', '.hdf5', '.he5',
                '.nia', '.nii', '.nii.gz', '.hdr', '.img', '.img.gz',
                '.nrrd', '.nhdr',
                '.png', '.PNG',
                '.vtk']

SEQUENCE_EXTS = ['.dcm', '.DICOM',
                 '.bmp', '.BMP',
                 '.jpg', '.JPG', '.jpeg', '.JPEG',
                 '.tif', '.TIF', '.tiff', '.TIFF',
                 '.png', '.PNG']

DICOM_EXTS = ['.dcm', '.DICOM']

FH_EXTS = ['.dcm', '.DICOM',
           '.gipl', '.gipl.gz',
           '.mnc', '.MNC',
           '.mrc', '.rec',
           '.mha', '.mhd',
           '.nia', '.nii', '.nii.gz', '.hdr', '.img', '.img.gz',
           '.hdf', '.h4', '.hdf4', '.he2', '.h5', '.hdf5', '.he5',
           '.nrrd', '.nhdr',
           '.vtk',
           '.gz']


def get_bioxels_shape(bioxel_size: float, orig_shape: tuple, orig_spacing: tuple):
    shape = (int(orig_shape[0] / bioxel_size * orig_spacing[0]),
             int(orig_shape[1] / bioxel_size * orig_spacing[1]),
             int(orig_shape[2] / bioxel_size * orig_spacing[2]))

    return (shape[0] if shape[0] > 0 else 1,
            shape[1] if shape[1] > 0 else 1,
            shape[2] if shape[2] > 0 else 1)


def get_ext(filepath: str) -> str:
    file_path = Path(filepath)
    if file_path.name.endswith(".nii.gz"):
        return ".nii.gz"
    elif file_path.name.endswith(".img.gz"):
        return ".img.gz"
    elif file_path.name.endswith(".gipl.gz"):
        return ".gipl.gz"
    else:
        return file_path.suffix


def get_sequence_name(filepath: str) -> str:
    ext = get_ext(filepath)
    filename = Path(filepath).name.removesuffix(ext)
    index: str = get_text_index_str(filename)
    return filename.removesuffix(index)


def get_sequence_index(filepath: str) -> int:
    ext = get_ext(filepath)
    filename = Path(filepath).name.removesuffix(ext)
    index: str = get_text_index_str(filename)
    return int(index) if index else 0


def collect_image_sequence(filepath: str):
    file_path = Path(filepath).resolve()

    files = list(file_path.parent.iterdir())
    files = [f for f in files if f.is_file()
             and get_ext(file_path) == get_ext(f)
             and get_sequence_name(file_path) == get_sequence_name(f)]

    files.sort(key=get_sequence_index)
    sequence = [str(f) for f in files]
    return sequence


def read_image(filepath: str, series_id=""):
    ext = get_ext(filepath)

    if ext in DICOM_EXTS:
        dir_path = Path(filepath).resolve().parent
        reader = sitk.ImageSeriesReader()
        reader.MetaDataDictionaryArrayUpdateOn()
        reader.LoadPrivateTagsOn()
        series_files = reader.GetGDCMSeriesFileNames(
            str(dir_path), series_id)
        reader.SetFileNames(series_files)
        image = reader.Execute()
        name = dir_path.name

    elif ext in SEQUENCE_EXTS:
        image = sitk.ReadImage(filepath)
        if image.GetDimension() == 2:
            sequence = collect_image_sequence(filepath)
            image = sitk.ReadImage(sequence)
            name = get_sequence_name(filepath)
        else:
            image = sitk.ReadImage(filepath)
            name = Path(filepath).name.removesuffix(ext)
    else:
        image = sitk.ReadImage(filepath)
        name = Path(filepath).name.removesuffix(ext)

    return image, name


def rgb2gray(image):
    # Convert sRGB image to gray scale and rescale results to [0,255]
    channels = [sitk.VectorIndexSelectionCast(
        image, i, sitk.sitkFloat32) for i in range(image.GetNumberOfComponentsPerPixel())]
    # linear mapping
    I = (0.2126*channels[0] + 0.7152*channels[1] + 0.0722*channels[2])

    return sitk.Cast(I, sitk.sitkFloat32)

def x2gray(image):
    return sitk.VectorIndexSelectionCast(image, 0, sitk.sitkUInt16)

class ImportVolumeDataDialog(bpy.types.Operator):
    bl_idname = "bioxelnodes.import_volume_data_dialog"
    bl_label = "Volume Data as Bioxels"
    bl_description = "Import Volume Data as Bioxels (VDB)"
    bl_options = {'UNDO'}

    filepath: bpy.props.StringProperty(
        subtype="FILE_PATH",
        options={'HIDDEN'}
    )  # type: ignore

    series_id: bpy.props.StringProperty()   # type: ignore

    resample_method: bpy.props.EnumProperty(
        name="Resample Method",
        default="linear",
        items=[("linear", "Linear", ""),
               ("nearest_neighbor", "Nearest Neighbor", ""),
               ("gaussian", "Gaussian", "")]
    )  # type: ignore

    read_as: bpy.props.EnumProperty(
        name="Read as",
        default="scalar",
        items=[("scalar", "Scalar", ""),
               ("labels", "Labels", "")]
    )  # type: ignore

    label_index: bpy.props.IntProperty(
        name="Label Index",
        default=1
    )  # type: ignore

    bioxel_size: bpy.props.FloatProperty(
        name="Bioxel Size (Larger size means small resolution)",
        soft_min=0.1, soft_max=10.0,
        min=1e-2, max=1e2,
        default=1,
    )  # type: ignore

    orig_spacing: bpy.props.FloatVectorProperty(
        name="Original Spacing",
        default=(1, 1, 1),
    )  # type: ignore

    orig_shape: bpy.props.IntVectorProperty(
        name="Original Shape",
        default=(100, 100, 100)
    )  # type: ignore

    scene_scale: bpy.props.FloatProperty(
        name="Scene Scale (Bioxels Unit pre Blender Unit)",
        soft_min=0.001, soft_max=100.0,
        min=1e-6, max=1e6,
        default=0.01,
    )  # type: ignore

    do_orient: bpy.props.BoolProperty(
        name="Orient to RAS",
        default=True,
    )  # type: ignore

    invert_scalar: bpy.props.BoolProperty(
        name="Invert Scalar (Background value maybe higher than object)",
        default=False,
    )  # type: ignore

    def execute(self, context):
        image, bioxels_name = read_image(self.filepath, self.series_id)

        bioxel_size = self.bioxel_size
        orig_spacing = self.orig_spacing
        image_spacing = image.GetSpacing()
        image_shape = image.GetSize()

        bioxels_spacing = (
            image_spacing[0] / orig_spacing[0] * bioxel_size,
            image_spacing[1] / orig_spacing[1] * bioxel_size,
            image_spacing[2] / orig_spacing[2] * bioxel_size
        )

        bioxels_shape = get_bioxels_shape(
            bioxel_size, image_shape, orig_spacing)

        if self.read_as == "labels":
            if "vector" in image.GetPixelIDTypeAsString():
                print("Convet to Grayscale...")
                image = x2gray(image)
            else:
                image = sitk.Cast(image, sitk.sitkUInt16)
            default_value = 0
        elif self.read_as == "scalar":
            if "vector" in image.GetPixelIDTypeAsString():
                print("Convet to Grayscale...")
                image = rgb2gray(image)
            else:
                image = sitk.Cast(image, sitk.sitkFloat32)

            stats = sitk.StatisticsImageFilter()
            stats.Execute(image)
            default_value = stats.GetMaximum() if self.invert_scalar else stats.GetMinimum()

        if self.resample_method == "linear":
            interpolator = sitk.sitkLinear
        elif self.resample_method == "nearest_neighbor":
            interpolator = sitk.sitkNearestNeighbor
        elif self.resample_method == "gaussian":
            interpolator = sitk.sitkGaussian

        print(f"Resampling...")
        image = sitk.Resample(
            image1=image,
            size=bioxels_shape,
            transform=sitk.Transform(),
            interpolator=interpolator,
            outputOrigin=image.GetOrigin(),
            outputSpacing=bioxels_spacing,
            outputDirection=image.GetDirection(),
            defaultPixelValue=default_value,
            outputPixelType=image.GetPixelID(),
        )

        if self.do_orient:
            print("Orienting to RAS...")
            image = sitk.DICOMOrient(image, 'RAS')

        print("Oriented Origin:", image.GetOrigin())
        print("Oriented Direction:", image.GetDirection())

        # return {'FINISHED'}

        # ITK indices, by convention, are [i,j,k] while NumPy indices are [k,j,i]
        # https://www.slicer.org/wiki/Coordinate_systems

        # ITK                  Numpy      3D
        # R (ight)     i   ->    k   ->   x
        # A (nterior)  j   ->    j   ->   y
        # S (uperior)  k   ->    i   ->   z
        array = sitk.GetArrayFromImage(image)

        orig_dtype = str(array.dtype)
        # print(f"Coverting Dtype from {orig_dtype} to float...")
        # array = array.astype(float)

        if array.ndim == 4:
            # if array.shape[0] == 3 and self.read_as == "scalar":
            #     # RGB -> Grayscale
            #     array = np.dot(array[..., :3], [0.2989, 0.5870, 0.1140])
            # else:
            #     array = array[:, :, :, 0]
            array = array[:, :, :, 0]

        array = np.transpose(array)

        bioxels_shape = array.shape
        bioxels_offset = 0.0

        if self.read_as == "labels":
            array = array == np.full_like(array, self.label_index)
            bioxels_default_threshold = 1.0
            bioxels_max = 1.0
            bioxels_min = 0.0
            bioxels_name = f"{bioxels_name}_{self.label_index}"
        else:
            if self.invert_scalar:
                array = -array

            orig_max = float(np.max(array))
            orig_min = float(np.min(array))
            orig_median = float(np.median(array))
            orig_percentile80 = float(np.percentile(array, 80)) \
                if self.invert_scalar else float(np.percentile(array, 80))

            # if (orig_dtype[0] != "u" and orig_min < 0) \
            #         or (orig_dtype[0] == "u" and self.invert_scalar):
            if orig_min < 0:
                bioxels_offset = -orig_min
                array = array + np.full_like(array, bioxels_offset)

            bioxels_default_threshold = orig_percentile80
            bioxels_max = float(np.max(array))
            bioxels_min = float(np.min(array))

            stats_table = [("Max", orig_max),
                           ("Min", orig_min),
                           ("Median", orig_median),
                           ("80%", orig_percentile80)]

            print("Bioxels Value Stats:")
            for stats in stats_table:
                print("| {: >10} | {: >40} |".format(*stats))

        # # Build VDB
        grid = vdb.BoolGrid() if self.read_as == "labels" else vdb.FloatGrid()
        grid.copyFromArray(array.copy().astype(float))

        # After sitk.DICOMOrient(), origin and direction will also orient base on LPS
        # so we need to convert them into RAS
        mat_lps2ras = axis_conversion(
            from_forward='-Z',
            from_up='-Y',
            to_forward='-Z',
            to_up='Y'
        ).to_4x4()

        origin = image.GetOrigin()
        direction = image.GetDirection()

        mat_location = mathutils.Matrix.Translation(
            mathutils.Vector(origin)
        )

        mat_rotation = mathutils.Matrix(
            np.array(direction).reshape((3, 3))
        ).to_4x4()

        mat_scale = mathutils.Matrix.Scale(
            bioxel_size, 4
        )

        transfrom = mat_lps2ras @ mat_location @ mat_rotation @ mat_scale \
            if self.do_orient else mat_location @ mat_rotation @ mat_scale

        grid.transform = vdb.createLinearTransform(transfrom.transposed())
        grid.name = "scalar"

        preferences = context.preferences.addons[__package__].preferences
        vdb_dirpath = Path(preferences.cache_dir, 'VDBs')
        vdb_dirpath.mkdir(parents=True, exist_ok=True)
        vdb_path = Path(vdb_dirpath, f"{uuid4()}.vdb")

        print(f"Storing the VDB file ({str(vdb_path)})...")
        vdb.write(str(vdb_path), grids=[grid])

        # Read VDB
        print(f"Importing the VDB file to Blender scene...")
        bpy.ops.object.volume_import(
            filepath=str(vdb_path), align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))

        bioxels_obj = bpy.context.active_object

        # Set props to VDB object
        bioxels_obj.name = f"{bioxels_name}_Bioxels"
        bioxels_obj.data.name = f"{bioxels_name}_Bioxels"

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
            bbox_transform = mat_ras2blender @ mat_scene_scale @ transfrom
            vert.co = bbox_transform @ mathutils.Vector(bbox_verts[index])

        bioxels_obj.parent = container_obj
        container_obj.name = bioxels_name
        container_obj.data.name = bioxels_name
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

        if preferences.do_add_segmentnode:
            nodes = node_tree.nodes
            links = node_tree.links

            input_node = get_node_by_type(nodes, 'NodeGroupInput')[0]
            output_node = get_node_by_type(nodes, 'NodeGroupOutput')[0]

            segment_node = custom_nodes.add_node(
                nodes, 'BioxelNodes_Segment')

            segment_node.inputs['Threshold'].default_value = bioxels_default_threshold

            links.new(input_node.outputs[0], segment_node.inputs[0])
            links.new(segment_node.outputs[0], output_node.inputs[0])

        # Change render setting for better result
        if preferences.do_change_render_setting:
            bpy.context.scene.render.engine = 'CYCLES'
            bpy.context.scene.cycles.volume_bounces = 12
            bpy.context.scene.cycles.transparent_max_bounces = 64

        self.report({"INFO"}, "Successfully Imported")

        return {'FINISHED'}

    def invoke(self, context, event):
        min_size = min(
            self.orig_spacing[0], self.orig_spacing[1], self.orig_spacing[2])
        default_size = 1.0
        self.bioxel_size = min_size if min_size > default_size else default_size
        context.window_manager.invoke_props_dialog(self, width=400)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        bioxels_shape = get_bioxels_shape(
            self.bioxel_size, self.orig_shape, self.orig_spacing)
        bioxel_count = bioxels_shape[0] * bioxels_shape[1] * bioxels_shape[2]
        text = f"Shape will be: {str(bioxels_shape)} {bioxel_count:,} "
        if bioxel_count > 100000000:
            text += "**TOO LARGE!**"

        panel = layout.box()
        panel.prop(self, "resample_method")
        panel.prop(self, "bioxel_size")
        row = panel.row()
        row.prop(self, "orig_spacing")
        panel.label(text=text)

        panel = layout.box()
        panel.prop(self, "read_as")
        if self.read_as == "labels":
            panel.prop(self, "label_index")
        else:
            panel.prop(self, "invert_scalar")

        panel = layout.box()
        panel.prop(self, "scene_scale")
        panel.prop(self, "do_orient")


def get_series_ids(self, context):
    items = []
    for index, series_id in enumerate(self.series_ids):
        items.append((
            series_id.id,
            series_id.label,
            "",
            index
        ))

    return items


class ReadDICOM(bpy.types.Operator):
    bl_idname = "bioxelnodes.read_dicom"
    bl_label = "Volume Data as Bioxels"
    bl_description = "Import Volume Data as Bioxels (VDB)"
    bl_options = {'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # type: ignore
    directory: bpy.props.StringProperty(subtype='DIR_PATH')  # type: ignore

    series_id: bpy.props.EnumProperty(
        name="Select Series",
        items=get_series_ids
    )  # type: ignore

    series_ids: bpy.props.CollectionProperty(
        type=BIOXELNODES_Series)  # type: ignore

    def execute(self, context):
        ext = get_ext(self.filepath)
        if ext not in SUPPORT_EXTS:
            self.report({"WARNING"}, "Not supported extension.")
            return {'CANCELLED'}

        print("Collecting Meta Data...")
        image, name = read_image(self.filepath, self.series_id)
        stats_table = [("Shape", str(image.GetSize())),
                       ("Spacing", str(image.GetSpacing())),
                       ("Origin", str(image.GetOrigin())),
                       ("Direction", str(image.GetDirection())),
                       ("Data Type", image.GetPixelIDTypeAsString())]

        print("Meta Data:")
        for stats in stats_table:
            print("| {: >10} | {: >40} |".format(*stats))

        do_orient = ext not in SEQUENCE_EXTS or ext in DICOM_EXTS

        bpy.ops.bioxelnodes.import_volume_data_dialog(
            'INVOKE_DEFAULT',
            filepath=self.filepath,
            orig_shape=image.GetSize(),
            orig_spacing=image.GetSpacing(),
            series_id=self.series_id or "",
            do_orient=do_orient
        )

        self.report({"INFO"}, "Successfully Readed.")

        return {'FINISHED'}

    def modal(self, context, event):
        self.execute(context)
        return {'FINISHED'}

    def invoke(self, context, event):
        if not self.filepath and not self.directory:
            return {'CANCELLED'}

        show_message('Reading image data, it may take a while...',
                     'Please be patient...')

        if get_ext(self.filepath) == '.dcm':
            dir_path = Path(self.filepath).parent
            reader = sitk.ImageSeriesReader()
            reader.MetaDataDictionaryArrayUpdateOn()
            reader.LoadPrivateTagsOn()
            series_ids = reader.GetGDCMSeriesIDs(str(dir_path))

            for _id in series_ids:
                series_id = self.series_ids.add()
                series_id.id = _id
                series_id.label = _id

            if len(series_ids) > 1:
                context.window_manager.invoke_props_dialog(self, width=400)
                return {'RUNNING_MODAL'}
            else:
                self.series_id = series_ids[0]

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "series_id")
        layout.label(
            text="Reading image data, it may take a while...")
        layout.label(
            text="Please be patient...")


class ImportVolumeData(bpy.types.Operator):
    bl_idname = "bioxelnodes.import_volume_data"
    bl_label = "Volume Data as Bioxels"
    bl_description = "Import Volume Data as Bioxels (VDB)"
    bl_options = {'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # type: ignore
    directory: bpy.props.StringProperty(subtype='DIR_PATH')  # type: ignore

    def execute(self, context):
        bpy.ops.bioxelnodes.read_dicom(
            'INVOKE_DEFAULT',
            filepath=self.filepath,
            directory=self.directory
        )
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


try:
    class BIOXELNODES_FH_ImportVolumeData(bpy.types.FileHandler):
        bl_idname = "BIOXELNODES_FH_ImportVolumeData"
        bl_label = "File handler for dicom import"
        bl_import_operator = "bioxelnodes.read_dicom"
        bl_file_extensions = ";".join(FH_EXTS)

        @classmethod
        def poll_drop(cls, context):
            return (context.area and context.area.type == 'VIEW_3D')
except:
    ...


class ExportVDB(bpy.types.Operator):
    bl_idname = "bioxelnodes.export_vdb"
    bl_label = "Bioxels as VDB"
    bl_description = "Export Bioxels original VDB data"
    bl_options = {'UNDO'}

    filepath: bpy.props.StringProperty(
        subtype="FILE_PATH"
    )  # type: ignore

    filename_ext = ".vdb"

    @classmethod
    def poll(cls, context):
        bioxels_obj = None
        for obj in bpy.context.selected_objects:
            bioxels_obj = get_bioxels_obj(obj)
            break

        return True if bioxels_obj else False

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        bioxels_obj = None
        for obj in bpy.context.selected_objects:
            bioxels_obj = get_bioxels_obj(obj)
            break

        filepath = f"{self.filepath.split('.')[0]}.vdb"
        # "//"
        source_dir = bpy.path.abspath(bioxels_obj.data.filepath)

        output_path: Path = Path(filepath).resolve()
        source_path: Path = Path(source_dir).resolve()
        # print('output_path', output_path)
        # print('source_path', source_path)
        shutil.copy(source_path, output_path)

        self.report({"INFO"}, f"Successfully exported to {output_path}")

        return {'FINISHED'}
