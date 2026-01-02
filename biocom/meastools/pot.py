"""Potentiostatic measurement tools for current range determination.

Provides functions for determining appropriate current ranges for potentiostatic
experiments through AC voltage tests.
"""

import numpy as np
from pathlib import Path
from typing import Optional

from ..com.server import OLECOM, DeviceChannel
from ..mps.techniques.sequence import TechniqueSequence
from ..mps.techniques.chrono import CAParameters
from ..mps.common import  SampleType, get_i_range
from ..mps import config as cfg
from ..mpr import read_mpr
from ..mps.write import write_techniques

from ..processing.chrono import ControlMode, process_ivt_simple


def load_irange_test(
        server: OLECOM, 
        device_channel: DeviceChannel,
        mps_file: Path,
        v_dc: float,
        v_ac: float,
        step_duration: float = 0.5, 
        dt: float = 1e-3, 
        t_init: Optional[float] = None,
        t_final: Optional[float] = None,
        **kwargs):
    """Load current range test settings using AC voltage steps.
    
    Configures chronoamperometry with voltage perturbations to determine
    appropriate current range for measurements.
    
    :param server: EC-Lab COM server instance
    :type server: OLECOM
    :param device_channel: Target device channel
    :type device_channel: DeviceChannel
    :param mps_file: Path for MPS settings file
    :type mps_file: Path
    :param v_dc: DC voltage in V
    :type v_dc: float
    :param v_ac: AC voltage amplitude in V
    :type v_ac: float
    :param step_duration: Duration of AC steps in seconds
    :type step_duration: float
    :param dt: Sampling interval in seconds
    :type dt: float
    :param t_init: Initial equilibration time (defaults to 10% of step_duration)
    :type t_init: Optional[float]
    :param t_final: Final equilibration time (defaults to 10% of step_duration)
    :type t_final: Optional[float]
    :param kwargs: Additional parameters for CAParameters
    :return: Success code (1 = success)
    :rtype: int
    """
    
    t_dc = max(0.1, step_duration * 0.1)
    
    if t_final is None:
        t_final = t_dc
        
    if t_init is None:
        t_init = t_dc
        
    step_durations = [t_init] + [step_duration] * 4  + [t_final]
    step_voltages = [v_dc, v_dc + v_ac, v_dc - v_ac, v_dc + v_ac, v_dc - v_ac, v_dc]
    
    ca = CAParameters(
        step_voltages,
        step_durations,
        dt,
        bandwidth=device_channel.model.max_bandwidth,
        **kwargs
    )
    # print("step durations:", ca.step_durations, ca._step_durations_formatted)
    # print("I Range:", ca.i_range)
    # print("I Range init:", ca.i_range_init)
    
    seq = TechniqueSequence([ca])
    config = cfg.set_defaults(device_channel.model, seq, 
                              SampleType.CORROSION)
    
    write_techniques(seq, config, mps_file.parent.joinpath(mps_file.name.replace(".mps", "_tmp.mps")))
    
    return server.load_techniques(device_channel, seq, config, mps_file)


def read_irange_test(mpr_file: Path):
    """Read current range test data and determine appropriate range.
    
    Analyzes measured current to determine the optimal current range setting.
    
    :param mpr_file: Path to MPR data file
    :type mpr_file: Path
    :return: Tuple of (maximum current in A, recommended IRange)
    :rtype: Tuple[float, IRange]
    """
    mpr = read_mpr(Path(mpr_file), unscale=True)
    i = mpr.data["I/A"]
    i_max = np.max(np.abs(i))
    return i_max, get_i_range(i_max)