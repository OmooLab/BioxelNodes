from pathlib import Path
import numpy as np
from .layer import Layer

# 3rd-party
import SimpleITK as sitk
from pyometiff import OMETIFFReader
import mrcfile
import transforms3d


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
                '.mrc', '.mrc.gz', '.map', '.map.gz',
                '.gz']

OME_EXTS = ['.ome.tiff', '.ome.tif',
            '.tif', '.TIF', '.tiff', '.TIFF']

MRC_EXTS = ['.mrc', '.mrc.gz', '.map', '.map.gz']

DICOM_EXTS = ['', '.dcm', '.DCM', '.DICOM', '.ima', '.IMA']

SEQUENCE_EXTS = ['.bmp', '.BMP',
                 '.jpg', '.JPG', '.jpeg', '.JPEG',
                 '.tif', '.TIF', '.tiff', '.TIFF',
                 '.png', '.PNG']


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
        return filepath.suffix


def get_file_name(filepath: Path):
    ext = get_ext(filepath)
    return filepath.name.removesuffix(ext).replace(" ", "-")


def get_file_index(filepath: Path):
    name = get_file_name(filepath)
    digits = ""

    # Iterate through the characters in reverse order
    started = False
    for char in name[::-1]:
        if char.isdigit():
            started = True
            # If the character is a digit, add it to the digits string
            digits += char
        else:
            if started:
                # If a non-digit character is encountered, stop the loop
                break

    # Reverse the digits string to get the correct order
    last_number = digits[::-1]

    return int(last_number) if last_number != "" else 0


def get_sequence_name(filepath: Path) -> str:
    name = get_file_name(filepath)
    index = get_file_index(filepath)
    return name.removesuffix(str(index))


def collect_sequence(filepath: Path):
    file_dict = {}
    for f in filepath.parent.iterdir():
        if f.is_file() \
                and get_ext(filepath) == get_ext(f) \
                and get_sequence_name(filepath) == get_sequence_name(f):
            index = get_file_index(f)
            file_dict[index] = f

    for key in file_dict.copy().keys():
        if not file_dict.get(key+1) \
                and not file_dict.get(key-1):
            del file_dict[key]

    file_dict = dict(sorted(file_dict.items()))
    sequence = [str(f) for f in file_dict.values()]

    if len(sequence) == 0:
        sequence = [str(filepath)]

    return sequence


def parse_volumetric_data(data_file: str, series_id="", progress_callback=None) -> Layer:
    """Parse any volumetric data to numpy with shap (T,X,Y,Z,C)

    Args:
        data_file (str): file path
        series_id (str, optional): DICOM series id. Defaults to "".

    Returns:
        _type_: _description_
    """

    data_path = Path(data_file).resolve()
    ext = get_ext(data_path)

    if progress_callback:
        progress_callback(0, "Reading the Data...")

    is_sequence = False
    if ext in SEQUENCE_EXTS:
        sequence = collect_sequence(data_path)
        if len(sequence) > 1:
            is_sequence = True

    data = None
    name = "",
    description = ""
    affine = np.identity(4)
    spacing = (1, 1, 1)
    origin = (0, 0, 0)
    direction = (1, 0, 0, 0, 1, 0, 0, 0, 1)

    # Parsing with mrcfile
    if data is None and ext in MRC_EXTS and not is_sequence:
        print("Parsing with mrcfile...")
        # TODO: much to do with mrc
        with mrcfile.open(data_path, 'r') as mrc:
            data = mrc.data
            # mrc.print_header()
            # print(data.shape)
            # print(mrc.voxel_size)

            if mrc.is_single_image():
                data = np.expand_dims(data, axis=0)  # expend frame
                data = np.expand_dims(data, axis=-1)  # expend Z
                data = np.expand_dims(data, axis=-1)  # expend channel

            elif mrc.is_image_stack():
                data = np.expand_dims(data, axis=-1)  # expend Z
                data = np.expand_dims(data, axis=-1)  # expend channel

            elif mrc.is_volume():
                data = np.expand_dims(data, axis=0)  # expend frame
                data = np.expand_dims(data, axis=-1)  # expend channel

            elif mrc.is_volume_stack():
                data = np.expand_dims(data, axis=-1)  # expend channel

            name = get_file_name(data_path)
            spacing = (mrc.voxel_size.x,
                       mrc.voxel_size.y,
                       mrc.voxel_size.z)

    # Parsing with OMETIFFReader
    if data is None and ext in OME_EXTS and not is_sequence:
        print("Parsing with OMETIFFReader...")
        reader = OMETIFFReader(fpath=data_path)
        ome_image, metadata, xml_metadata = reader.read()

        # TODO: some old bio-format tiff the header is not the same.
        if progress_callback:
            progress_callback(0.5, "Transpose to 'TXYZC'...")

        try:
            # print(ome_image.shape)
            # for key in metadata:
            #     print(f"{key},{metadata[key]}")
            ome_order = metadata['DimOrder BF Array']
            if ome_image.ndim == 2:
                ome_order = ome_order.replace("T", "")\
                    .replace("C", "").replace("Z", "")
                bioxel_order = (ome_order.index('X'),
                                ome_order.index('Y'))
                data = np.transpose(ome_image, bioxel_order)
                data = np.expand_dims(data, axis=0)  # expend frame
                data = np.expand_dims(data, axis=-1)  # expend Z
                data = np.expand_dims(data, axis=-1)  # expend channel

            elif ome_image.ndim == 3:
                # -> XYZC
                ome_order = ome_order.replace("T", "").replace("C", "")
                bioxel_order = (ome_order.index('X'),
                                ome_order.index('Y'),
                                ome_order.index('Z'))
                data = np.transpose(ome_image, bioxel_order)
                data = np.expand_dims(data, axis=0)  # expend frame
                data = np.expand_dims(data, axis=-1)  # expend channel
            elif ome_image.ndim == 4:
                # -> XYZC
                ome_order = ome_order.replace("T", "")
                bioxel_order = (ome_order.index('X'),
                                ome_order.index('Y'),
                                ome_order.index('Z'),
                                ome_order.index('C'))
                data = np.transpose(ome_image, bioxel_order)
                data = np.expand_dims(data, axis=0)  # expend frame
            elif ome_image.ndim == 5:
                # -> TXYZC
                bioxel_order = (ome_order.index('T'),
                                ome_order.index('X'),
                                ome_order.index('Y'),
                                ome_order.index('Z'),
                                ome_order.index('C'))
                data = np.transpose(ome_image, bioxel_order)

            try:
                spacing = (metadata['PhysicalSizeX'],
                           metadata['PhysicalSizeY'],
                           metadata['PhysicalSizeZ'])
            except:
                ...

            name = get_file_name(data_path)
        except:
            ...

    # Parsing with SimpleITK
    if data is None:
        print("Parsing with SimpleITK...")
        if ext in DICOM_EXTS:
            data_dirpath = data_path.parent
            reader = sitk.ImageSeriesReader()
            reader.MetaDataDictionaryArrayUpdateOn()
            reader.LoadPrivateTagsOn()
            series_files = reader.GetGDCMSeriesFileNames(
                str(data_dirpath), series_id)
            reader.SetFileNames(series_files)

            itk_image = reader.Execute()
            # for k in reader.GetMetaDataKeys(0):
            #     v = reader.GetMetaData(0, k)
            #     print(f'({k}) = = "{v}"')

            def get_meta(key):
                try:
                    stirng = reader.GetMetaData(0, key).removesuffix(" ")
                    if stirng in ["No study description",
                                  "No series description",
                                  ""]:
                        return None
                    else:
                        return stirng
                except:
                    return None

            study_description = get_meta("0008|1030")
            series_description = get_meta("0008|103e")
            series_modality = get_meta("0008|0060")

            name = study_description or data_dirpath.name
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
            itk_image = sitk.ReadImage(sequence)
            name = get_sequence_name(data_path)
        else:
            itk_image = sitk.ReadImage(data_path)
            name = get_file_name(data_path)

        # for key in itk_image.GetMetaDataKeys():
        #     print(f"{key},{itk_image.GetMetaData(key)}")

        if progress_callback:
            progress_callback(0.5, "Transpose to 'TXYZC'...")

        if itk_image.GetDimension() == 2:

            data = sitk.GetArrayFromImage(itk_image)

            if data.ndim == 3:
                data = np.transpose(data, (1, 0, 2))

                data = np.expand_dims(data, axis=-2)  # expend Z
            else:
                data = np.transpose(data)
                data = np.expand_dims(data, axis=-1)  # expend Z
                data = np.expand_dims(data, axis=-1)  # expend channel

            data = np.expand_dims(data, axis=0)  # expend frame

        elif itk_image.GetDimension() == 3:
            if ext not in SEQUENCE_EXTS:
                itk_image = sitk.DICOMOrient(itk_image, 'RAS')
                # After sitk.DICOMOrient(), origin and direction will also orient base on LPS
                # so we need to convert them into RAS
                # affine = axis_conversion(from_forward='-Z',
                #                          from_up='-Y',
                #                          to_forward='-Z',
                #                          to_up='Y').to_4x4()

                affine = np.array([[-1.0000,  0.0000, 0.0000, 0.0000],
                                   [0.0000, -1.0000, 0.0000, 0.0000],
                                   [0.0000,  0.0000, 1.0000, 0.0000],
                                   [0.0000,  0.0000, 0.0000, 1.0000]])

            spacing = tuple(itk_image.GetSpacing())
            origin = tuple(itk_image.GetOrigin())
            direction = tuple(itk_image.GetDirection())

            data = sitk.GetArrayFromImage(itk_image)
            # transpose ijk to kji
            if data.ndim == 4:
                data = np.transpose(data, (2, 1, 0, 3))
            else:
                data = np.transpose(data)
                data = np.expand_dims(data, axis=-1)  # expend channel

            data = np.expand_dims(data, axis=0)  # expend frame

        elif itk_image.GetDimension() == 4:

            spacing = tuple(itk_image.GetSpacing()[:3])
            origin = tuple(itk_image.GetOrigin()[:3])
            # FIXME: not sure...
            direction = np.array(itk_image.GetDirection())
            direction = direction.reshape(3, 3) if itk_image.GetDimension() == 3 \
                else direction.reshape(4, 4)

            direction = direction[1:, 1:]
            direction = tuple(direction.flatten())

            data = sitk.GetArrayFromImage(itk_image)

            if data.ndim == 5:
                data = np.transpose(data, (0, 3, 2, 1, 4))
            else:
                data = np.transpose(data, (0, 3, 2, 1))
                data = np.expand_dims(data, axis=-1)

        if itk_image.GetDimension() > 5:
            raise Exception

    t = origin
    r = np.array(direction).reshape((3, 3))
    affine = np.dot(affine,
                    transforms3d.affines.compose(t, r, [1, 1, 1]))

    meta = {
        "name": name,
        "description": description,
        "spacing": spacing,
        "affine": affine,
        "xyz_shape": data.shape[1:4],
        "frame_count": data.shape[0],
        "channel_count": data.shape[-1],
    }

    return data, meta
