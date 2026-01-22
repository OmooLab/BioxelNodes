"""
Unit tests for bioxel module.

Tests cover:
- Data class functionality
- Parsing NRRD and DICOM formats
- Layer creation and transformation
- Utility functions
"""

from bioxelnodes.bioxel import (
    Data,
    read,
    read_meta,
    calc_layer_shape,
    calc_layer_size,
    Layer,
)
import pytest
import numpy as np
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# Test data files
NRRD_FILE = Path(__file__).parent / "data/VHP_M.nrrd"
DICOM_FILE = Path(__file__).parent / "data/VHP_M_CT_Head/IM000001.dcm"
DICOM_DIR = Path(__file__).parent / "data/VHP_M_CT_Head/"


class TestDataClass:
    """Test Data class initialization and properties"""

    def test_data_initialization(self):
        """Test basic Data initialization with NRRD"""
        data = Data(filepath=str(NRRD_FILE), series_id="")

        assert data.filepath is not None
        assert data.series_id == ""
        assert data._data is None
        assert data._meta is None

    def test_read_meta_nrrd(self):
        """Test reading only meta from NRRD file"""
        data_obj = read_meta(str(NRRD_FILE))

        assert data_obj._data is None
        assert data_obj._meta is not None
        assert "name" in data_obj.meta
        assert "spacing" in data_obj.meta
        assert "affine" in data_obj.meta
        assert "xyz_shape" in data_obj.meta
        assert "frame_count" in data_obj.meta
        assert "channel_count" in data_obj.meta
        assert "dtype" in data_obj.meta

    def test_read_meta_dicom(self):
        """Test reading only meta from DICOM file"""
        data_obj = read_meta(str(DICOM_FILE), series_id="")

        assert data_obj._data is None
        assert data_obj._meta is not None
        assert "name" in data_obj.meta

    def test_read_full_data_nrrd(self):
        """Test reading full NRRD data"""
        data_obj = read(str(NRRD_FILE))

        assert data_obj._data is not None
        assert data_obj._meta is not None
        assert isinstance(data_obj.data, np.ndarray)
        assert data_obj.data.ndim == 5

    def test_read_full_data_dicom(self):
        """Test reading full DICOM data"""
        data_obj = read(str(DICOM_FILE), series_id="")

        assert data_obj._data is not None
        assert data_obj._meta is not None
        assert isinstance(data_obj.data, np.ndarray)

    def test_data_properties_nrrd(self):
        """Test Data property accessors"""
        data_obj = read(str(NRRD_FILE))

        assert hasattr(data_obj, "name")
        assert hasattr(data_obj, "description")
        assert hasattr(data_obj, "shape")
        assert hasattr(data_obj, "xyz_shape")
        assert hasattr(data_obj, "spacing")
        assert hasattr(data_obj, "affine")
        assert hasattr(data_obj, "frame_count")
        assert hasattr(data_obj, "channel_count")
        assert hasattr(data_obj, "dtype")

        assert isinstance(data_obj.shape, tuple)
        assert isinstance(data_obj.xyz_shape, tuple)
        assert isinstance(data_obj.spacing, tuple)
        assert isinstance(data_obj.affine, np.ndarray)
        assert isinstance(data_obj.dtype, np.dtype)

    def test_data_lazy_loading(self):
        """Test lazy loading behavior"""
        data_obj = Data(filepath=str(NRRD_FILE), series_id="")

        assert data_obj.is_loaded() is False

        data_obj.load_meta()
        assert data_obj._data is None
        assert data_obj._meta is not None

        data_obj.load_data()
        assert data_obj._data is not None
        assert data_obj.is_loaded() is True

    def test_shape_property(self):
        """Test shape property returns TXYZC format"""
        data_obj = read(str(NRRD_FILE))

        shape = data_obj.shape
        assert len(shape) == 5
        assert shape[0] == data_obj.meta["frame_count"]
        assert shape[1:4] == data_obj.meta["xyz_shape"]
        assert shape[4] == data_obj.meta["channel_count"]

    def test_load_meta_method(self):
        """Test load_meta() method exists and works"""
        data_obj = Data(filepath=str(NRRD_FILE), series_id="")

        assert hasattr(data_obj, "load_meta")

        data_obj.load_meta()
        assert data_obj._meta is not None
        assert data_obj._data is None


class TestDataToLayers:
    """Test Data.to_layers() method"""

    def test_to_layers_dicom_scalar(self):
        """Test converting DICOM data to scalar layers"""
        data_obj = read(str(DICOM_FILE), series_id="")

        layers = data_obj.to_layers(kind="scalar", bioxel_size=2.0)

        assert len(layers) == 1
        assert layers[0].kind == "scalar"
        assert isinstance(layers[0], Layer)

    def test_to_layers_nrrd_scalar(self):
        """Test converting NRRD data to scalar layers"""
        data_obj = read(str(NRRD_FILE))

        layers = data_obj.to_layers(kind="scalar", bioxel_size=2.0)

        assert len(layers) == 1
        assert layers[0].kind == "scalar"
        assert isinstance(layers[0], Layer)

    def test_to_layers_with_remap(self):
        """Test data remapping"""
        data_obj = read(str(NRRD_FILE))

        layers = data_obj.to_layers(kind="scalar", bioxel_size=2.0, remap=True)

        assert len(layers) == 1
        assert layers[0].data.dtype == np.float32
        assert np.all(layers[0].data >= 0)
        assert np.all(layers[0].data <= 1)

    def test_to_layers_with_bioxel_size(self):
        """Test with different bioxel sizes"""
        data_obj = read(str(NRRD_FILE))

        layers_1x = data_obj.to_layers(kind="scalar", bioxel_size=1.0)
        layers_2x = data_obj.to_layers(kind="scalar", bioxel_size=2.0)

        assert len(layers_1x) == 1
        assert len(layers_2x) == 1

        # Larger bioxel size means smaller layer
        shape_1x = layers_1x[0].shape
        shape_2x = layers_2x[0].shape
        assert shape_2x[0] <= shape_1x[0]
        assert shape_2x[1] <= shape_1x[1]
        assert shape_2x[2] <= shape_1x[2]

    def test_to_layers_with_smooth(self):
        """Test with smoothing parameter"""
        data_obj = read(str(NRRD_FILE))

        layers = data_obj.to_layers(kind="scalar", bioxel_size=2.0, smooth=1)

        assert len(layers) == 1
        assert isinstance(layers[0], Layer)

    def test_to_layers_frame_source_first_frame(self):
        """Test frame_source = '-1' (first frame only)"""
        data_obj = read(str(NRRD_FILE))

        layers = data_obj.to_layers(kind="scalar", bioxel_size=2.0, frame_source="-1")

        assert len(layers) == 1
        assert layers[0].frame_count == 1


class TestUtilityFunctions:
    """Test utility functions"""

    def test_calc_layer_shape(self):
        """Test layer shape calculation"""
        shape = calc_layer_shape(
            bioxel_size=1.0, orig_shape=(100, 100, 100), orig_spacing=(1.0, 1.0, 1.0)
        )

        assert len(shape) == 3
        assert shape[0] == 100
        assert shape[1] == 100
        assert shape[2] == 100

    def test_calc_layer_shape_small_bioxel(self):
        """Test layer shape with small bioxel size"""
        shape = calc_layer_shape(
            bioxel_size=2.0, orig_shape=(100, 100, 100), orig_spacing=(1.0, 1.0, 1.0)
        )

        assert len(shape) == 3
        assert shape[0] == 50
        assert shape[1] == 50
        assert shape[2] == 50

    def test_calc_layer_shape_minimum(self):
        """Test layer shape doesn't go below 1"""
        shape = calc_layer_shape(
            bioxel_size=100.0, orig_shape=(100, 100, 100), orig_spacing=(1.0, 1.0, 1.0)
        )

        assert shape == (1, 1, 1)

    def test_calc_layer_size(self):
        """Test layer size calculation"""
        size = calc_layer_size(shape=(100, 100, 100), bioxel_size=1.0, scale=1.0)

        assert len(size) == 3
        assert size[0] == 100.0
        assert size[1] == 100.0
        assert size[2] == 100.0

    def test_calc_layer_size_with_scale(self):
        """Test layer size with scale factor"""
        size = calc_layer_size(shape=(100, 100, 100), bioxel_size=1.0, scale=0.01)

        assert len(size) == 3
        assert size[0] == 1.0
        assert size[1] == 1.0
        assert size[2] == 1.0


class TestLayerClass:
    """Test Layer class functionality"""

    def test_layer_initialization(self):
        """Test Layer initialization"""
        data = np.random.rand(1, 8, 8, 8, 1).astype(np.float32)
        layer = Layer(data=data, name="test_layer", kind="scalar")

        assert layer.name == "test_layer"
        assert layer.kind == "scalar"
        assert np.array_equal(layer.data, data)

    def test_layer_properties(self):
        """Test Layer property accessors"""
        data = np.random.rand(1, 8, 8, 8, 1).astype(np.float32)
        layer = Layer(
            data=data, name="test_layer", kind="scalar", affine=np.identity(4)
        )

        assert hasattr(layer, "bioxel_size")
        assert hasattr(layer, "shape")
        assert hasattr(layer, "dtype")
        assert hasattr(layer, "origin")
        assert hasattr(layer, "euler")
        assert hasattr(layer, "frame_count")
        assert hasattr(layer, "channel_count")
        assert hasattr(layer, "min")
        assert hasattr(layer, "max")

    def test_layer_shape_property(self):
        """Test layer shape returns XYZ (not TXYZC)"""
        data = np.random.rand(1, 8, 8, 8, 1).astype(np.float32)
        layer = Layer(data=data, name="test", kind="scalar")

        shape = layer.shape
        assert len(shape) == 3
        assert shape[0] == 8
        assert shape[1] == 8
        assert shape[2] == 8

    def test_layer_affine_property(self):
        """Test affine transformation matrix"""
        data = np.random.rand(1, 8, 8, 8, 1).astype(np.float32)
        affine = np.array(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )
        layer = Layer(data=data, name="test", kind="scalar", affine=affine)

        result_affine = layer.affine
        assert result_affine.shape == (4, 4)
        assert np.allclose(result_affine, affine)

    def test_layer_min_max(self):
        """Test layer min/max properties"""
        data = np.random.rand(1, 8, 8, 8, 1).astype(np.float32)
        layer = Layer(data=data, name="test", kind="scalar")

        assert isinstance(layer.min, float)
        assert isinstance(layer.max, float)
        assert layer.min <= layer.max

    def test_layer_copy(self):
        """Test layer deep copy"""
        data = np.random.rand(1, 8, 8, 8, 1).astype(np.float32)
        layer = Layer(data=data, name="test", kind="scalar")
        layer_copy = layer.copy()

        assert layer_copy.name == layer.name
        assert layer_copy.kind == layer.kind
        assert np.array_equal(layer_copy.data, layer.data)

        assert layer_copy is not layer
        layer_copy.data[0, 0, 0, 0, 0] = 999.0
        assert layer.data[0, 0, 0, 0, 0] != 999.0

    def test_layer_invalid_data_shape(self):
        """Test Layer raises error for invalid data shape"""
        data = np.random.rand(8, 8, 8).astype(np.float32)

        with pytest.raises(Exception):
            Layer(data=data, name="test", kind="scalar")

    def test_layer_invalid_affine_shape(self):
        """Test Layer raises error for invalid affine shape"""
        data = np.random.rand(1, 8, 8, 8, 1).astype(np.float32)
        affine = np.identity(3)

        with pytest.raises(Exception):
            Layer(data=data, name="test", kind="scalar", affine=affine)


class TestConstants:
    """Test module constants"""

    def test_support_exts_exists(self):
        """Test SUPPORT_EXTS constant"""
        from bioxelnodes.bioxel import SUPPORT_EXTS

        assert isinstance(SUPPORT_EXTS, list)
        assert len(SUPPORT_EXTS) > 0
        assert ".h5" in SUPPORT_EXTS
        assert ".nrrd" in SUPPORT_EXTS
        assert ".nii.gz" in SUPPORT_EXTS
        assert ".dcm" in SUPPORT_EXTS

    def test_dicom_exts_exists(self):
        """Test DICOM_EXTS constant"""
        from bioxelnodes.bioxel import DICOM_EXTS

        assert isinstance(DICOM_EXTS, list)
        assert "" in DICOM_EXTS
        assert ".dcm" in DICOM_EXTS
        assert ".DCM" in DICOM_EXTS

    def test_ome_exts_exists(self):
        """Test OME_EXTS constant"""
        from bioxelnodes.bioxel import OME_EXTS

        assert isinstance(OME_EXTS, list)
        assert ".tiff" in OME_EXTS
        assert ".ome.tiff" in OME_EXTS

    def test_mrc_exts_exists(self):
        """Test MRC_EXTS constant"""
        from bioxelnodes.bioxel import MRC_EXTS

        assert isinstance(MRC_EXTS, list)
        assert ".mrc" in MRC_EXTS


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_nonexistent_file(self):
        """Test handling of nonexistent file"""
        with pytest.raises(FileNotFoundError):
            data_obj = read("/nonexistent/file.nii.gz", "")

    def test_frame_count_property_multiframe(self):
        """Test frame_count property for multi-frame data"""
        data_obj = read(str(NRRD_FILE))

        assert data_obj.frame_count >= 1
        assert data_obj.frame_count == data_obj.meta["frame_count"]

    def test_channel_count_property(self):
        """Test channel_count property"""
        data_obj = read(str(NRRD_FILE))

        assert data_obj.channel_count >= 1
        assert data_obj.channel_count == data_obj.meta["channel_count"]

    def test_nrrd_format_support(self):
        """Test NRRD format is in supported extensions"""
        from bioxelnodes.bioxel import SUPPORT_EXTS

        assert ".nrrd" in SUPPORT_EXTS

    def test_dicom_format_support(self):
        """Test DICOM format is in supported extensions"""
        from bioxelnodes.bioxel import SUPPORT_EXTS

        assert ".dcm" in SUPPORT_EXTS
        assert "" in SUPPORT_EXTS


class TestRealDataFiles:
    """Test with real data files"""

    def test_nrrd_file_exists(self):
        """Test NRRD test file exists"""
        assert NRRD_FILE.exists()
        assert NRRD_FILE.is_file()

    def test_dicom_file_exists(self):
        """Test DICOM test file exists"""
        assert DICOM_FILE.exists()
        assert DICOM_FILE.is_file()

    def test_dicom_directory_exists(self):
        """Test DICOM directory exists"""
        assert DICOM_DIR.exists()
        assert DICOM_DIR.is_dir()

    def test_read_nrrd_data(self):
        """Test reading real NRRD data"""
        data_obj = read(str(NRRD_FILE))

        assert data_obj._data is not None
        assert data_obj._meta is not None
        assert isinstance(data_obj.data, np.ndarray)
        assert data_obj.data.size > 0

    def test_read_dicom_data(self):
        """Test reading real DICOM data"""
        data_obj = read(str(DICOM_FILE), series_id="")

        assert data_obj._data is not None
        assert data_obj._meta is not None
        assert isinstance(data_obj.data, np.ndarray)
        assert data_obj.data.size > 0

    def test_nrrd_meta_contains_required_fields(self):
        """Test NRRD meta contains all required fields"""
        data_obj = read(str(NRRD_FILE))
        meta = data_obj.meta

        required_fields = [
            "name",
            "description",
            "spacing",
            "affine",
            "xyz_shape",
            "frame_count",
            "channel_count",
            "dtype",
        ]

        for field in required_fields:
            assert field in meta, f"Meta missing field: {field}"

    def test_dicom_meta_contains_required_fields(self):
        """Test DICOM meta contains all required fields"""
        data_obj = read(str(DICOM_FILE), series_id="")
        meta = data_obj.meta

        required_fields = [
            "name",
            "description",
            "spacing",
            "affine",
            "xyz_shape",
            "frame_count",
            "channel_count",
            "dtype",
        ]

        for field in required_fields:
            assert field in meta, f"Meta missing field: {field}"

    def test_data_to_layers_with_real_nrrd(self):
        """Test to_layers with real NRRD data"""
        data_obj = read(str(NRRD_FILE))

        layers = data_obj.to_layers(kind="scalar", bioxel_size=3.0)

        assert len(layers) > 0
        assert all(isinstance(layer, Layer) for layer in layers)

    def test_data_to_layers_with_real_dicom(self):
        """Test to_layers with real DICOM data"""
        data_obj = read(str(DICOM_FILE), series_id="")

        layers = data_obj.to_layers(kind="scalar", bioxel_size=3.0)

        assert len(layers) > 0
        assert all(isinstance(layer, Layer) for layer in layers)

    def test_nrrd_spacing_values(self):
        """Test NRRD spacing values are reasonable"""
        data_obj = read(str(NRRD_FILE))
        spacing = data_obj.spacing

        assert len(spacing) == 3
        assert all(s > 0 for s in spacing)

    def test_dicom_spacing_values(self):
        """Test DICOM spacing values are reasonable"""
        data_obj = read(str(DICOM_FILE), series_id="")
        spacing = data_obj.spacing

        assert len(spacing) == 3
        assert all(s > 0 for s in spacing)
