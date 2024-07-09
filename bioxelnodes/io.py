import math
import bpy
import shutil
from bpy_extras.io_utils import axis_conversion
import pyopenvdb as vdb
import numpy as np
from pathlib import Path
from uuid import uuid4
import mathutils
import random

from . import skimage as ski
from .nodes import custom_nodes
from .props import BIOXELNODES_Series
from .utils import (calc_bbox_verts, get_all_layers, get_container_from_selection, get_layer, get_text_index_str,
                    get_nodes_by_type, hide_in_ray, lock_transform, move_node_between_nodes, move_node_to_node, save_vdb, show_message)

try:
    import SimpleITK as sitk
except:
    ...

SUPPORT_EXTS = ['', '.dcm', '.DCM', '.DICOM',
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

DICOM_EXTS = ['', '.dcm', '.DCM', '.DICOM']

FH_EXTS = ['', '.dcm', '.DCM', '.DICOM',
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


def get_layer_size(shape: tuple, bioxel_size: float, scale: float = 1.0):
    size = (float(shape[0] * bioxel_size * scale),
            float(shape[1] * bioxel_size * scale),
            float(shape[2] * bioxel_size * scale))

    return size


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


def collect_sequence(filepath: str):
    file_path = Path(filepath).resolve()

    files = list(file_path.parent.iterdir())
    files = [f for f in files if f.is_file()
             and get_ext(file_path) == get_ext(f)
             and get_sequence_name(file_path) == get_sequence_name(f)]

    files.sort(key=get_sequence_index)
    sequence = [str(f) for f in files]
    return sequence


def parse_volume_data(filepath: str, series_id=""):
    ext = get_ext(filepath)

    if ext in DICOM_EXTS:
        dir_path = Path(filepath).resolve().parent
        reader = sitk.ImageSeriesReader()
        reader.MetaDataDictionaryArrayUpdateOn()
        reader.LoadPrivateTagsOn()
        series_files = reader.GetGDCMSeriesFileNames(
            str(dir_path), series_id)
        reader.SetFileNames(series_files)
        itk_volume = reader.Execute()
        name = dir_path.name

    elif ext in SEQUENCE_EXTS:
        itk_volume = sitk.ReadImage(filepath)
        if itk_volume.GetDimension() == 2:
            sequence = collect_sequence(filepath)
            itk_volume = sitk.ReadImage(sequence)
            name = get_sequence_name(filepath)
        else:
            itk_volume = sitk.ReadImage(filepath)
            name = Path(filepath).name.removesuffix(ext)
    else:
        itk_volume = sitk.ReadImage(filepath)
        name = Path(filepath).name.removesuffix(ext)

    itk_volume = sitk.DICOMOrient(itk_volume, 'RAS')
    volume = sitk.GetArrayFromImage(itk_volume)

    if volume.ndim == 4:
        volume = np.transpose(volume, (2, 1, 0, 3))
    else:
        volume = np.transpose(volume)

    meta = {
        "name": name,
        "shape": tuple(itk_volume.GetSize()),
        "spacing": tuple(itk_volume.GetSpacing()),
        "origin": tuple(itk_volume.GetOrigin()),
        "direction": tuple(itk_volume.GetDirection()),
    }

    for key, value in meta.items():
        print(f"{key}: {value}")

    return volume, meta


class ImportVolumeDataDialog(bpy.types.Operator):
    bl_idname = "bioxelnodes.import_volume_data_dialog"
    bl_label = "Volume Data as Bioxel Layer"
    bl_description = "Import Volume Data as Bioxel Layer"
    bl_options = {'UNDO'}

    filepath: bpy.props.StringProperty(
        subtype="FILE_PATH"
    )  # type: ignore

    container_name: bpy.props.StringProperty(
        name="Container Name"
    )   # type: ignore

    layer_name: bpy.props.StringProperty(
        name="Layer Name",
    )   # type: ignore

    series_id: bpy.props.StringProperty()   # type: ignore

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
        soft_min=0.0001, soft_max=10.0,
        min=1e-6, max=1e6,
        default=0.01,
    )  # type: ignore

    do_orient: bpy.props.BoolProperty(
        name="Orient to RAS",
        default=True,
    )  # type: ignore

    def execute(self, context):
        is_first_import = len(get_all_layers()) == 0
        volume, meta = parse_volume_data(self.filepath)
        container_name = self.container_name or meta['name'] or "Container"
        bioxel_size = self.bioxel_size
        orig_spacing = self.orig_spacing

        layer_spacing = (
            meta['spacing'][0] / orig_spacing[0] * bioxel_size,
            meta['spacing'][1] / orig_spacing[1] * bioxel_size,
            meta['spacing'][2] / orig_spacing[2] * bioxel_size
        )

        dtype_index = volume.dtype.num

        layer_shape = get_layer_shape(
            bioxel_size, meta['shape'], orig_spacing)

        # After sitk.DICOMOrient(), origin and direction will also orient base on LPS
        # so we need to convert them into RAS
        mat_lps2ras = axis_conversion(
            from_forward='-Z',
            from_up='-Y',
            to_forward='-Z',
            to_up='Y'
        ).to_4x4()

        mat_location = mathutils.Matrix.Translation(
            mathutils.Vector(meta['origin'])
        )

        mat_rotation = mathutils.Matrix(
            np.array(meta['direction']).reshape((3, 3))
        ).to_4x4()

        mat_scale = mathutils.Matrix.Scale(
            bioxel_size, 4
        )

        # transfrom = mat_lps2ras @ mat_location @ mat_rotation @ mat_scale \
        #     if self.do_orient else mat_location @ mat_rotation @ mat_scale

        transfrom = mat_lps2ras @ mat_location @ mat_rotation @ mat_scale

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

            bbox_verts = calc_bbox_verts((0, 0, 0), layer_shape)
            for index, vert in enumerate(container.data.vertices):
                vert.co = transfrom @ mathutils.Vector(bbox_verts[index])

            container.matrix_world = mat_ras2blender @ mat_scene_scale
            container.name = container_name
            container.data.name = container_name

            container['bioxel_container'] = True
            container['scene_scale'] = scene_scale
            bpy.ops.node.new_geometry_nodes_modifier()
            container_node_group = container.modifiers[0].node_group
            input_node = get_nodes_by_type(container_node_group,
                                           'NodeGroupInput')[0]
            container_node_group.links.remove(input_node.outputs[0].links[0])

        else:
            container = bpy.data.objects[self.container]
            container_node_group = container.modifiers[0].node_group

        preferences = context.preferences.addons[__package__].preferences
        loc, rot, sca = transfrom.decompose()

        layer_origin = tuple(loc)
        layer_rotation = tuple(rot.to_euler())

        def create_layer(volume, layer_name, layer_type="scalar"):
            grid = vdb.FloatGrid()
            volume = volume.copy().astype(np.float32)
            grid.copyFromArray(volume)
            # grid.transform = vdb.createLinearTransform(transfrom.transposed())
            grid.name = layer_type

            vdb_path = save_vdb([grid], context)

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
            node_group = layer.modifiers[0].node_group

            input_node = get_nodes_by_type(node_group, 'NodeGroupInput')[0]
            output_node = get_nodes_by_type(node_group, 'NodeGroupOutput')[0]

            to_layer_node = custom_nodes.add_node(node_group,
                                                  "BioxelNodes__ConvertToLayer")

            node_group.links.new(input_node.outputs[0],
                                 to_layer_node.inputs[0])
            node_group.links.new(to_layer_node.outputs[0],
                                 output_node.inputs[0])

            # for compatibility to old vdb
            to_layer_node.inputs['Not Transfromed'].default_value = True
            to_layer_node.inputs['Layer ID'].default_value = random.randint(-200000000,
                                                                            200000000)
            to_layer_node.inputs['Data Type'].default_value = dtype_index
            to_layer_node.inputs['Bioxel Size'].default_value = bioxel_size
            to_layer_node.inputs['Shape'].default_value = layer_shape
            to_layer_node.inputs['Origin'].default_value = layer_origin
            to_layer_node.inputs['Rotation'].default_value = layer_rotation

            move_node_between_nodes(to_layer_node, [input_node, output_node])

            return layer

        if self.read_as == "labels":
            if volume.ndim == 4:
                volume = np.amax(volume, -1)
            volume = volume.astype(int)
            orig_max = int(np.max(volume))
            orig_min = int(np.min(volume))
            layer_name = self.layer_name or "Label"

            for i in range(orig_max):
                label = volume == np.full_like(volume, i+1)
                print(f"Resampling...")
                label = ski.resize(label,
                                   layer_shape,
                                   preserve_range=True,
                                   anti_aliasing=False)
                layer = create_layer(volume=label,
                                     layer_name=f"{container_name}_{layer_name}_{i+1}",
                                     layer_type="label")

                mask_node = custom_nodes.add_node(container_node_group,
                                                  'BioxelNodes_MaskByLabel')
                mask_node.label = f"{layer_name}_{i+1}"
                mask_node.inputs[0].default_value = layer

                # Connect to output if no output linked
                output_node = get_nodes_by_type(container_node_group,
                                                'NodeGroupOutput')[0]
                if len(output_node.inputs[0].links) == 0:
                    container_node_group.links.new(mask_node.outputs[0],
                                                   output_node.inputs[0])
                    move_node_to_node(mask_node, output_node, (-300, 0))
                else:
                    move_node_to_node(mask_node, output_node,
                                      (0, -100 * (i+1)))

        else:
            if volume.ndim == 4:
                volume = np.amax(volume, -1)
                # volume = skimage.color.rgb2gray(volume)

            # if volume.dtype.kind == 'u':
            #     imax_in = np.iinfo(volume.dtype).max
            #     volume = np.multiply(volume, 255.0 / imax_in, dtype=np.float32)
            # elif volume.dtype.kind == 'i':
            #     volume = volume.astype(np.float32)

            # should not change any value!
            volume = volume.astype(np.float32)

            print(f"Resampling...")
            volume = ski.resize(volume,
                                layer_shape,
                                anti_aliasing=True)

            orig_max = float(np.max(volume))
            orig_min = float(np.min(volume))

            scalar_offset = 0
            if orig_min < 0:
                scalar_offset = -orig_min
                volume = volume + np.full_like(volume, scalar_offset)

            layer_name = self.layer_name or "Scalar"
            layer = create_layer(volume=volume,
                                 layer_name=f"{container_name}_{layer_name}",
                                 layer_type="scalar")

            layer_node_group = layer.modifiers[0].node_group
            to_layer_node = layer_node_group.nodes['BioxelNodes__ConvertToLayer']
            to_layer_node.inputs['Scalar Offset'].default_value = scalar_offset
            to_layer_node.inputs['Scalar Max'].default_value = orig_max
            to_layer_node.inputs['Scalar Min'].default_value = orig_min

            mask_node = custom_nodes.add_node(container_node_group,
                                              'BioxelNodes_MaskByThreshold')
            mask_node.label = layer_name
            mask_node.inputs[0].default_value = layer

            # Connect to output if no output linked
            output_node = get_nodes_by_type(container_node_group,
                                            'NodeGroupOutput')[0]

            if len(output_node.inputs[0].links) == 0:
                container_node_group.links.new(mask_node.outputs[0],
                                               output_node.inputs[0])
                move_node_to_node(mask_node, output_node, (-300, 0))
            else:
                move_node_to_node(mask_node, output_node, (0, -100))

        bpy.context.view_layer.objects.active = container

        # Change render setting for better result
        if preferences.do_change_render_setting and is_first_import:
            bpy.context.scene.render.engine = 'CYCLES'
            try:
                bpy.context.scene.cycles.shading_system = True
                bpy.context.scene.cycles.volume_bounces = 12
                bpy.context.scene.cycles.transparent_max_bounces = 16
                bpy.context.scene.cycles.volume_preview_step_rate = 10
                bpy.context.scene.cycles.volume_step_rate = 10
                bpy.context.scene.eevee.volumetric_tile_size = '2'
                bpy.context.scene.eevee.volumetric_shadow_samples = 128
                bpy.context.scene.eevee.volumetric_samples = 256
            except:
                pass

        self.report({"INFO"}, "Successfully Imported")

        return {'FINISHED'}

    def invoke(self, context, event):
        if self.read_as == "labels":
            volume_dtype = "Label"
        elif self.read_as == "scalar":
            volume_dtype = "Scalar"
        title = f"Import as **{volume_dtype}** (Add to Container: {self.container})" \
            if self.container != "" else f"Import as **{volume_dtype}** (Init a Container)"
        context.window_manager.invoke_props_dialog(self,
                                                   width=500,
                                                   title=title)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layer_shape = get_layer_shape(self.bioxel_size,
                                      self.orig_shape,
                                      self.orig_spacing)
        layer_size = get_layer_size(layer_shape,
                                    self.bioxel_size,
                                    self.scene_scale)

        bioxel_count = layer_shape[0] * layer_shape[1] * layer_shape[2]
        layer_shape_text = f"Shape will be: {str(layer_shape)} {bioxel_count:,} "
        if bioxel_count > 100000000:
            layer_shape_text += "**TOO LARGE!**"

        layer_size_text = f"Size will be: ({layer_size[0]:.2f}, {layer_size[1]:.2f}, {layer_size[2]:.2f}) m"

        layout = self.layout
        if self.container == "":
            layout.prop(self, "container_name")
        layout.prop(self, "layer_name")

        panel = layout.box()
        panel.prop(self, "bioxel_size")
        row = panel.row()
        row.prop(self, "orig_spacing")
        panel.label(text=layer_shape_text)

        if self.container == "":
            panel = layout.box()
            panel.prop(self, "scene_scale")
            panel.label(text=layer_size_text)


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

    read_as: bpy.props.EnumProperty(
        name="Read as",
        default="scalar",
        items=[("scalar", "Scalar", ""),
               ("labels", "Labels", "")]
    )  # type: ignore

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
        volume, meta = parse_volume_data(self.filepath)
        if self.read_as == "labels":
            not_int = volume.dtype.kind != "b" and volume.dtype.kind != "i" and volume.dtype.kind != "u"
            too_large = np.max(volume) > 100

            if not_int or too_large:
                self.report(
                    {"WARNING"}, "This volume data does not looks like labels, please check again.")
                return {'CANCELLED'}

        # do_orient = ext not in SEQUENCE_EXTS or ext in DICOM_EXTS

        orig_shape = meta['shape']
        orig_spacing = meta['spacing']
        min_size = min(orig_spacing[0], orig_spacing[1], orig_spacing[2])
        bioxel_size = max(min_size, 1.0)

        layer_size = get_layer_size(orig_shape,
                                    bioxel_size)
        log10 = math.floor(math.log10(max(*layer_size)))
        scene_scale = math.pow(10, -log10)

        if self.container:
            container = bpy.data.objects[self.container]
            container_name = container.name
        else:
            container_name = meta['name']

        bpy.ops.bioxelnodes.import_volume_data_dialog(
            'INVOKE_DEFAULT',
            filepath=self.filepath,
            container_name=container_name,
            orig_shape=orig_shape,
            orig_spacing=orig_spacing,
            bioxel_size=bioxel_size,
            series_id=self.series_id or "",
            # do_orient=do_orient,
            container=self.container,
            read_as=self.read_as,
            scene_scale=scene_scale
        )

        self.report({"INFO"}, "Successfully Readed.")

        return {'FINISHED'}

    def modal(self, context, event):
        self.execute(context)
        return {'FINISHED'}

    def invoke(self, context, event):
        if not self.filepath and not self.directory:
            return {'CANCELLED'}

        show_message('Parsing volume data, it may take a while...',
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


class ImportVolumeData():
    bl_options = {'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # type: ignore
    directory: bpy.props.StringProperty(subtype='DIR_PATH')  # type: ignore

    read_as = "scalar"

    def execute(self, context):
        containers = get_container_from_selection()

        if len(containers) > 0:
            bpy.ops.bioxelnodes.parse_volume_data(
                'INVOKE_DEFAULT',
                filepath=self.filepath,
                directory=self.directory,
                container=containers[0].name,
                read_as=self.read_as
            )
        else:
            bpy.ops.bioxelnodes.parse_volume_data(
                'INVOKE_DEFAULT',
                filepath=self.filepath,
                directory=self.directory,
                read_as=self.read_as
            )

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class ImportAsScalarLayer(bpy.types.Operator, ImportVolumeData):
    bl_idname = "bioxelnodes.import_as_scalar_layer"
    bl_label = "Import as Scalar"
    bl_description = "Import Volume Data to Container as Scalar"
    read_as = "scalar"


class ImportAsLabelLayer(bpy.types.Operator, ImportVolumeData):
    bl_idname = "bioxelnodes.import_as_label_layer"
    bl_label = "Import as Labels"
    bl_description = "Import Volume Data to Container as Label"
    read_as = "labels"


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
    bl_label = "Import as Bioxel Layer"
    bl_description = "Import additional Volume Data to Container"
    bl_options = {'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # type: ignore
    directory: bpy.props.StringProperty(subtype='DIR_PATH')  # type: ignore

    @classmethod
    def poll(cls, context):
        containers = get_container_from_selection()
        return len(containers) > 0

    def execute(self, context):
        containers = get_container_from_selection()

        bpy.ops.bioxelnodes.parse_volume_data(
            'INVOKE_DEFAULT',
            filepath=self.filepath,
            directory=self.directory,
            container=containers[0].name
        )
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class ExportVolumeData(bpy.types.Operator):
    bl_idname = "bioxelnodes.export_volume_data"
    bl_label = "Export Bioxel as VDB"
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
