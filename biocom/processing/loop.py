"""Loop experiment data processing.

Provides utilities for reading loop files and splitting cyclic data into
individual cycles.
"""

import numpy as np
from pathlib import Path

from ..mpr import read_mpr

def read_loop_file(file: Path):
    """Read loop split indices from EC-Lab LOOP file.
    
    :param file: Path to LOOP text file
    :type file: Path
    :return: List of data indices marking cycle boundaries
    :rtype: List[int]
    """
    with open(file, "r") as f:
        txt = f.read()
        
    split_index = [int(t) for t in txt.split("\n")[1:-1]]
    return split_index
    
    
def path_to_loop_file(mpr_file: Path):
    """Convert MPR file path to corresponding LOOP file path.
    
    :param mpr_file: Path to MPR data file
    :type mpr_file: Path
    :return: Path to LOOP file
    :rtype: Path
    """
    return mpr_file.parent.joinpath(mpr_file.name.replace(".mpr", "_LOOP.txt"))
    
def split_cycles(mpr_file: Path, unscale=True):
    """Split loop experiment data into individual cycles.
    
    :param mpr_file: Path to MPR data file
    :type mpr_file: Path
    :param unscale: Whether to unscale data values
    :type unscale: bool
    :return: List of data arrays, one per cycle
    :rtype: List[ndarray]
    """
    mpr = read_mpr(mpr_file, unscale=unscale)
    loop_file = path_to_loop_file(mpr_file)
    split_index = read_loop_file(loop_file)
    # First and last indices are unnecesary (0 and len(mpr.data))
    return np.split(mpr.data, split_index[1:-1])