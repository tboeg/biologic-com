"""Wait (WAIT) technique parameters.

This module provides parameter classes for configuring waiting steps in EC-Lab. Wait can monitor the electrode potential and current while maintaining the previous control point.
"""
from dataclasses import dataclass

from .technique import TechniqueParameters
from ..write_utils import format_duration
from ... import units
from enum import Enum
from datetime import datetime

class WaitMode(Enum):
    DURATION = 1
    UNTIL = 0

@dataclass
class WaitParameters(TechniqueParameters):
    """Wait technique parameters.
    
    Configures a wait step that can monitor electrode potential and current while
    maintaining the previous control point. Useful for equilibration, rest
    periods, and stability monitoring.
    
    :param duration: Wait duration (seconds)
    :type duration: float
    :param mode: If True, wait until a specific date and time instead of a duration (default: False)
    :type mode: WaitMode
    :param stop_date: Wait until date
    :type stop_date: String in format "YYYY-MM-DD HH:MM:SS"
    :param start_from_technique: Record from start of previous technique (True) or from a particular technique (False) (default: True)
    :type start_from_technique: bool
    :param start_technique_index: If from_technique is False, the index of the technique from which to start recording (1-based)
    :type start_technique_index: int
    :param record: Record voltage and current if True (default: False)
    :type record: bool
    :param record_dv: Voltage change threshold for recording (mV, default: 0.0)
    :type record_dv: float
    :param record_di: Current change threshold for recording (mA, default: 0.0)
    :type record_di: float
    :param record_dt: Time interval for recording (seconds, default: 0.0)
    :type record_dt: float
    """

    duration: float = 10.0  # seconds
    stop_date_str: str = "2024-01-01 00:00:00"  # "YYYY-MM-DD HH:MM:SS"
    mode: WaitMode = WaitMode.DURATION
    start_from_technique: bool = False
    start_technique_index: int = 1
    record: bool = False
    record_dv: float = 0.0  # mV
    record_di: float = 0.0  # mA
    record_dt: float = 0.0  # s
    
    technique_name = "Wait"
    abbreviation = "WAIT"
    
    _param_map = { 'select': 'mode',
        'td (h:m:s)': '_duration_formatted',
        'from': 'start_from_technique',
        'tech. num.': 'start_technique_index',
        'date (m/d/y)':'_stop_date_formatted',
        'date (h:m:s)':'_stop_time_formatted',
        'record': 'record',
        'dE (mV)': 'record_dv',
        'dI': '_i_A_scaled',
        'unit dI': '_i_A_unit',
        'dt (s)': 'record_dt'
    }

    def __post_init__(self):
        self._i_A_scaled, self._i_A_unit_char = units.get_scaled_value_and_prefix(self.record_di*1E-3, 1e-9, 1)
        self._i_A_unit = self._i_A_unit_char + "A"
        try:
            self.stop_date = datetime.fromisoformat(self.stop_date_str)
        except ValueError:
            raise ValueError("stop_date must be in format 'YYYY-MM-DD HH:MM:SS'")

    @property
    def _duration_formatted(self):
        return format_duration(self.duration)
    
    @property
    def _stop_date_formatted(self):
        return self.stop_date.strftime(r'%m/%d/%y')
    
    @property
    def _stop_time_formatted(self):
        return self.stop_date.strftime(r'%H:%M:%S')