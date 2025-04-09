import numpy as np
import warnings

from . import _ni_support
from . import _nd_image
from ._utils import normalize_axis_index


def _prepad_for_spline_filter(input, mode, cval):
    if mode in ['nearest', 'grid-constant']:
        npad = 12
        if mode == 'grid-constant':
            padded = np.pad(input, npad, mode='constant',
                               constant_values=cval)
        elif mode == 'nearest':
            padded = np.pad(input, npad, mode='edge')
    else:
        # other modes have exact boundary conditions implemented so
        # no prepadding is needed
        npad = 0
        padded = input
    return padded, npad

def spline_filter1d(input, order=3, axis=-1, output=np.float64,
                    mode='mirror'):
    """
    Calculate a 1-D spline filter along the given axis.

    The lines of the array along the given axis are filtered by a
    spline filter. The order of the spline must be >= 2 and <= 5.

    Parameters
    ----------
    %(input)s
    order : int, optional
        The order of the spline, default is 3.
    axis : int, optional
        The axis along which the spline filter is applied. Default is the last
        axis.
    output : ndarray or dtype, optional
        The array in which to place the output, or the dtype of the returned
        array. Default is ``numpy.float64``.
    %(mode_interp_mirror)s

    Returns
    -------
    spline_filter1d : ndarray
        The filtered input.

    See Also
    --------
    spline_filter : Multidimensional spline filter.

    Notes
    -----
    All of the interpolation functions in `ndimage` do spline interpolation of
    the input image. If using B-splines of `order > 1`, the input image
    values have to be converted to B-spline coefficients first, which is
    done by applying this 1-D filter sequentially along all
    axes of the input. All functions that require B-spline coefficients
    will automatically filter their inputs, a behavior controllable with
    the `prefilter` keyword argument. For functions that accept a `mode`
    parameter, the result will only be correct if it matches the `mode`
    used when filtering.

    For complex-valued `input`, this function processes the real and imaginary
    components independently.

    .. versionadded:: 1.6.0
        Complex-valued support added.

    Examples
    --------
    We can filter an image using 1-D spline along the given axis:

    >>> from scipy.ndimage import spline_filter1d
    >>> import numpy as np
    >>> import matplotlib.pyplot as plt
    >>> orig_img = np.eye(20)  # create an image
    >>> orig_img[10, :] = 1.0
    >>> sp_filter_axis_0 = spline_filter1d(orig_img, axis=0)
    >>> sp_filter_axis_1 = spline_filter1d(orig_img, axis=1)
    >>> f, ax = plt.subplots(1, 3, sharex=True)
    >>> for ind, data in enumerate([[orig_img, "original image"],
    ...             [sp_filter_axis_0, "spline filter (axis=0)"],
    ...             [sp_filter_axis_1, "spline filter (axis=1)"]]):
    ...     ax[ind].imshow(data[0], cmap='gray_r')
    ...     ax[ind].set_title(data[1])
    >>> plt.tight_layout()
    >>> plt.show()

    """
    if order < 0 or order > 5:
        raise RuntimeError('spline order not supported')
    input = np.asarray(input)
    complex_output = np.iscomplexobj(input)
    output = _ni_support._get_output(output, input,
                                     complex_output=complex_output)
    if complex_output:
        spline_filter1d(input.real, order, axis, output.real, mode)
        spline_filter1d(input.imag, order, axis, output.imag, mode)
        return output
    if order in [0, 1]:
        output[...] = np.array(input)
    else:
        mode = _ni_support._extend_mode_to_code(mode)
        axis = normalize_axis_index(axis, input.ndim)
        _nd_image.spline_filter1d(input, order, axis, output, mode)
    return output


def spline_filter(input, order=3, output=np.float64, mode='mirror'):
    """
    Multidimensional spline filter.

    Parameters
    ----------
    %(input)s
    order : int, optional
        The order of the spline, default is 3.
    output : ndarray or dtype, optional
        The array in which to place the output, or the dtype of the returned
        array. Default is ``numpy.float64``.
    %(mode_interp_mirror)s

    Returns
    -------
    spline_filter : ndarray
        Filtered array. Has the same shape as `input`.

    See Also
    --------
    spline_filter1d : Calculate a 1-D spline filter along the given axis.

    Notes
    -----
    The multidimensional filter is implemented as a sequence of
    1-D spline filters. The intermediate arrays are stored
    in the same data type as the output. Therefore, for output types
    with a limited precision, the results may be imprecise because
    intermediate results may be stored with insufficient precision.

    For complex-valued `input`, this function processes the real and imaginary
    components independently.

    .. versionadded:: 1.6.0
        Complex-valued support added.

    Examples
    --------
    We can filter an image using multidimentional splines:

    >>> from scipy.ndimage import spline_filter
    >>> import numpy as np
    >>> import matplotlib.pyplot as plt
    >>> orig_img = np.eye(20)  # create an image
    >>> orig_img[10, :] = 1.0
    >>> sp_filter = spline_filter(orig_img, order=3)
    >>> f, ax = plt.subplots(1, 2, sharex=True)
    >>> for ind, data in enumerate([[orig_img, "original image"],
    ...                             [sp_filter, "spline filter"]]):
    ...     ax[ind].imshow(data[0], cmap='gray_r')
    ...     ax[ind].set_title(data[1])
    >>> plt.tight_layout()
    >>> plt.show()

    """
    if order < 2 or order > 5:
        raise RuntimeError('spline order not supported')
    input = np.asarray(input)
    complex_output = np.iscomplexobj(input)
    output = _ni_support._get_output(output, input,
                                     complex_output=complex_output)
    if complex_output:
        spline_filter(input.real, order, output.real, mode)
        spline_filter(input.imag, order, output.imag, mode)
        return output
    if order not in [0, 1] and input.ndim > 0:
        for axis in range(input.ndim):
            spline_filter1d(input, order, axis, output=output, mode=mode)
            input = output
    else:
        output[...] = input[...]
    return output


def zoom(input, zoom, output=None, order=3, mode='constant', cval=0.0,
         prefilter=True, *, grid_mode=False):
    """
    Zoom an array.

    The array is zoomed using spline interpolation of the requested order.

    Parameters
    ----------
    %(input)s
    zoom : float or sequence
        The zoom factor along the axes. If a float, `zoom` is the same for each
        axis. If a sequence, `zoom` should contain one value for each axis.
    %(output)s
    order : int, optional
        The order of the spline interpolation, default is 3.
        The order has to be in the range 0-5.
    %(mode_interp_constant)s
    %(cval)s
    %(prefilter)s
    grid_mode : bool, optional
        If False, the distance from the pixel centers is zoomed. Otherwise, the
        distance including the full pixel extent is used. For example, a 1d
        signal of length 5 is considered to have length 4 when `grid_mode` is
        False, but length 5 when `grid_mode` is True. See the following
        visual illustration:

        .. code-block:: text

                | pixel 1 | pixel 2 | pixel 3 | pixel 4 | pixel 5 |
                     |<-------------------------------------->|
                                        vs.
                |<----------------------------------------------->|

        The starting point of the arrow in the diagram above corresponds to
        coordinate location 0 in each mode.

    Returns
    -------
    zoom : ndarray
        The zoomed input.

    Notes
    -----
    For complex-valued `input`, this function zooms the real and imaginary
    components independently.

    .. versionadded:: 1.6.0
        Complex-valued support added.

    Examples
    --------
    >>> from scipy import ndimage, datasets
    >>> import matplotlib.pyplot as plt

    >>> fig = plt.figure()
    >>> ax1 = fig.add_subplot(121)  # left side
    >>> ax2 = fig.add_subplot(122)  # right side
    >>> ascent = datasets.ascent()
    >>> result = ndimage.zoom(ascent, 3.0)
    >>> ax1.imshow(ascent, vmin=0, vmax=255)
    >>> ax2.imshow(result, vmin=0, vmax=255)
    >>> plt.show()

    >>> print(ascent.shape)
    (512, 512)

    >>> print(result.shape)
    (1536, 1536)
    """
    if order < 0 or order > 5:
        raise RuntimeError('spline order not supported')
    input = np.asarray(input)
    if input.ndim < 1:
        raise RuntimeError('input and output rank must be > 0')
    zoom = _ni_support._normalize_sequence(zoom, input.ndim)
    output_shape = tuple(
        [int(round(ii * jj)) for ii, jj in zip(input.shape, zoom)])
    complex_output = np.iscomplexobj(input)
    output = _ni_support._get_output(output, input, shape=output_shape,
                                     complex_output=complex_output)
    if complex_output:
        # import under different name to avoid confusion with zoom parameter
        from scipy.ndimage._interpolation import zoom as _zoom

        kwargs = dict(order=order, mode=mode, prefilter=prefilter)
        _zoom(input.real, zoom, output=output.real,
              cval=np.real(cval), **kwargs)
        _zoom(input.imag, zoom, output=output.imag,
              cval=np.imag(cval), **kwargs)
        return output
    if prefilter and order > 1:
        padded, npad = _prepad_for_spline_filter(input, mode, cval)
        filtered = spline_filter(padded, order, output=np.float64, mode=mode)
    else:
        npad = 0
        filtered = input
    if grid_mode:
        # warn about modes that may have surprising behavior
        suggest_mode = None
        if mode == 'constant':
            suggest_mode = 'grid-constant'
        elif mode == 'wrap':
            suggest_mode = 'grid-wrap'
        if suggest_mode is not None:
            warnings.warn(
                (f"It is recommended to use mode = {suggest_mode} instead of {mode} "
                 f"when grid_mode is True."),
                stacklevel=2
            )
    mode = _ni_support._extend_mode_to_code(mode)

    zoom_div = np.array(output_shape)
    zoom_nominator = np.array(input.shape)
    if not grid_mode:
        zoom_div -= 1
        zoom_nominator -= 1

    # Zooming to infinite values is unpredictable, so just choose
    # zoom factor 1 instead
    zoom = np.divide(zoom_nominator, zoom_div,
                     out=np.ones_like(input.shape, dtype=np.float64),
                     where=zoom_div != 0)
    zoom = np.ascontiguousarray(zoom)
    _nd_image.zoom_shift(filtered, zoom, None, output, order, mode, cval, npad,
                         grid_mode)
    return output
