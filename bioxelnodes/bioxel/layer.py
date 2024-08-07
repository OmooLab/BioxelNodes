import copy
import numpy as np

from . import scipy
from . import skimage as ski
from . import scipy as ndi

# 3rd-party
import transforms3d

# TODO: turn to dataclasses


class Layer():
    def __init__(self,
                 data: np.ndarray,
                 name: str,
                 kind="scalar",
                 affine=np.identity(4)) -> None:
        if data.ndim != 5:
            raise Exception("Data shape order should be TXYZC")

        affine = np.array(affine)
        if affine.shape != (4, 4):
            raise Exception("affine shape should be (4,4)")

        self.data = data
        self.name = name
        self.kind = kind
        self.affine = affine

    @property
    def bioxel_size(self):
        t, r, z, s = transforms3d.affines.decompose44(self.affine)
        return z.tolist()

    @property
    def shape(self):
        return self.data.shape[1:4]

    @property
    def dtype(self):
        return self.data.dtype

    @property
    def origin(self):
        t, r, z, s = transforms3d.affines.decompose44(self.affine)
        return t.tolist()

    @property
    def euler(self):
        t, r, z, s = transforms3d.affines.decompose44(self.affine)
        return list(transforms3d.euler.mat2euler(r))

    @property
    def min(self):
        return float(np.min(self.data))

    @property
    def frame_count(self):
        return self.data.shape[0]

    @property
    def channel_count(self):
        return self.data.shape[-1]

    @property
    def max(self):
        return float(np.max(self.data))

    def copy(self):
        return copy.deepcopy(self)

    def fill(self, value: float, mask: np.ndarray):
        mask_frames = ()
        if mask.ndim == 4:
            if mask.shape[0] != self.frame_count:
                raise Exception("Mask frame count is not same as ")
            for f in range(self.frame_count):
                mask_frame = mask[f, :, :, :]
                mask_frame = scipy.minimum_filter(
                    mask_frame.astype(np.float32), size=3)
                # mask_frame = scipy.median_filter(
                #     mask_frame.astype(np.float32), size=2)
                mask_frames += (mask_frame,)
        elif mask.ndim == 3:
            for f in range(self.frame_count):
                mask_frame = mask[:, :, :]
                mask_frame = scipy.minimum_filter(
                    mask_frame.astype(np.float32), size=3)
                # mask_frame = scipy.median_filter(
                #     mask_frame.astype(np.float32), size=2)
                mask_frames += (mask_frame,)
        else:
            raise Exception("Mask shape order should be TXYZ or XYZ")

        _mask = np.stack(mask_frames)
        _mask = np.expand_dims(_mask, axis=-1)
        self.data = _mask * value + (1-_mask) * self.data

    def resize(self, shape: tuple, progress_callback=None):
        if len(shape) != 3:
            raise Exception("Shape must be 3 dim")

        data = self.data
        order = 0 if self.dtype == bool else 1

        # TXYZC > TXYZ
        if self.kind in ['label', 'scalar']:
            data = np.amax(data, -1)

        # if self.kind in ['scalar']:
        #     dtype = data.dtype
            # data = data.astype(np.float32)

        data_frames = ()
        for f in range(self.frame_count):
            if progress_callback:
                progress_callback(f, self.frame_count)

            # frame = ski.resize(data[f, :, :, :],
            #                    shape,
            #                    preserve_range=True,
            #                    anti_aliasing=data.dtype.kind != "b")

            factors = np.divide(self.shape, shape)
            zoom_factors = [1 / f for f in factors]
            frame = ndi.zoom(data[f, :, :, :],
                             zoom_factors,
                             order=order)

            data_frames += (frame,)

        data = np.stack(data_frames)

        # if self.kind in ['scalar']:
        #     data = data.astype(dtype)

        # TXYZ > TXYZC
        if self.kind in ['label', 'scalar']:
            data = np.expand_dims(data, axis=-1)  # expend channel

        self.data = data
