"""Open circuit voltage (OCV) measurement tools.

Provides functions for running and reading OCV measurements using the COM interface.
"""

import numpy as np
from pathlib import Path
from typing import Union

from ..com.server import OLECOM, DeviceChannel
from ..mps.techniques.sequence import TechniqueSequence
from ..mps.techniques.ocv import OCVParameters
from ..mps.common import SampleType
from ..mps import config as cfg
from ..mpr import read_mpr


def run_ocv(
        server: OLECOM, 
        device_channel: DeviceChannel,
        mps_file: Path,
        duration: float = 5, 
        dt: float = 0.1, 
        **kwargs):
    """Run open circuit voltage measurement.
    
    Measures the equilibrium potential with no applied current.
    
    :param server: EC-Lab COM server instance
    :type server: OLECOM
    :param device_channel: Target device channel
    :type device_channel: DeviceChannel
    :param mps_file: Path for MPS settings file
    :type mps_file: Path
    :param duration: Measurement duration in seconds
    :type duration: float
    :param dt: Sampling interval in seconds
    :type dt: float
    :param kwargs: Additional parameters for OCVParameters
    :return: Data filename
    :rtype: str
    """

    ocv = OCVParameters(
        duration,
        dt,
        **kwargs
    )
    
    seq = TechniqueSequence([ocv])
    config = cfg.set_defaults(device_channel.model, seq, 
                              SampleType.CORROSION)
    
    server.load_techniques(device_channel, seq, config, mps_file)

    server.run_channel(device_channel, mps_file)

    return server.get_data_filename(device_channel, 0)


def read_ocv(mpr_file: Path, n_points: Union[int, None] = 10, agg='mean') -> float:
    """Read OCV from file and estimate the OCV by aggregating the 
    last n_points points.

    :param Path mpr_file: Path to mpr file.
    :param int n_points: Number of points to aggregate, starting from 
        the end of the file and moving back. If None, use all points in 
        the file. Defaults to 10.
    :param str agg: Aggregation function to use. Any numpy function
        is allowed (e.g. 'mean', 'median', 'max'). 
        Defaults to 'mean'.
    :return float: Aggregated OCV.
    """
    mpr = read_mpr(Path(mpr_file), unscale=True)
    if n_points is None:
        n_points = len(mpr.data)
    return getattr(np, agg)(mpr.data['Ewe/V'][-n_points:])
