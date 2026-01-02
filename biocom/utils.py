import numpy as np
from numpy import ndarray
from typing import Callable, Tuple, List, Union, Optional

def merge_dicts(*dicts):
    """Merge multiple dictionaries into one.
    
    Equivalent to dict1 | dict2, but backwards compatible with Python < 3.9.
    In the case of duplicate keys, dictionaries that appear later in the 
    argument sequence take precedence.

    :param dicts: Variable number of dictionaries to merge
    :type dicts: dict
    :return: Merged dictionary
    :rtype: dict
    """
    # for backwards compatibility
    new = dicts[0].copy()
    for d in dicts:
        new.update(d)
    return new


def split_list(x: list, split_func: Callable) -> Tuple[List]:
    """Split each entry of a list with split_func, then return separate lists of the outputs.
    
    Applies split_func to each element of x, then transposes the results so that
    the ith output list contains the ith return value from split_func for all inputs.

    :param list x: Input list to process
    :param Callable split_func: Function that takes one element and returns a tuple or list
    :return: Tuple of lists, where the ith list contains the ith split_func output for all entries
    :rtype: Tuple[List]
    """
    split = [split_func(xi) for xi in x]
    return tuple([[s[i] for s in split] for i in range(len(split[0]))])


def isiterable(a) -> bool:
    """Check if an object is iterable.
    
    :param a: Object to test for iterability
    :return: True if object is iterable, False otherwise
    :rtype: bool
    """
    try:
        iter(a)
        return True
    except TypeError:
        return False
    
    
def nearest_index(x_array: ndarray, x_val: Union[float, ndarray], constraint: Optional[int] = None):
    """Get index of x_array corresponding to value closest to x_val.
    
    :param ndarray x_array: Array in which to search
    :param x_val: Value(s) to match
    :type x_val: float or ndarray
    :param int constraint: Directional constraint: -1 for x_array <= x_val, 1 for x_array >= x_val, None for closest regardless of direction, defaults to None
    :return: If x_val is scalar, returns a single integer index. If x_val is an array, returns an array of indices of the same length
    :rtype: int or ndarray
    :raises ValueError: If no index satisfies the constraint
    """
    if constraint is None:
        def func(arr, x):
            return np.abs(arr - x)
    elif constraint in [-1, 1]:
        def func(arr, x):
            out = np.zeros_like(arr) + np.inf
            constraint_index = constraint * arr >= constraint * x
            out[constraint_index] = constraint * (arr - x)[constraint_index]
            return out
    else:
        raise ValueError(f'Invalid constraint argument {constraint}. Options: None, -1, 1')

    if np.isscalar(x_val):
        obj_func = func(x_array, x_val)
        index = np.argmin(obj_func)
        max_of = obj_func
    else:
        aa, bb = np.meshgrid(x_array, np.array(x_val))
        obj_func = func(aa, bb)
        index = np.argmin(obj_func, axis=1)
        max_of = np.max(obj_func[index])
        

    # Validate index
    if max_of == np.inf:
        if constraint == -1:
            min_val = np.min(x_array)
            raise ValueError(f'No index satisfying {constraint} constraint: minimum array value {min_val} '
                             f'exceeds target value {x_val}')
        else:
            max_val = np.max(x_array)
            raise ValueError(f'No index satisfying {constraint} constraint: maximum array value {max_val} '
                             f'is less than target value {x_val}')

    return index


def nearest_value(x_array: ndarray, x_val: Union[float, ndarray], constraint: Optional[int] = None):
    """Get value from x_array that is closest to x_val.
    
    :param ndarray x_array: Array in which to search
    :param x_val: Value(s) to match
    :type x_val: float or ndarray
    :param int constraint: Directional constraint: -1 for x_array <= x_val, 1 for x_array >= x_val, None for closest regardless of direction, defaults to None
    :return: If x_val is scalar, returns a single value. If x_val is an array, returns an array of values of the same length
    :rtype: float or ndarray
    :raises ValueError: If no index satisfies the constraint
    """
    index = nearest_index(x_array, x_val, constraint)
    return x_array[index]
