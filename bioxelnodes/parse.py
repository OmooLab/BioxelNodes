from pathlib import Path
import numpy as np

from .exceptions import CancelledByUser
from .utils import get_text_index_str

try:
    import SimpleITK as sitk
    from pyometiff import OMETIFFReader
    import mrcfile
except:
    ...

"""
Convert any volumetric data to 3D numpy array with order TXYZC
"""

SUPPORT_EXTS = ['', '.dcm', '.DCM', '.DICOM', '.ima', '.IMA',
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
                '.vtk',
                '.ome.tiff', '.ome.tif',
                '.mrc', '.mrc.gz', '.map', '.map.gz']

OME_EXTS = ['.ome.tiff', '.ome.tif',
            '.tif', '.TIF', '.tiff', '.TIFF']

MRC_EXTS = ['.mrc', '.mrc.gz', '.map', '.map.gz']

SEQUENCE_EXTS = ['.bmp', '.BMP',
                 '.jpg', '.JPG', '.jpeg', '.JPEG',
                 '.tif', '.TIF', '.tiff', '.TIFF',
                 '.png', '.PNG']

DICOM_EXTS = ['', '.dcm', '.DCM', '.DICOM', '.ima', '.IMA']

FH_EXTS = ['', '.dcm', '.DCM', '.DICOM', '.ima', '.IMA',
           '.gipl', '.gipl.gz',
           '.mnc', '.MNC',
           '.mrc', '.rec',
           '.mha', '.mhd',
           '.nia', '.nii', '.nii.gz', '.hdr', '.img', '.img.gz',
           '.hdf', '.h4', '.hdf4', '.he2', '.h5', '.hdf5', '.he5',
           '.nrrd', '.nhdr',
           '.vtk',
           '.gz']


def get_ext(filepath: str) -> str:
    file_path = Path(filepath)
    if file_path.name.endswith(".nii.gz"):
        return ".nii.gz"
    elif file_path.name.endswith(".img.gz"):
        return ".img.gz"
    elif file_path.name.endswith(".gipl.gz"):
        return ".gipl.gz"
    elif file_path.name.endswith(".ome.tiff"):
        return ".ome.tiff"
    elif file_path.name.endswith(".ome.tif"):
        return ".ome.tif"
    elif file_path.name.endswith(".mrc.gz"):
        return ".mrc.gz"
    elif file_path.name.endswith(".map.gz"):
        return ".map.gz"
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
    file_dict = {}
    for file in files:
        if file.is_file() \
                and get_ext(file_path) == get_ext(file) \
                and get_sequence_name(file_path) == get_sequence_name(file):
            file_dict[get_sequence_index(file)] = file

    for key in file_dict.copy().keys():
        if not file_dict.get(key+1) \
                and not file_dict.get(key-1):
            del file_dict[key]

    file_dict = dict(sorted(file_dict.items()))
    sequence = [str(f) for f in file_dict.values()]

    if len(sequence) == 0:
        sequence = [str(file_path)]

    return sequence


def parse_volumetric_data(filepath: str, series_id="", progress_callback=None):
    """Parse any volumetric data to numpy with shap (T,X,Y,Z,C)

    Args:
        filepath (str): file path
        series_id (str, optional): DICOM series id. Defaults to "".

    Returns:
        _type_: _description_
    """
    ext = get_ext(filepath)

    if progress_callback:
        progressing = progress_callback(0, "Reading the Data...")
        if not progressing:
            raise CancelledByUser

    is_sequence = False
    if ext in SEQUENCE_EXTS:
        sequence = collect_sequence(filepath)
        if len(sequence) > 1:
            is_sequence = True

    volume = None

    # Parsing with mrcfile
    if volume is None and ext in MRC_EXTS and not is_sequence:
        print("Parsing with mrcfile...")
        # TODO: much to do with mrc
        with mrcfile.open(filepath) as mrc:
            volume = mrc.data
            # mrc.print_header()
            # print(volume.shape)
            # print(mrc.voxel_size)

            if mrc.is_single_image():
                volume = np.expand_dims(volume, axis=0)  # expend frame
                volume = np.expand_dims(volume, axis=-1)  # expend Z
                volume = np.expand_dims(volume, axis=-1)  # expend channel

            elif mrc.is_image_stack():
                volume = np.expand_dims(volume, axis=-1)  # expend Z
                volume = np.expand_dims(volume, axis=-1)  # expend channel

            elif mrc.is_volume():
                volume = np.expand_dims(volume, axis=0)  # expend frame
                volume = np.expand_dims(volume, axis=-1)  # expend channel

            elif mrc.is_volume_stack():
                volume = np.expand_dims(volume, axis=-1)  # expend channel
            name = Path(filepath).name.removesuffix(ext).replace(" ", "-")
            shape = volume.shape[1:4]
            spacing = (mrc.voxel_size.x, mrc.voxel_size.y, mrc.voxel_size.z)

            meta = {
                "name": name,
                "description": "",
                "shape": shape,
                "spacing": spacing,
                "origin": (0, 0, 0),
                "direction": (1, 0, 0, 0, 1, 0, 0, 0, 1),
                "frame_count": volume.shape[0],
                "channel_count": volume.shape[-1],
                "is_oriented": False
            }

    # Parsing with OMETIFFReader
    if volume is None and ext in OME_EXTS and not is_sequence:
        print("Parsing with OMETIFFReader...")
        reader = OMETIFFReader(fpath=filepath)
        ome_volume, metadata, xml_metadata = reader.read()

        if progress_callback:
            progressing = progress_callback(0.5, "Transpose to 'TXYZC'...")
            if not progressing:
                raise CancelledByUser

        try:
            # print(ome_volume.shape)
            # for key in metadata:
            #     print(f"{key},{metadata[key]}")
            ome_order = metadata['DimOrder BF Array']
            if ome_volume.ndim == 2:
                ome_order = ome_order.replace("T", "")\
                    .replace("C", "").replace("Z", "")
                bioxel_order = (ome_order.index('X'),
                                ome_order.index('Y'))
                volume = np.transpose(ome_volume, bioxel_order)
                volume = np.expand_dims(volume, axis=0)  # expend frame
                volume = np.expand_dims(volume, axis=-1)  # expend Z
                volume = np.expand_dims(volume, axis=-1)  # expend channel

            elif ome_volume.ndim == 3:
                # -> XYZC
                ome_order = ome_order.replace("T", "").replace("C", "")
                bioxel_order = (ome_order.index('X'),
                                ome_order.index('Y'),
                                ome_order.index('Z'))
                volume = np.transpose(ome_volume, bioxel_order)
                volume = np.expand_dims(volume, axis=0)  # expend frame
                volume = np.expand_dims(volume, axis=-1)  # expend channel
            elif ome_volume.ndim == 4:
                # -> XYZC
                ome_order = ome_order.replace("T", "")
                bioxel_order = (ome_order.index('X'),
                                ome_order.index('Y'),
                                ome_order.index('Z'),
                                ome_order.index('C'))
                volume = np.transpose(ome_volume, bioxel_order)
                volume = np.expand_dims(volume, axis=0)  # expend frame
            elif ome_volume.ndim == 5:
                # -> TXYZC
                bioxel_order = (ome_order.index('T'),
                                ome_order.index('X'),
                                ome_order.index('Y'),
                                ome_order.index('Z'),
                                ome_order.index('C'))
                volume = np.transpose(ome_volume, bioxel_order)

            shape = volume.shape[1:4]

            try:
                spacing = (metadata['PhysicalSizeX'],
                           metadata['PhysicalSizeY'],
                           metadata['PhysicalSizeZ'])
            except:
                spacing = (1, 1, 1)

            name = Path(filepath).name.removesuffix(ext).replace(" ", "-")
            meta = {
                "name": name,
                "description": "",
                "shape": shape,
                "spacing": spacing,
                "origin": (0, 0, 0),
                "direction": (1, 0, 0, 0, 1, 0, 0, 0, 1),
                "frame_count": volume.shape[0],
                "channel_count": volume.shape[-1],
                "is_oriented": False
            }
        except:
            ...

    # Parsing with SimpleITK
    if volume is None:
        print("Parsing with SimpleITK...")
        if ext in DICOM_EXTS:
            dir_path = Path(filepath).resolve().parent
            reader = sitk.ImageSeriesReader()
            reader.MetaDataDictionaryArrayUpdateOn()
            reader.LoadPrivateTagsOn()
            series_files = reader.GetGDCMSeriesFileNames(
                str(dir_path), series_id)
            reader.SetFileNames(series_files)

            itk_volume = reader.Execute()
            # for k in reader.GetMetaDataKeys(0):
            #     v = reader.GetMetaData(0, k)
            #     print(f'({k}) = = "{v}"')

            def get_meta(key):
                try:
                    stirng = reader.GetMetaData(0, key).removesuffix(" ")
                    if stirng in ["No study description",
                                  "No series description"]:
                        return None
                    else:
                        return stirng
                except:
                    return None

            study_description = get_meta("0008|1030")
            series_description = get_meta("0008|103e")
            series_modality = get_meta("0008|0060")

            name = study_description or dir_path.name
            if series_description and series_modality:
                description = f"{series_description}-{series_modality}"
            elif series_description:
                description = series_description
            elif series_modality:
                description = series_modality
            else:
                description = ""

            name = name.replace(" ", "-")
            description = description.replace(" ", "-")

        elif ext in SEQUENCE_EXTS and is_sequence:
            try:
                itk_volume = sitk.ReadImage(sequence)
                name = get_sequence_name(filepath).replace(" ", "-")
                description = ""
            except RuntimeError as e:
                raise e
        else:
            itk_volume = sitk.ReadImage(filepath)
            name = Path(filepath).name.removesuffix(ext).replace(" ", "-")
            description = ""

        # for key in itk_volume.GetMetaDataKeys():
        #     print(f"{key},{itk_volume.GetMetaData(key)}")

        if progress_callback:
            progressing = progress_callback(0.5, "Transpose to 'TXYZC'...")
            if not progressing:
                raise CancelledByUser

        if itk_volume.GetDimension() == 2:
            volume = sitk.GetArrayFromImage(itk_volume)

            if volume.ndim == 3:
                volume = np.transpose(volume, (1, 0, 2))

                volume = np.expand_dims(volume, axis=-2)  # expend Z
            else:
                volume = np.transpose(volume)
                volume = np.expand_dims(volume, axis=-1)  # expend Z
                volume = np.expand_dims(volume, axis=-1)  # expend channel

            volume = np.expand_dims(volume, axis=0)  # expend frame

            meta = {
                "name": name,
                "description": description,
                "shape": volume.shape[1:4],
                "spacing": (1, 1, 1),
                "origin": (0, 0, 0),
                "direction": (1, 0, 0, 0, 1, 0, 0, 0, 1),
                "frame_count": 1,
                "channel_count": volume.shape[-1],
                "is_oriented": False
            }

        elif itk_volume.GetDimension() == 3:
            itk_volume = sitk.DICOMOrient(itk_volume, 'RAS')

            volume = sitk.GetArrayFromImage(itk_volume)

            # transpose ijk to kji
            if volume.ndim == 4:
                volume = np.transpose(volume, (2, 1, 0, 3))
            else:
                volume = np.transpose(volume)
                volume = np.expand_dims(volume, axis=-1)  # expend channel

            volume = np.expand_dims(volume, axis=0)  # expend frame

            meta = {
                "name": name,
                "description": description,
                "shape": tuple(itk_volume.GetSize()),
                "spacing": tuple(itk_volume.GetSpacing()),
                "origin": tuple(itk_volume.GetOrigin()),
                "direction": tuple(itk_volume.GetDirection()),
                "frame_count": 1,
                "channel_count": volume.shape[-1],
                "is_oriented": True
            }

        elif itk_volume.GetDimension() == 4:
            # FIXME: not sure...
            direction = np.array(itk_volume.GetDirection())
            direction = direction.reshape(3, 3) if itk_volume.GetDimension() == 3 \
                else direction.reshape(4, 4)

            direction = direction[1:, 1:]
            direction = tuple(direction.flatten())

            volume = sitk.GetArrayFromImage(itk_volume)

            if volume.ndim == 5:
                volume = np.transpose(volume, (0, 3, 2, 1, 4))
            else:
                volume = np.transpose(volume, (0, 3, 2, 1))
                volume = np.expand_dims(volume, axis=-1)

            meta = {
                "name": name,
                "description": description,
                "shape": tuple(itk_volume.GetSize()[:3]),
                "spacing": tuple(itk_volume.GetSpacing()[:3]),
                "origin": tuple(itk_volume.GetOrigin()[:3]),
                "direction": direction,
                "frame_count": volume.shape[0],
                "channel_count": volume.shape[-1],
                "is_oriented": False
            }

    return volume, meta
