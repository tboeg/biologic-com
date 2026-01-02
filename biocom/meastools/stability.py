"""Sample stability monitoring tools.

Provides functions for determining electrochemical sample stability based on
single-frequency impedance measurements over time.
"""

import numpy as np
from numpy import ndarray
import scipy.ndimage as ndi
from pathlib import Path
from collections import deque
import time
from typing import Callable, Optional, Union

from ..com.server import OLECOM, DeviceChannel
from ..mps.common import EweVs, Bandwidth, SampleType
from ..mps.techniques.eis import PEISParameters
from ..mps.techniques.sequence import TechniqueSequence
from ..mps import config as cfg


def load_z_stability_test(
        server: OLECOM, 
        device_channel: DeviceChannel,
        mps_file: Path,
        v_dc: float,
        v_ac: float,
        f: float,
        v_vs: EweVs = EweVs.REF,
        bandwidth: Optional[Bandwidth] = None,
        **kwargs):
    """Load impedance stability test settings.
    
    Configures single-frequency PEIS for repeated measurements to monitor
    sample stability over time.
    
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
    :param f: Measurement frequency in Hz
    :type f: float
    :param v_vs: Voltage reference
    :type v_vs: EweVs
    :param bandwidth: Amplifier bandwidth setting
    :type bandwidth: Optional[Bandwidth]
    :param kwargs: Additional parameters for PEISParameters
    """
    if bandwidth is None:
        # Use highest available bandwidth
        bandwidth = Bandwidth(device_channel.model.max_bandwidth)
    
    eis = PEISParameters(
        v_dc,
        v_ac,
        v_vs,
        f,
        f,
        bandwidth=bandwidth,
        **kwargs
    )
        
    seq = TechniqueSequence([eis])
    config = cfg.set_defaults(device_channel.model, seq, 
                              SampleType.CORROSION)
    
    server.load_techniques(device_channel, seq, config, mps_file)
    
    
async def run_z_stability_test_async(
        server: OLECOM, 
        device_channel: DeviceChannel,
        min_wait: float,
        timeout: float, 
        window: int = 10,
        rate_thresh: float = 0.01
        ):
    """Run impedance stability test asynchronously.
    
    Repeatedly measures impedance until stable or timeout. Stability is determined
    by monitoring the rate of change of impedance magnitude.
    
    :param server: EC-Lab COM server instance
    :type server: OLECOM
    :param device_channel: Target device channel (settings must be pre-loaded)
    :type device_channel: DeviceChannel
    :param min_wait: Minimum wait time in seconds before checking stability
    :type min_wait: float
    :param timeout: Maximum wait time in seconds
    :type timeout: float
    :param window: Number of measurements to use for stability analysis
    :type window: int
    :param rate_thresh: Threshold for rate of change (fraction of |Z| per minute)
    :type rate_thresh: float
    :return: True if stable within timeout, False otherwise
    :rtype: bool
    """
    # assume that settings are already loaded
    z_log = deque()
    
    # Write to a single mpr file and overwrite at each iteration
    mpr_file = server.get_settings(device_channel).replace(".mps", ".mpr")

    start_time = time.monotonic()
    elapsed = 0
    stable = False
    while not (stable and elapsed > min_wait):
        # Launch z measurement
        output_file = server.run_channel(device_channel, output_file=mpr_file)
        
        await server.wait_for_channel_async(device_channel, min_wait=1.0, timeout=120.0)
        
        elapsed = time.monotonic() - start_time
        data = server.get_eis_value(output_file, 0)
        z_log.append([elapsed, data['Re(Z)/Ohm'], data['-Im(Z)/Ohm']])
        
        if len(z_log >= window):
            z_arr = np.array(z_log)[-window:]
            z_mod = np.sum(z_arr[:, 1:] **2, axis=1) ** 0.5
            # Calculate rate of change as % of |Z| per minute
            stable = value_is_stable(z_arr[:, 0], z_arr[:, 1:], z_mod * rate_thresh)

        if elapsed > timeout:
            break
        
    return stable
    
    

def value_is_stable(
        times: Union[ndarray, list], 
        values: Union[ndarray, list], 
        rate_thresh: float, 
        filter_values: bool = True, 
        filter_func: Optional[Callable[[ndarray]]] = None,
        relative: bool = False):
    """Determine if a time-series value has stabilized.
    
    Fits a linear trend to the data and checks if the rate of change is below
    the specified threshold.
    
    :param times: Time points in seconds
    :type times: Union[ndarray, list]
    :param values: Measured values (can be 1D or 2D array)
    :type values: Union[ndarray, list]
    :param rate_thresh: Maximum acceptable rate of change per minute
    :type rate_thresh: float
    :param filter_values: Whether to apply Gaussian smoothing to reduce noise
    :type filter_values: bool
    :param filter_func: Custom filter function (defaults to Gaussian with sigma=1)
    :type filter_func: Optional[Callable[[ndarray]]]
    :param relative: Whether to normalize values by median before analysis
    :type relative: bool
    :return: True if rate of change is below threshold
    :rtype: bool
    """
    times = np.array(times)
    values = np.array(values)
    
    if np.ndim(values) > 1:
        # Vector of values
        # Ensure that all entries are stable
        return all([value_is_stable(v) for v in values.T])
    
    if relative:
        # Analyze changes relative to median value
        values = values / np.median(values)

    if filter_values:
        # Filter measured values to reduce impact of noise
        if filter_func is None:
            filter_func = lambda x: ndi.gaussian_filter1d(x, 1, mode='nearest')
        values = filter_func(values)

    # Get rate of change per minute
    fit = np.polyfit(times / 60, values, deg=1)
    rate = fit[0]
    # print('slope: {:.6f} units/min'.format(slope))

    # If rate is below threshold, property has equilibrated
    if abs(rate) <= rate_thresh:
        return True
    else:
        return False
    
