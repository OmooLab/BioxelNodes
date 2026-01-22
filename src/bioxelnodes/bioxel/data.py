from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable, List
import numpy as np
import SimpleITK as sitk
from pyometiff import OMETIFFReader
import mrcfile
import transforms3d

from .layer import Layer

# 类型定义
ProgressCallback = Optional[Callable[[float, str], None]]


SUPPORT_EXTS = [
    "",
    ".dcm",
    ".DCM",
    ".DICOM",
    ".ima",
    ".IMA",
    ".ome.tiff",
    ".ome.tif",
    ".tif",
    ".TIF",
    ".tiff",
    ".TIFF",
    ".mrc",
    ".mrc.gz",
    ".map",
    ".map.gz",
    ".bmp",
    ".BMP",
    ".png",
    ".PNG",
    ".jpg",
    ".JPG",
    ".jpeg",
    ".JPEG",
    ".PIC",
    ".pic",
    ".gipl",
    ".gipl.gz",
    ".lsm",
    ".LSM",
    ".mnc",
    ".MNC",
    ".mrc",
    ".rec",
    ".mha",
    ".mhd",
    ".hdf",
    ".h4",
    ".hdf4",
    ".he2",
    ".h5",
    ".hdf5",
    ".he5",
    ".nia",
    ".nii",
    ".nii.gz",
    ".hdr",
    ".img",
    ".img.gz",
    ".nrrd",
    ".nhdr",
    ".vtk",
    ".gz",
]

OME_EXTS = [".ome.tiff", ".ome.tif", ".tif", ".TIF", ".tiff", ".TIFF"]

MRC_EXTS = [".mrc", ".mrc.gz", ".map", ".map.gz"]

DICOM_EXTS = ["", ".dcm", ".DCM", ".DICOM", ".ima", ".IMA"]

SEQUENCE_EXTS = [
    ".bmp",
    ".BMP",
    ".jpg",
    ".JPG",
    ".jpeg",
    ".JPEG",
    ".tif",
    ".TIF",
    ".tiff",
    ".TIFF",
    ".png",
    ".PNG",
    ".mrc",
]


@dataclass
class Data:
    filepath: str
    series_id: str
    _data: Optional[np.ndarray] = field(default=None, repr=False)
    _meta: Optional[dict] = field(default=None, repr=False)

    @property
    def data(self) -> np.ndarray:
        if self._data is None:
            self.load_data()
        return self._data

    @property
    def meta(self) -> dict:
        if self._meta is None:
            self.load_meta()
        return self._meta

    @property
    def name(self) -> str:
        return self.meta["name"]

    @property
    def description(self) -> str:
        return self.meta["description"]

    @property
    def shape(self) -> tuple:
        return (
            self.meta["frame_count"],
            *self.meta["xyz_shape"],
            self.meta["channel_count"],
        )

    @property
    def xyz_shape(self) -> tuple:
        return self.meta["xyz_shape"]

    @property
    def spacing(self) -> tuple:
        return self.meta["spacing"]

    @property
    def affine(self) -> np.ndarray:
        return self.meta["affine"]

    @property
    def frame_count(self) -> int:
        return self.meta["frame_count"]

    @property
    def channel_count(self) -> int:
        return self.meta["channel_count"]

    @property
    def dtype(self) -> np.dtype:
        return self.meta.get("dtype", np.float32)

    def load_meta(self, progress_callback: ProgressCallback = None):
        data, meta = self._parse_file(progress_callback)
        self._meta = meta
        del data

    def load_data(self, progress_callback: ProgressCallback = None):
        if not self.is_loaded():
            data, meta = self._parse_file(progress_callback)
            self._data = data
            self._meta = meta

    def is_loaded(self) -> bool:
        return self._data is not None

    def to_layers(
        self,
        kind: str = "scalar",
        layer_name: str = "",
        bioxel_size: float = 1.0,
        smooth: int = 0,
        remap: bool = False,
        split_channel: bool = False,
        frame_source: str = "-1",
        progress_callback: ProgressCallback = None,
    ) -> List[Layer]:
        from .layer import Layer

        data = self.data.copy()

        data, layer_shape = self._transform_shape(data, frame_source)

        data = self._preprocess(data, kind, remap)

        mat_scale = transforms3d.zooms.zfdir2aff(bioxel_size)
        affine = np.dot(self.meta["affine"], mat_scale)

        base_name = layer_name or kind.capitalize()

        if kind == "label":
            return self._create_label_layers(
                data, base_name, layer_shape, affine, smooth, progress_callback
            )
        elif kind == "color":
            return self._create_color_layers(
                data, base_name, layer_shape, affine, progress_callback
            )
        elif kind == "scalar":
            return self._create_scalar_layers(
                data,
                base_name,
                layer_shape,
                affine,
                smooth,
                split_channel,
                progress_callback,
            )

        return []

    def _parse_file(self, progress_callback: ProgressCallback = None):
        data_path = Path(self.filepath).resolve()
        ext = self._get_ext(data_path)

        if progress_callback:
            progress_callback(0.0, "Reading Data...")

        is_sequence = False
        sequence = None
        if ext in SEQUENCE_EXTS:
            sequence = self._collect_sequence(data_path)
            if sequence and len(sequence) > 1:
                is_sequence = True

        data = None
        name = ""
        description = ""
        affine = np.identity(4)
        spacing = (1, 1, 1)
        origin = (0, 0, 0)
        direction = (1, 0, 0, 0, 1, 0, 0, 0, 1)

        if data is None and ext in MRC_EXTS and not is_sequence:
            data, name, spacing = self._parse_mrc(data_path)

        if data is None and ext in OME_EXTS and not is_sequence:
            data, name, spacing = self._parse_ome_tiff(data_path, progress_callback)

        if data is None:
            data, name, description, spacing, origin, direction = self._parse_sitk(
                data_path, ext, is_sequence, sequence, progress_callback
            )

        t = origin
        r = np.array(direction).reshape((3, 3))
        affine = np.dot(affine, transforms3d.affines.compose(t, r, [1, 1, 1]))

        meta = {
            "name": name,
            "description": description,
            "spacing": spacing,
            "affine": affine,
            "xyz_shape": data.shape[1:4],
            "frame_count": data.shape[0],
            "channel_count": data.shape[-1],
            "dtype": data.dtype,
        }

        return data, meta

    def _parse_mrc(self, data_path: Path):
        print("Parsing with mrcfile...")
        with mrcfile.open(data_path, "r") as mrc:
            mrc_data = mrc.data

            if mrc.is_single_image():
                data = np.expand_dims(np.asarray(mrc_data), axis=0)
                data = np.expand_dims(data, axis=-1)
                data = np.expand_dims(data, axis=-1)
            elif mrc.is_image_stack():
                data = np.expand_dims(np.asarray(mrc_data), axis=-1)
                data = np.expand_dims(data, axis=-1)
            elif mrc.is_volume():
                data = np.expand_dims(np.asarray(mrc_data), axis=0)
                data = np.expand_dims(data, axis=-1)
            elif mrc.is_volume_stack():
                data = np.expand_dims(np.asarray(mrc_data), axis=-1)

            name = self._get_file_no_digits_name(data_path)
            spacing = (mrc.voxel_size.x, mrc.voxel_size.y, mrc.voxel_size.z)

        return data, name, spacing

    def _parse_ome_tiff(self, data_path: Path, progress_callback=None):
        print("Parsing with OMETIFFReader...")
        reader = OMETIFFReader(fpath=data_path)
        ome_image, metadata, xml_metadata = reader.read()

        if progress_callback:
            progress_callback(0.5, "Transpose to 'TXYZC'...")

        try:
            ome_order = metadata["DimOrder BF Array"]
            data = self._transpose_ome_image(ome_image, ome_order)

            try:
                spacing = (
                    metadata["PhysicalSizeX"],
                    metadata["PhysicalSizeY"],
                    metadata["PhysicalSizeZ"],
                )
            except:
                spacing = (1, 1, 1)

            name = self._get_file_no_digits_name(data_path)
        except Exception as e:
            print(f"Error parsing OME-TIFF: {e}")
            data = np.zeros((1, 1, 1, 1, 1), dtype=np.float32)
            name = ""
            spacing = (1, 1, 1)

        return data, name, spacing

    def _parse_sitk(
        self,
        data_path: Path,
        ext: str,
        is_sequence: bool,
        sequence: Optional[list],
        progress_callback=None,
    ):
        print("Parsing with SimpleITK...")

        if ext in DICOM_EXTS:
            data_dirpath = data_path.parent
            reader = sitk.ImageSeriesReader()
            reader.MetaDataDictionaryArrayUpdateOn()
            reader.LoadPrivateTagsOn()
            series_files = reader.GetGDCMSeriesFileNames(
                str(data_dirpath), self.series_id
            )
            reader.SetFileNames(series_files)

            itk_image = reader.Execute()
            name, description = self._extract_dicom_meta(reader, data_dirpath)

        elif ext in SEQUENCE_EXTS and is_sequence and sequence:
            sequence_list = sequence if sequence else []
            itk_image = sitk.ReadImage(sequence_list)
            name = self._get_file_no_digits_name(data_path)
            description = ""

        else:
            itk_image = sitk.ReadImage(data_path)
            name = self._get_filename(data_path)
            description = ""

        if progress_callback:
            progress_callback(0.5, "Transpose to 'TXYZC'...")

        data = self._convert_sitk_to_numpy(itk_image, ext, is_sequence)

        if itk_image.GetDimension() >= 3 and ext not in SEQUENCE_EXTS:
            spacing = tuple(itk_image.GetSpacing())
            origin = tuple(itk_image.GetOrigin())
            direction = tuple(itk_image.GetDirection())
        else:
            spacing = (1, 1, 1)
            origin = (0, 0, 0)
            direction = (1, 0, 0, 0, 1, 0, 0, 0, 1)

        return data, name, description, spacing, origin, direction

    def _transpose_ome_image(self, ome_image, ome_order: str):
        if ome_image.ndim == 2:
            ome_order = ome_order.replace("T", "").replace("C", "").replace("Z", "")
            bioxel_order = (ome_order.index("X"), ome_order.index("Y"))
            data = np.transpose(ome_image, bioxel_order)
            data = np.expand_dims(data, axis=0)
            data = np.expand_dims(data, axis=-1)
            data = np.expand_dims(data, axis=-1)

        elif ome_image.ndim == 3:
            ome_order = ome_order.replace("T", "").replace("C", "")
            bioxel_order = (
                ome_order.index("X"),
                ome_order.index("Y"),
                ome_order.index("Z"),
            )
            data = np.transpose(ome_image, bioxel_order)
            data = np.expand_dims(data, axis=0)
            data = np.expand_dims(data, axis=-1)

        elif ome_image.ndim == 4:
            ome_order = ome_order.replace("T", "")
            bioxel_order = (
                ome_order.index("X"),
                ome_order.index("Y"),
                ome_order.index("Z"),
                ome_order.index("C"),
            )
            data = np.transpose(ome_image, bioxel_order)
            data = np.expand_dims(data, axis=0)

        elif ome_image.ndim == 5:
            bioxel_order = (
                ome_order.index("T"),
                ome_order.index("X"),
                ome_order.index("Y"),
                ome_order.index("Z"),
                ome_order.index("C"),
            )
            data = np.transpose(ome_image, bioxel_order)

        return data

    def _convert_sitk_to_numpy(self, itk_image, ext: str, is_sequence: bool):
        if itk_image.GetDimension() == 2:
            data = sitk.GetArrayFromImage(itk_image)

            if data.ndim == 3:
                data = np.transpose(data, (1, 0, 2))
                data = np.expand_dims(data, axis=-2)
            else:
                data = np.transpose(data)
                data = np.expand_dims(data, axis=-1)
                data = np.expand_dims(data, axis=-1)

            data = np.expand_dims(data, axis=0)

        elif itk_image.GetDimension() == 3:
            if ext not in SEQUENCE_EXTS:
                itk_image = sitk.DICOMOrient(itk_image, "RAS")

            data = sitk.GetArrayFromImage(itk_image)

            if data.ndim == 4:
                data = np.transpose(data, (2, 1, 0, 3))
            else:
                data = np.transpose(data)
                data = np.expand_dims(data, axis=-1)

            data = np.expand_dims(data, axis=0)

        elif itk_image.GetDimension() == 4:
            data = sitk.GetArrayFromImage(itk_image)

            if data.ndim == 5:
                data = np.transpose(data, (0, 3, 2, 1, 4))
            else:
                data = np.transpose(data, (0, 3, 2, 1))
                data = np.expand_dims(data, axis=-1)

        return data

    def _extract_dicom_meta(self, reader, data_dirpath: Path):
        def get_meta(key):
            try:
                string = reader.GetMetaData(0, key).removesuffix(" ")
                string.encode("utf-8")
                if string in ["No study description", "No series description", ""]:
                    return None
                else:
                    return string
            except:
                return None

        study_description = get_meta("0008|1030") or data_dirpath.name
        series_description = get_meta("0008|103e")
        series_modality = get_meta("0008|0060")

        if series_description and series_modality:
            description = f"{series_description}-{series_modality}"
        elif series_description:
            description = series_description
        elif series_modality:
            description = series_modality
        else:
            description = ""

        name = study_description.replace(" ", "-")
        description = description.replace(" ", "-")

        return name, description

    @staticmethod
    def _get_ext(filepath: Path) -> str:
        if filepath.name.endswith(".nii.gz"):
            return ".nii.gz"
        elif filepath.name.endswith(".img.gz"):
            return ".img.gz"
        elif filepath.name.endswith(".gipl.gz"):
            return ".gipl.gz"
        elif filepath.name.endswith(".ome.tiff"):
            return ".ome.tiff"
        elif filepath.name.endswith(".ome.tif"):
            return ".ome.tif"
        elif filepath.name.endswith(".mrc.gz"):
            return ".mrc.gz"
        elif filepath.name.endswith(".map.gz"):
            return ".map.gz"
        else:
            suffix = filepath.suffix
            return "" if len(suffix) > 5 else suffix

    @staticmethod
    def _get_filename(filepath: Path) -> str:
        ext = Data._get_ext(filepath)
        return filepath.name.removesuffix(ext)

    @staticmethod
    def _get_file_no_digits_name(filepath: Path) -> str:
        prefix, digits, suffix = Data._get_filename_parts(filepath)
        prefix = Data._remove_end_str(prefix, "_")
        prefix = Data._remove_end_str(prefix, ".")
        prefix = Data._remove_end_str(prefix, "-")
        prefix = Data._remove_end_str(prefix, " ")
        return prefix + suffix

    @staticmethod
    def _get_filename_parts(filepath: Path) -> tuple:
        def has_digits(s):
            return any(char.isdigit() for char in s)

        name = Data._get_filename(filepath)
        parts = name.replace(".", " ").replace("_", " ").split(" ")
        skip_prefixs = ["CH", "ch", "channel"]
        number_part = None
        number_part_i = None

        for i, part in enumerate(parts[::-1]):
            if has_digits(part):
                if not any([part.startswith(prefix) for prefix in skip_prefixs]):
                    number_part = part
                    number_part_i = len(parts) - i
                    break

        if number_part is None:
            return name, "", ""

        prefix_parts = parts[: number_part_i - 1]
        prefix_parts_count = sum([len(part) + 1 for part in prefix_parts])

        digits = ""
        suffix = ""

        started = False
        for char in number_part[::-1]:
            if char.isdigit():
                started = True
                digits += char
            else:
                if started:
                    break
                else:
                    suffix += char

        digits = digits[::-1]

        prefix_parts_count += len(number_part) - len(digits) - len(suffix)

        prefix = name[:prefix_parts_count]
        suffix = name[prefix_parts_count + len(digits) :]

        return prefix, digits, suffix

    @staticmethod
    def _get_file_index(filepath: Path) -> int:
        prefix, digits, suffix = Data._get_filename_parts(filepath)
        return int(digits) if digits != "" else 0

    @staticmethod
    def _collect_sequence(filepath: Path):
        file_dict = {}
        for f in filepath.parent.iterdir():
            if (
                f.is_file()
                and Data._get_ext(filepath) == Data._get_ext(f)
                and Data._get_file_no_digits_name(filepath)
                == Data._get_file_no_digits_name(f)
            ):
                index = Data._get_file_index(f)
                file_dict[index] = f

        for key in list(file_dict.keys()):
            if not file_dict.get(key + 1) and not file_dict.get(key - 1):
                del file_dict[key]

        file_dict = dict(sorted(file_dict.items()))
        sequence = [str(f) for f in file_dict.values()]

        if len(sequence) == 0:
            sequence = [str(filepath)]

        return sequence

    @staticmethod
    def _remove_end_str(string: str, end: str) -> str:
        while string.endswith(end) and len(string) > 0:
            string = string.removesuffix(end)
        return string

    def _transform_shape(self, data, frame_source: str) -> tuple:
        orig_shape = self.xyz_shape

        if frame_source == "-1":
            data = data[0:1, :, :, :, :]
            new_shape = orig_shape
        elif frame_source == "0":
            new_shape = orig_shape
        elif frame_source == "1":
            data = data.transpose(1, 0, 2, 3, 4)
            new_shape = (1, orig_shape[1], orig_shape[2])
        elif frame_source == "2":
            data = data.transpose(2, 1, 0, 3, 4)
            new_shape = (orig_shape[0], 1, orig_shape[2])
        elif frame_source == "3":
            data = data.transpose(3, 1, 2, 0, 4)
            new_shape = (orig_shape[0], orig_shape[1], 1)
        else:
            data = data.transpose(4, 1, 2, 3, 0)
            new_shape = orig_shape

        return data, new_shape

    def _preprocess(self, data, kind: str, remap: bool) -> np.ndarray:
        if kind == "color":
            if np.issubdtype(data.dtype, np.uint8):
                data = np.multiply(data, 1.0 / 256, dtype=np.float32)
            elif data.dtype.kind in ["u", "i"]:
                data = data.astype(np.float32)
                min_val, max_val = data.min(), data.max()
                if max_val != min_val:
                    data = (data - min_val) / (max_val - min_val)
                else:
                    data = np.zeros_like(data, dtype=np.float32)
            else:
                data = data.astype(np.float32)

            if data.shape[4] == 1:
                data = np.repeat(data, repeats=3, axis=4)
            elif data.shape[4] == 2:
                zeros_shape = list(data.shape[:4]) + [1]
                zeros = np.zeros(zeros_shape, dtype=np.float32)
                data = np.concatenate((data, zeros), axis=-1)
            elif data.shape[4] > 3:
                data = data[:, :, :, :, :3]

        elif kind == "scalar":
            if remap:
                data = data.astype(np.float32)
                min_val, max_val = data.min(), data.max()
                if max_val != min_val:
                    data = (data - min_val) / (max_val - min_val)
                else:
                    data = np.zeros_like(data, dtype=np.float32)

        elif kind == "label":
            data = data.astype(int)

        return data

    def _create_progress_cb_factory(self, progress_callback):
        def factory(name, progress, progress_step):
            def callback(frame, total):
                if progress_callback:
                    sub_progress = progress + frame * (progress_step / total)
                    progress_callback(
                        sub_progress, f"Processing {name} Frame {frame+1}..."
                    )

            return callback

        return factory

    def _create_label_layers(
        self,
        data,
        base_name,
        layer_shape,
        affine,
        smooth,
        progress_callback: ProgressCallback,
    ):
        from .layer import Layer

        layers = []
        label_count = int(np.max(data))
        if label_count == 0:
            return layers

        progress_step = 0.7 / label_count
        cb_factory = self._create_progress_cb_factory(progress_callback)

        for i in range(label_count):
            name_i = f"{base_name}_{i+1}"
            progress = 0.2 + i * progress_step
            if progress_callback:
                progress_callback(progress, f"Processing {name_i}...")

            label_data = data == np.full_like(data, i + 1)
            progress_cb = cb_factory(name_i, progress, progress_step)

            layer = Layer(data=label_data, name=name_i, kind="label")
            layer.resize(
                shape=layer_shape, smooth=smooth, progress_callback=progress_cb
            )
            layer.affine = affine
            layers.append(layer)

        return layers

    def _create_color_layers(
        self, data, base_name, layer_shape, affine, progress_callback: ProgressCallback
    ):
        from .layer import Layer

        if progress_callback:
            progress_callback(0.2, f"Processing {base_name}...")

        cb_factory = self._create_progress_cb_factory(progress_callback)
        progress_cb = cb_factory(base_name, 0.2, 0.7)

        layer = Layer(data=data, name=base_name, kind="color")
        layer.resize(shape=layer_shape, progress_callback=progress_cb)
        layer.affine = affine

        return [layer]

    def _create_scalar_layers(
        self,
        data,
        base_name,
        layer_shape,
        affine,
        smooth,
        split_channel,
        progress_callback: ProgressCallback,
    ):
        from .layer import Layer

        layers = []
        cb_factory = self._create_progress_cb_factory(progress_callback)

        if split_channel:
            channel_count = data.shape[-1]
            progress_step = 0.7 / channel_count

            for i in range(channel_count):
                name_i = f"{base_name}_{i+1}"
                progress = 0.2 + i * progress_step
                if progress_callback:
                    progress_callback(progress, f"Processing {name_i}...")

                progress_cb = cb_factory(name_i, progress, progress_step)
                layer = Layer(
                    data=data[:, :, :, :, i : i + 1], name=name_i, kind="scalar"
                )
                layer.resize(
                    shape=layer_shape, smooth=smooth, progress_callback=progress_cb
                )
                layer.affine = affine
                layers.append(layer)
        else:
            if progress_callback:
                progress_callback(0.2, f"Processing {base_name}...")

            progress_cb = cb_factory(base_name, 0.2, 0.7)
            layer = Layer(data=data, name=base_name, kind="scalar")
            layer.resize(
                shape=layer_shape, smooth=smooth, progress_callback=progress_cb
            )
            layer.affine = affine
            layers.append(layer)

        return layers


# 模块级函数签名
def read(
    filepath: str, series_id: str = "", progress_callback: ProgressCallback = None
) -> Data:
    filepath = Path(filepath).resolve()
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    data_obj = Data(filepath=filepath, series_id=series_id)
    data_obj.load_data(progress_callback)
    return data_obj


def read_meta(filepath: str, series_id: str = "") -> Data:
    data_obj = Data(filepath=filepath, series_id=series_id)
    data_obj.load_meta()
    return data_obj


def calc_layer_shape(
    bioxel_size: float, orig_shape: tuple, orig_spacing: tuple
) -> tuple:
    shape = (
        int(orig_shape[0] / bioxel_size * orig_spacing[0]),
        int(orig_shape[1] / bioxel_size * orig_spacing[1]),
        int(orig_shape[2] / bioxel_size * orig_spacing[2]),
    )
    return (
        shape[0] if shape[0] > 0 else 1,
        shape[1] if shape[1] > 0 else 1,
        shape[2] if shape[2] > 0 else 1,
    )


def calc_layer_size(shape: tuple, bioxel_size: float, scale: float = 1.0) -> tuple:
    size = (
        float(shape[0] * bioxel_size * scale),
        float(shape[1] * bioxel_size * scale),
        float(shape[2] * bioxel_size * scale),
    )
    return size


def get_ext(filepath: Path) -> str:
    if filepath.name.endswith(".nii.gz"):
        return ".nii.gz"
    elif filepath.name.endswith(".img.gz"):
        return ".img.gz"
    elif filepath.name.endswith(".gipl.gz"):
        return ".gipl.gz"
    elif filepath.name.endswith(".ome.tiff"):
        return ".ome.tiff"
    elif filepath.name.endswith(".ome.tif"):
        return ".ome.tif"
    elif filepath.name.endswith(".mrc.gz"):
        return ".mrc.gz"
    elif filepath.name.endswith(".map.gz"):
        return ".map.gz"
    else:
        suffix = filepath.suffix
        return "" if len(suffix) > 5 else suffix
