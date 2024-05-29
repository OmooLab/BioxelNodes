import bpy
import shutil
from bpy_extras.io_utils import axis_conversion
import pyopenvdb as vdb
import numpy as np
from pathlib import Path
from uuid import uuid4
import mathutils

from .nodes import custom_nodes
from .props import BIOXELNODES_Series
from .utils import (calc_bbox_verts, get_container, get_layer, get_text_index_str,
                    get_node_by_type, hide_in_ray, lock_transform, show_message)

try:
    import SimpleITK as sitk
except:
    ...

SUPPORT_EXTS = ['.dcm', '.DCM', '.DICOM',
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

SEQUENCE_EXTS = ['.dcm', '.DCM', '.DICOM',
                 '.bmp', '.BMP',
                 '.jpg', '.JPG', '.jpeg', '.JPEG',
                 '.tif', '.TIF', '.tiff', '.TIFF',
                 '.png', '.PNG']

DICOM_EXTS = ['.dcm', '.DCM', '.DICOM']

FH_EXTS = ['.dcm', '.DCM', '.DICOM',
           '.gipl', '.gipl.gz',
           '.mnc', '.MNC',
           '.mrc', '.rec',
           '.mha', '.mhd',
           '.nia', '.nii', '.nii.gz', '.hdr', '.img', '.img.gz',
           '.hdf', '.h4', '.hdf4', '.he2', '.h5', '.hdf5', '.he5',
           '.nrrd', '.nhdr',
           '.vtk',
           '.gz']


def get_layer_shape(bioxel_size: float, orig_shape: tuple, orig_spacing: tuple):
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
    layers = [sitk.VectorIndexSelectionCast(
        image, i, sitk.sitkFloat32) for i in range(image.GetNumberOfComponentsPerPixel())]
    # linear mapping
    I = (0.2126*layers[0] + 0.7152*layers[1] + 0.0722*layers[2])

    return sitk.Cast(I, sitk.sitkFloat32)


def x2gray(image):
    return sitk.VectorIndexSelectionCast(image, 0, sitk.sitkUInt16)


class ImportVolumeDataDialog(bpy.types.Operator):
    bl_idname = "bioxelnodes.import_volume_data_dialog"
    bl_label = "Volume Data as Bioxel Layer"
    bl_description = "Import Volume Data as Bioxel Layer"
    bl_options = {'UNDO'}

    filepath: bpy.props.StringProperty(
        subtype="FILE_PATH"
    )  # type: ignore

    container_name: bpy.props.StringProperty()   # type: ignore
    layer_name: bpy.props.StringProperty()   # type: ignore

    series_id: bpy.props.StringProperty()   # type: ignore

    resample_method: bpy.props.EnumProperty(
        name="Resample Method",
        default="linear",
        items=[("linear", "Linear", ""),
               ("nearest_neighbor", "Nearest Neighbor", ""),
               ("gaussian", "Gaussian", "")]
    )  # type: ignore

    container: bpy.props.StringProperty()   # type: ignore

    read_as: bpy.props.EnumProperty(
        name="Read as",
        default="scalar",
        items=[("scalar", "Scalar", ""),
               ("labels", "Labels", "")]
    )  # type: ignore

    bioxel_size: bpy.props.FloatProperty(
        name="Bioxel Size (Larger size means small resolution)",
        soft_min=0.1, soft_max=10.0,
        min=0.1, max=1e2,
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
        name="Scene Scale (Bioxel Unit pre Blender Unit)",
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
        image, name = read_image(self.filepath, self.series_id)
        container_name = self.container_name or name
        bioxel_size = self.bioxel_size
        orig_spacing = self.orig_spacing
        image_spacing = image.GetSpacing()
        image_shape = image.GetSize()

        layer_spacing = (
            image_spacing[0] / orig_spacing[0] * bioxel_size,
            image_spacing[1] / orig_spacing[1] * bioxel_size,
            image_spacing[2] / orig_spacing[2] * bioxel_size
        )

        layer_shape = get_layer_shape(
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
            size=layer_shape,
            transform=sitk.Transform(),
            interpolator=interpolator,
            outputOrigin=image.GetOrigin(),
            outputSpacing=layer_spacing,
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
            array = array[:, :, :, 0]

        array = np.transpose(array)

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

        # Wrapper a Container
        if not self.container:
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

            bpy.ops.mesh.primitive_cube_add(
                enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1)
            )
            container = bpy.context.active_object

            bbox_verts = calc_bbox_verts((0, 0, 0), array.shape)
            for index, vert in enumerate(container.data.vertices):
                bbox_transform = transfrom
                vert.co = bbox_transform @ mathutils.Vector(bbox_verts[index])

            container.matrix_world = mat_ras2blender @ mat_scene_scale
            container.name = container_name
            container.data.name = container_name

            container['bioxel_container'] = True
            container['scene_scale'] = scene_scale
            bpy.ops.node.new_geometry_nodes_modifier()
            container_node_tree = container.modifiers[0].node_group
            input_node = get_node_by_type(container_node_tree.nodes,
                                          'NodeGroupInput')[0]
            container_node_tree.links.remove(input_node.outputs[0].links[0])

            # bpy.ops.mesh.primitive_cube_add(
            #     enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1)
            # )
            # frame = bpy.context.active_object
            # bbox_verts = calc_bbox_verts((0, 0, 0), array.shape)
            # for index, vert in enumerate(frame.data.vertices):
            #     # bbox_transform = mat_ras2blender @ mat_scene_scale @ transfrom
            #     bbox_transform = transfrom
            #     vert.co = bbox_transform @ mathutils.Vector(bbox_verts[index])

            # frame.name = f"Frame_{container_name}"
            # frame.data.name = f"Frame_{container_name}"
            # lock_transform(frame)
            # hide_in_ray(frame)
            # frame.hide_select = True
            # frame.hide_render = True
            # frame.display_type = 'WIRE'
            # frame.parent = container

        else:
            container = bpy.data.objects[self.container]
            container_node_tree = container.modifiers[0].node_group

        preferences = context.preferences.addons[__package__].preferences
        cache_dir = Path(preferences.cache_dir, 'VDBs')
        cache_dir.mkdir(parents=True, exist_ok=True)

        loc, rot, sca = transfrom.decompose()

        layer_origin = tuple(loc)
        layer_rotation = tuple(rot.to_euler())
        layer_shape = tuple(array.shape)

        def create_layer(array, layer_name, layer_type="scalar"):
            grid = vdb.FloatGrid()
            array = array.copy().astype(float)
            grid.copyFromArray(array)
            grid.transform = vdb.createLinearTransform(transfrom.transposed())
            grid.name = layer_type

            vdb_path = Path(cache_dir, f"{uuid4()}.vdb")
            print(f"Storing the cache ({str(vdb_path)})...")
            vdb.write(str(vdb_path), grids=[grid])

            # Read VDB
            print(f"Loading the cache to Blender scene...")
            bpy.ops.object.volume_import(
                filepath=str(vdb_path), align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))

            layer = bpy.context.active_object

            # Set props to VDB object
            layer.name = layer_name
            layer.data.name = layer_name

            lock_transform(layer)
            hide_in_ray(layer)
            layer.hide_select = True
            layer.hide_render = True
            layer.hide_viewport = True
            layer.data.display.use_slice = True
            layer.data.display.density = 1e-05

            layer['bioxel_layer'] = True
            layer['bioxel_layer_type'] = layer_type
            layer.parent = container

            for collection in layer.users_collection:
                collection.objects.unlink(layer)

            for collection in container.users_collection:
                collection.objects.link(layer)

            print(f"Creating layer ...")

            bpy.ops.node.new_geometry_nodes_modifier()
            node_tree = layer.modifiers[0].node_group
            nodes = node_tree.nodes
            links = node_tree.links

            input_node = get_node_by_type(nodes, 'NodeGroupInput')[0]
            output_node = get_node_by_type(nodes, 'NodeGroupOutput')[0]

            node_type = 'BioxelNodes_AsLabel' if layer_type == "label" else 'BioxelNodes_AsScalar'
            source_node = custom_nodes.add_node(nodes, node_type)

            links.new(input_node.outputs[0], source_node.inputs[0])
            links.new(source_node.outputs[0], output_node.inputs[0])

            source_node.inputs['Bioxel Size'].default_value = bioxel_size
            source_node.inputs['Shape'].default_value = layer_shape
            source_node.inputs['Origin'].default_value = layer_origin
            source_node.inputs['Rotation'].default_value = layer_rotation

            return layer

        if self.read_as == "labels":
            orig_max = int(np.max(array))
            orig_min = int(np.min(array))
            layer_name = self.layer_name or "Label"

            for i in range(orig_max):
                label = array == np.full_like(array, i+1)
                layer = create_layer(array=label,
                                     layer_name=f"{container_name}_{layer_name}_{i+1}",
                                     layer_type="label")

                output_node = get_node_by_type(container_node_tree.nodes,
                                               'NodeGroupOutput')[0]
                mask_node = custom_nodes.add_node(container_node_tree.nodes,
                                                  'BioxelNodes_MaskByLabel')
                mask_node.inputs[0].default_value = layer
                if len(output_node.inputs[0].links) == 0:
                    container_node_tree.links.new(mask_node.outputs[0],
                                                  output_node.inputs[0])

        else:
            if self.invert_scalar:
                array = -array

            orig_max = float(np.max(array))
            orig_min = float(np.min(array))
            orig_median = float(np.median(array))
            orig_percentile80 = float(np.percentile(array, 80)) \
                if self.invert_scalar else float(np.percentile(array, 80))

            stats_table = [("Max", orig_max),
                           ("Min", orig_min),
                           ("Median", orig_median),
                           ("80%", orig_percentile80)]

            print("Volume Data Stats:")
            for stats in stats_table:
                print("| {: >10} | {: >40} |".format(*stats))

            scalar_offset = 0
            if orig_min < 0:
                scalar_offset = -orig_min
                array = array + np.full_like(array, scalar_offset)

            layer_name = self.layer_name or "Scalar"
            layer = create_layer(array=array,
                                 layer_name=f"{container_name}_{layer_name}",
                                 layer_type="scalar")

            layer_node_tree = layer.modifiers[0].node_group
            source_node = layer_node_tree.nodes['BioxelNodes_AsScalar']
            source_node.inputs['Offset'].default_value = scalar_offset
            source_node.inputs['Max'].default_value = orig_max
            source_node.inputs['Min'].default_value = orig_min

            output_node = get_node_by_type(container_node_tree.nodes,
                                           'NodeGroupOutput')[0]
            mask_node = custom_nodes.add_node(container_node_tree.nodes,
                                              'BioxelNodes_MaskByThreshold')
            mask_node.inputs[0].default_value = layer

            if len(output_node.inputs[0].links) == 0:
                container_node_tree.links.new(mask_node.outputs[0],
                                              output_node.inputs[0])

        bpy.context.view_layer.objects.active = container

        # Change render setting for better result
        if preferences.do_change_render_setting:
            bpy.context.scene.render.engine = 'CYCLES'
            bpy.context.scene.cycles.volume_bounces = 12
            bpy.context.scene.cycles.transparent_max_bounces = 16
            bpy.context.scene.cycles.volume_preview_step_rate = 10

        self.report({"INFO"}, "Successfully Imported")

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_props_dialog(self, width=400)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layer_shape = get_layer_shape(
            self.bioxel_size, self.orig_shape, self.orig_spacing)
        bioxel_count = layer_shape[0] * layer_shape[1] * layer_shape[2]
        text = f"Shape will be: {str(layer_shape)} {bioxel_count:,} "
        if bioxel_count > 100000000:
            text += "**TOO LARGE!**"

        layout = self.layout
        panel = layout.box()
        panel.prop(self, "container_name")
        panel.prop(self, "layer_name")

        panel = layout.box()
        panel.prop(self, "resample_method")
        panel.prop(self, "bioxel_size")
        row = panel.row()
        row.prop(self, "orig_spacing")
        panel.label(text=text)

        panel = layout.box()
        panel.prop(self, "do_orient")

        panel = layout.box()
        panel.prop(self, "read_as")
        if self.read_as == "labels":
            ...
        else:
            panel.prop(self, "invert_scalar")

        panel = layout.box()
        panel.prop(self, "scene_scale")


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


class ParseVolumeData(bpy.types.Operator):
    bl_idname = "bioxelnodes.parse_volume_data"
    bl_label = "Volume Data as Bioxel Layer"
    bl_description = "Import Volume Data as Bioxel Layer"
    bl_options = {'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # type: ignore
    directory: bpy.props.StringProperty(subtype='DIR_PATH')  # type: ignore
    container: bpy.props.StringProperty()   # type: ignore

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
        for k in image.GetMetaDataKeys():
            stats_table.append((k, str(image.GetMetaData(k))))

        print("Meta Data:")
        for stats in stats_table:
            print("| {: >20} | {: >100} |".format(*stats))

        do_orient = ext not in SEQUENCE_EXTS or ext in DICOM_EXTS

        orig_shape = image.GetSize()
        orig_spacing = image.GetSpacing()
        min_size = min(orig_spacing[0], orig_spacing[1], orig_spacing[2])
        bioxel_size = max(min_size, 1.0)
        if self.container:
            container = bpy.data.objects[self.container]
            container_name = container.name
        else:
            container_name = name

        bpy.ops.bioxelnodes.import_volume_data_dialog(
            'INVOKE_DEFAULT',
            filepath=self.filepath,
            container_name=container_name,
            orig_shape=orig_shape,
            orig_spacing=orig_spacing,
            bioxel_size=bioxel_size,
            series_id=self.series_id or "",
            do_orient=do_orient,
            container=self.container
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
    bl_label = "Volume Data as Bioxel Layer"
    bl_description = "Import Volume Data as Bioxel Layer"
    bl_options = {'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # type: ignore
    directory: bpy.props.StringProperty(subtype='DIR_PATH')  # type: ignore

    def execute(self, context):
        bpy.ops.bioxelnodes.parse_volume_data(
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
        bl_import_operator = "bioxelnodes.parse_volume_data"
        bl_file_extensions = ";".join(FH_EXTS)

        @classmethod
        def poll_drop(cls, context):
            return (context.area and context.area.type == 'VIEW_3D')
except:
    ...


class AddVolumeData(bpy.types.Operator):
    bl_idname = "bioxelnodes.add_volume_data"
    bl_label = "Add Volume Data to Container"
    bl_description = "Add Volume Data to Container"
    bl_options = {'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # type: ignore
    directory: bpy.props.StringProperty(subtype='DIR_PATH')  # type: ignore

    @classmethod
    def poll(cls, context):
        container = get_container(bpy.context.active_object)
        return True if container else False

    def execute(self, context):
        container = get_container(bpy.context.active_object)

        bpy.ops.bioxelnodes.parse_volume_data(
            'INVOKE_DEFAULT',
            filepath=self.filepath,
            directory=self.directory,
            container=container.name
        )
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class ExportVDB(bpy.types.Operator):
    bl_idname = "bioxelnodes.export_vdb"
    bl_label = "Bioxel Layer as VDB"
    bl_description = "Export Bioxel Layer as VDB"
    bl_options = {'UNDO'}

    filepath: bpy.props.StringProperty(
        subtype="FILE_PATH"
    )  # type: ignore

    filename_ext = ".vdb"

    @classmethod
    def poll(cls, context):
        layer = get_layer(bpy.context.active_object)
        return True if layer else False

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        layer = get_layer(bpy.context.active_object)

        filepath = f"{self.filepath.split('.')[0]}.vdb"
        # "//"
        source_dir = bpy.path.abspath(layer.data.filepath)

        output_path: Path = Path(filepath).resolve()
        source_path: Path = Path(source_dir).resolve()
        # print('output_path', output_path)
        # print('source_path', source_path)
        shutil.copy(source_path, output_path)

        self.report({"INFO"}, f"Successfully exported to {output_path}")

        return {'FINISHED'}
