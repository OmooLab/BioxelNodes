import warnings
import numpy as np
from .. import scipy as ndi
from ._utils import convert_to_float

def _clip_warp_output(input_image, output_image, mode, cval, clip):
    """Clip output image to range of values of input image.

    Note that this function modifies the values of `output_image` in-place
    and it is only modified if ``clip=True``.

    Parameters
    ----------
    input_image : ndarray
        Input image.
    output_image : ndarray
        Output image, which is modified in-place.

    Other parameters
    ----------------
    mode : {'constant', 'edge', 'symmetric', 'reflect', 'wrap'}
        Points outside the boundaries of the input are filled according
        to the given mode.  Modes match the behaviour of `numpy.pad`.
    cval : float
        Used in conjunction with mode 'constant', the value outside
        the image boundaries.
    clip : bool
        Whether to clip the output to the range of values of the input image.
        This is enabled by default, since higher order interpolation may
        produce values outside the given input range.

    """
    if clip:
        min_val = np.min(input_image)
        if np.isnan(min_val):
            # NaNs detected, use NaN-safe min/max
            min_func = np.nanmin
            max_func = np.nanmax
            min_val = min_func(input_image)
        else:
            min_func = np.min
            max_func = np.max
        max_val = max_func(input_image)

        # Check if cval has been used such that it expands the effective input
        # range
        preserve_cval = (
            mode == 'constant'
            and not min_val <= cval <= max_val
            and min_func(output_image) <= cval <= max_func(output_image)
        )

        # expand min/max range to account for cval
        if preserve_cval:
            # cast cval to the same dtype as the input image
            cval = input_image.dtype.type(cval)
            min_val = min(min_val, cval)
            max_val = max(max_val, cval)

        # Convert array-like types to ndarrays (gh-7159)
        min_val, max_val = np.asarray(min_val), np.asarray(max_val)
        np.clip(output_image, min_val, max_val, out=output_image)


def _validate_interpolation_order(image_dtype, order):
    """Validate and return spline interpolation's order.

    Parameters
    ----------
    image_dtype : dtype
        Image dtype.
    order : int, optional
        The order of the spline interpolation. The order has to be in
        the range 0-5. See `skimage.transform.warp` for detail.

    Returns
    -------
    order : int
        if input order is None, returns 0 if image_dtype is bool and 1
        otherwise. Otherwise, image_dtype is checked and input order
        is validated accordingly (order > 0 is not supported for bool
        image dtype)

    """

    if order is None:
        return 0 if image_dtype == bool else 1

    if order < 0 or order > 5:
        raise ValueError(
            "Spline interpolation order has to be in the " "range 0-5.")

    if image_dtype == bool and order != 0:
        raise ValueError(
            "Input image dtype is bool. Interpolation is not defined "
            "with bool data type. Please set order to 0 or explicitly "
            "cast input image to another data type."
        )

    return order


def _preprocess_resize_output_shape(image, output_shape):
    """Validate resize output shape according to input image.

    Parameters
    ----------
    image: ndarray
        Image to be resized.
    output_shape: iterable
        Size of the generated output image `(rows, cols[, ...][, dim])`. If
        `dim` is not provided, the number of channels is preserved.

    Returns
    -------
    image: ndarray
        The input image, but with additional singleton dimensions appended in
        the case where ``len(output_shape) > input.ndim``.
    output_shape: tuple
        The output image converted to tuple.

    Raises
    ------
    ValueError:
        If output_shape length is smaller than the image number of
        dimensions

    Notes
    -----
    The input image is reshaped if its number of dimensions is not
    equal to output_shape_length.

    """
    output_shape = tuple(output_shape)
    output_ndim = len(output_shape)
    input_shape = image.shape
    if output_ndim > image.ndim:
        # append dimensions to input_shape
        input_shape += (1,) * (output_ndim - image.ndim)
        image = np.reshape(image, input_shape)
    elif output_ndim == image.ndim - 1:
        # multichannel case: append shape of last axis
        output_shape = output_shape + (image.shape[-1],)
    elif output_ndim < image.ndim:
        raise ValueError(
            "output_shape length cannot be smaller than the "
            "image number of dimensions"
        )

    return image, output_shape


def _to_ndimage_mode(mode):
    """Convert from `numpy.pad` mode name to the corresponding ndimage mode."""
    mode_translation_dict = dict(
        constant='constant',
        edge='nearest',
        symmetric='reflect',
        reflect='mirror',
        wrap='wrap',
    )
    if mode not in mode_translation_dict:
        raise ValueError(
            f"Unknown mode: '{mode}', or cannot translate mode. The "
            f"mode should be one of 'constant', 'edge', 'symmetric', "
            f"'reflect', or 'wrap'. See the documentation of numpy.pad for "
            f"more info."
        )
    return _fix_ndimage_mode(mode_translation_dict[mode])


def _fix_ndimage_mode(mode):
    # SciPy 1.6.0 introduced grid variants of constant and wrap which
    # have less surprising behavior for images. Use these when available
    grid_modes = {'constant': 'grid-constant', 'wrap': 'grid-wrap'}
    return grid_modes.get(mode, mode)


def resize(
    image,
    output_shape,
    order=None,
    mode='reflect',
    cval=0,
    clip=True,
    preserve_range=False,
    anti_aliasing=None,
    anti_aliasing_sigma=None,
):
    """Resize image to match a certain size.

    Performs interpolation to up-size or down-size N-dimensional images. Note
    that anti-aliasing should be enabled when down-sizing images to avoid
    aliasing artifacts. For downsampling with an integer factor also see
    `skimage.transform.downscale_local_mean`.

    Parameters
    ----------
    image : ndarray
        Input image.
    output_shape : iterable
        Size of the generated output image `(rows, cols[, ...][, dim])`. If
        `dim` is not provided, the number of channels is preserved. In case the
        number of input channels does not equal the number of output channels a
        n-dimensional interpolation is applied.

    Returns
    -------
    resized : ndarray
        Resized version of the input.

    Other parameters
    ----------------
    order : int, optional
        The order of the spline interpolation, default is 0 if
        image.dtype is bool and 1 otherwise. The order has to be in
        the range 0-5. See `skimage.transform.warp` for detail.
    mode : {'constant', 'edge', 'symmetric', 'reflect', 'wrap'}, optional
        Points outside the boundaries of the input are filled according
        to the given mode.  Modes match the behaviour of `numpy.pad`.
    cval : float, optional
        Used in conjunction with mode 'constant', the value outside
        the image boundaries.
    clip : bool, optional
        Whether to clip the output to the range of values of the input image.
        This is enabled by default, since higher order interpolation may
        produce values outside the given input range.
    preserve_range : bool, optional
        Whether to keep the original range of values. Otherwise, the input
        image is converted according to the conventions of `img_as_float`.
        Also see https://scikit-image.org/docs/dev/user_guide/data_types.html
    anti_aliasing : bool, optional
        Whether to apply a Gaussian filter to smooth the image prior
        to downsampling. It is crucial to filter when downsampling
        the image to avoid aliasing artifacts. If not specified, it is set to
        True when downsampling an image whose data type is not bool.
        It is also set to False when using nearest neighbor interpolation
        (``order`` == 0) with integer input data type.
    anti_aliasing_sigma : {float, tuple of floats}, optional
        Standard deviation for Gaussian filtering used when anti-aliasing.
        By default, this value is chosen as (s - 1) / 2 where s is the
        downsampling factor, where s > 1. For the up-size case, s < 1, no
        anti-aliasing is performed prior to rescaling.

    Notes
    -----
    Modes 'reflect' and 'symmetric' are similar, but differ in whether the edge
    pixels are duplicated during the reflection.  As an example, if an array
    has values [0, 1, 2] and was padded to the right by four values using
    symmetric, the result would be [0, 1, 2, 2, 1, 0, 0], while for reflect it
    would be [0, 1, 2, 1, 0, 1, 2].

    Examples
    --------
    >>> from skimage import data
    >>> from skimage.transform import resize
    >>> image = data.camera()
    >>> resize(image, (100, 100)).shape
    (100, 100)

    """

    image, output_shape = _preprocess_resize_output_shape(image, output_shape)
    input_shape = image.shape
    input_type = image.dtype

    if input_type == np.float16:
        image = image.astype(np.float32)

    if anti_aliasing is None:
        anti_aliasing = (
            not input_type == bool
            and not (np.issubdtype(input_type, np.integer) and order == 0)
            and any(x < y for x, y in zip(output_shape, input_shape))
        )

    if input_type == bool and anti_aliasing:
        raise ValueError("anti_aliasing must be False for boolean images")

    factors = np.divide(input_shape, output_shape)
    order = _validate_interpolation_order(input_type, order)
    if order > 0:
        image = convert_to_float(image, preserve_range)

    # Translate modes used by np.pad to those used by scipy.ndimage
    ndi_mode = _to_ndimage_mode(mode)
    if anti_aliasing:
        if anti_aliasing_sigma is None:
            anti_aliasing_sigma = np.maximum(0, (factors - 1) / 2)
        else:
            anti_aliasing_sigma = np.atleast_1d(anti_aliasing_sigma) * np.ones_like(
                factors
            )
            if np.any(anti_aliasing_sigma < 0):
                raise ValueError(
                    "Anti-aliasing standard deviation must be "
                    "greater than or equal to zero"
                )
            elif np.any((anti_aliasing_sigma > 0) & (factors <= 1)):
                warnings.warn(
                    "Anti-aliasing standard deviation greater than zero but "
                    "not down-sampling along all axes",
                    stacklevel=2
                )
        filtered = ndi.gaussian_filter(
            image, anti_aliasing_sigma, cval=cval, mode=ndi_mode
        )
    else:
        filtered = image

    zoom_factors = [1 / f for f in factors]
    out = ndi.zoom(
        filtered, zoom_factors, order=order, mode=ndi_mode, cval=cval, grid_mode=True
    )

    _clip_warp_output(image, out, mode, cval, clip)

    return out
