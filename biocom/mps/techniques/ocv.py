"""Open Circuit Voltage (OCV) technique parameters.

This module provides parameter classes for configuring Open Circuit Voltage
measurements in EC-Lab. OCV monitors the electrode potential without applying
current or voltage control.
"""
from dataclasses import dataclass

from .technique import HardwareParameters, TechniqueParameters, HARDWARE_PARAM_MAP
from ..write_utils import format_duration
from ...utils import merge_dicts


@dataclass
class _OCVParameters(object):
    """Internal OCV parameter storage.
    
    Base class containing OCV-specific parameters. Used with multiple
    inheritance to combine with HardwareParameters.
    
    :param duration: Measurement duration (seconds)
    :type duration: float
    :param record_dt: Recording time interval (seconds)
    :type record_dt: float
    :param dvdt_limit: Voltage drift limit for termination (mV/h, default: 0.0)
    :type dvdt_limit: float
    :param record_average: Record averaged voltage if True (default: False)
    :type record_average: bool
    :param record_dv: Voltage change threshold for recording (mV, default: 0.0)
    :type record_dv: float
    """
    duration: float
    record_dt: float
    dvdt_limit: float = 0.0  # mV/h
    record_average: bool = False
    record_dv: float = 0.0  # mV
    
    technique_name = "Open Circuit Voltage"
    abbreviation = "OCV"
    
    _param_map = merge_dicts(
        {
            'tR (h:m:s)': '_duration_formatted',
            'dER/dt (mV/h)': 'dvdt_limit',
            'record': '_record',
            'dER (mV)': 'record_dv',
            'dtR (s)': 'record_dt' 
        },
        # only E range applies to OCV; no I range or bandwidth
        {k: v for k, v in HARDWARE_PARAM_MAP.items() if k[:7] == 'E range'},
    )
    
@dataclass
class OCVParameters(HardwareParameters, _OCVParameters, TechniqueParameters):
    """Open Circuit Voltage technique parameters.
    
    Configures an OCV measurement that monitors electrode potential without
    applying external current or voltage. Useful for equilibration, rest
    periods, and stability monitoring.
    
    Inherits hardware parameters (v_range_min, v_range_max) from
    HardwareParameters and measurement parameters from _OCVParameters.
    
    :param duration: Measurement duration (seconds)
    :type duration: float
    :param record_dt: Recording time interval (seconds)
    :type record_dt: float
    :param dvdt_limit: Voltage drift limit for early termination (mV/h, default: 0.0)
    :type dvdt_limit: float
    :param record_average: Record averaged voltage if True (default: False)
    :type record_average: bool
    :param record_dv: Voltage change threshold for recording (mV, default: 0.0)
    :type record_dv: float
    :param v_range_min: Minimum voltage range (V, default: -10.0)
    :type v_range_min: float
    :param v_range_max: Maximum voltage range (V, default: 10.0)
    :type v_range_max: float
    
    Example::
    
        # Simple 60-second OCV measurement
        ocv = OCVParameters(
            duration=60.0,
            record_dt=1.0
        )
        
        # OCV with stability criterion
        ocv_stable = OCVParameters(
            duration=3600.0,
            record_dt=10.0,
            dvdt_limit=0.1  # Stop when drift < 0.1 mV/h
        )
    """    
    @property
    def _record(self):
        if self.record_average:
            return "<Ewe>"
        return "Ewe"
    
    @property
    def _duration_formatted(self):
        return format_duration(self.duration)