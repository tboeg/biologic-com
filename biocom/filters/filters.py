"""Signal filtering functions for electrochemical data processing.

This module provides specialized filtering capabilities including:
- Masked filtering for weighted data
- NaN-aware filtering
- Nonuniform Gaussian filtering with spatially-varying smoothing scales
"""

import numpy as np
from scipy import ndimage



def masked_filter(a, mask, filter_func=None, **filter_kw):
    """Perform a masked/normalized filter operation on an array.
    
    Applies a linear filter with weighting based on a mask array. The filter is
    normalized by the filtered mask to maintain proper weighting. Only valid for
    linear filters.
    
    :param a: Array to filter
    :type a: ndarray
    :param mask: Mask array indicating weight of each element; must match shape of a
    :type mask: ndarray
    :param filter_func: Filter function to apply (defaults to gaussian_filter)
    :type filter_func: callable, optional
    :param filter_kw: Keyword arguments to pass to filter_func
    :type filter_kw: dict, optional
    :return: Filtered array with proper normalization
    :rtype: ndarray
    """
    if filter_kw is None:
        if filter_func is None:
            sigma = np.ones(np.ndim(a))
            sigma[-1] = 0
            filter_kw = {'sigma': sigma}
        else:
            filter_kw = None
    if filter_func is None:
        filter_func = ndimage.gaussian_filter

    mask = mask.astype(float)

    x_filt = filter_func(a * mask, **filter_kw)
    mask_filt = filter_func(mask, **filter_kw)

    # print(np.sum(np.isnan(x_filt)), np.sum(np.isnan(mask_filt)), np.sum(mask_filt == 0))

    return x_filt / mask_filt


def nan_filter(a, filter_func, **filter_kw):
    """Filter an array containing NaN values.
    
    Applies a filter operation while properly handling NaN values by treating
    them as masked data. NaN positions are given zero weight in the filtering.
    
    :param a: Array to filter (may contain NaN values)
    :type a: ndarray
    :param filter_func: Filter function to apply
    :type filter_func: callable
    :param filter_kw: Keyword arguments to pass to filter_func
    :type filter_kw: dict, optional
    :return: Filtered array with NaN values properly handled
    :rtype: ndarray
    """
    mask = ~np.isnan(a)
    return masked_filter(np.nan_to_num(a), mask, filter_func, **filter_kw)




# Nonuniform gaussian
# -------------------
def nonuniform_gaussian_filter1d(a, sigma, axis=-1,
                                 mode='reflect', cval=0.0, truncate=4, order=0,
                                 sigma_node_factor=1.5, min_sigma=0.25):
    """Apply 1D Gaussian filter with varying length scale.
    
    Performs Gaussian filtering where the smoothing lengthscale (sigma) can vary
    along the array. This is accomplished by filtering at multiple discrete sigma
    values and averaging the results using weights based on the local sigma value.
    
    :param a: Input array to filter
    :type a: ndarray
    :param sigma: Smoothing scale for each position (same shape as a)
    :type sigma: ndarray
    :param axis: Axis along which to apply the filter
    :type axis: int
    :param mode: Mode for handling array borders ('reflect', 'constant', 'nearest', etc.)
    :type mode: str
    :param cval: Value to fill past edges when mode is 'constant'
    :type cval: float
    :param truncate: Truncate filter at this many standard deviations
    :type truncate: float
    :param order: Order of the derivative (0 = smoothing, 1 = first derivative, etc.)
    :type order: int
    :param sigma_node_factor: Spacing factor between discrete sigma nodes (in log space)
    :type sigma_node_factor: float
    :param min_sigma: Minimum effective sigma value (below this, no filtering applied)
    :type min_sigma: float
    :return: Filtered array
    :rtype: ndarray
    """
    if np.max(sigma) > 0:
        sigma = np.maximum(sigma, 1e-8)
        # Get sigma nodes
        min_ls = max(np.min(np.log10(sigma)), np.log10(min_sigma))  # Don't go below min effective value
        max_ls = max(np.max(np.log10(sigma)), np.log10(min_sigma))
        num_nodes = int(np.ceil((max_ls - min_ls) / np.log10(sigma_node_factor))) + 1
        sigma_nodes = np.logspace(min_ls, max_ls, num_nodes)

        if np.min(sigma) < min_sigma:
            # If smallest sigma is below min effective value, insert dummy node at lowest value
            # This node will simply return the original array

            # Determine factor for uniform node spacing
            if len(sigma_nodes) > 1:
                factor = sigma_nodes[-1] / sigma_nodes[-2]
            else:
                factor = sigma_node_factor

            # Limit requested sigma values to 2 increments below min effective sigma
            # This will ensure that any sigma values well below min_sigma will not be filtered, while those
            # close to min_sigma will receive mixed-lengthscale filtering as intended
            sigma[sigma < min_sigma / (factor ** 2)] = min_sigma / (factor ** 2)

            # Insert as many sigma values as needed to get to lowest requested value (max 2 inserts)
            while sigma_nodes[0] > np.min(sigma) * 1.001:
                sigma_nodes = np.insert(sigma_nodes, 0, sigma_nodes[0] / factor)

        # print(sigma_nodes)
        if len(sigma_nodes) > 1:
            node_delta = np.log(sigma_nodes[-1] / sigma_nodes[-2])
        else:
            node_delta = 1

        def get_node_weights(x):
            # Tile x and nodes to same shape with extra axis
            tile_shape = np.ones(np.ndim(x) + 1, dtype=int)
            tile_shape[0] = len(sigma_nodes)
            # print('x:', x)
            x_tile = np.tile(x, tile_shape)
            node_tile = np.tile(sigma_nodes, (*x.shape, 1))
            node_tile = np.moveaxis(node_tile, -1, 0)

            nw = np.abs(np.log(x_tile / node_tile)) / node_delta
            nw[nw >= 1] = 1
            nw = 1 - nw
            # print('min weight:', np.min(nw))
            # print('max weight:', np.max(nw))
            # print('min weight sum:', np.min(np.sum(nw, axis=0)))
            # print('max weight sum:', np.max(np.sum(nw, axis=0)))
            return nw

        node_outputs = np.empty((len(sigma_nodes), *a.shape))

        for i in range(len(sigma_nodes)):
            if sigma_nodes[i] < min_sigma:
                # Sigma is below minimum effective value
                # if empty:
                #     # For empty filter, still need to apply filter to determine central value
                #     node_outputs[i] = empty_gaussian_filter1d(a, sigma=min_sigma, axis=axis, mode=mode, cval=cval,
                #                                               truncate=truncate, order=order)
                # else:
                # For standard filter, reduces to original array
                node_outputs[i] = a
            else:
                # if empty:
                #     node_outputs[i] = empty_gaussian_filter1d(a, sigma=sigma_nodes[i], axis=axis, mode=mode, cval=cval,
                #                                               truncate=truncate, order=order)
                # else:
                node_outputs[i] = ndimage.gaussian_filter1d(a, sigma=sigma_nodes[i], axis=axis, mode=mode,
                                                                cval=cval,
                                                                truncate=truncate, order=order)

        node_weights = get_node_weights(sigma)
        # print(node_weights.shape, node_outputs.shape)
        # print(np.sum(node_weights, axis=0))

        out = node_outputs * node_weights
        return np.sum(out, axis=0)

    else:
        # No filtering to perform on this axis
        return a

