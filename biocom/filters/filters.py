import numpy as np
from scipy import ndimage



def masked_filter(a, mask, filter_func=None, **filter_kw):
    """
    Perform a masked/normalized filter operation on a. Only valid for linear filters
    :param ndarray a: array to filter
    :param ndarray mask: mask array indicating weight of each pixel in x_in; must match shape of x_in
    :param filter_func: filter function to apply. Defaults to gaussian_filter
    :param filter_kw: keyword args to pass to filter_func
    :return:
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
    mask = ~np.isnan(a)
    return masked_filter(np.nan_to_num(a), mask, filter_func, **filter_kw)




# Nonuniform gaussian
# -------------------
def nonuniform_gaussian_filter1d(a, sigma, axis=-1,
                                 mode='reflect', cval=0.0, truncate=4, order=0,
                                 sigma_node_factor=1.5, min_sigma=0.25):
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

