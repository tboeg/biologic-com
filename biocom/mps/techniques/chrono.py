"""Chronoamperometry and Chronopotentiometry technique parameters.

This module provides parameter classes for chronoamperometric (CA) and
chronopotentiometric (CP) techniques. These time-based electrochemical methods
apply constant voltage (CA) or current (CP) and record the response.
"""
from dataclasses import dataclass
import numpy as np
from numpy import ndarray
from typing import Union, Optional, List

from .stepwise import StepwiseTechniqueParameters

from ..common import (
    IRange, EweVs, IVs, DQUnits, get_i_range
)
from .technique import (
    HardwareParameters, HARDWARE_PARAM_MAP, HARDWARE_PARAM_MAP_ILIMIT, LOOP_PARAM_MAP
)
from ..write_utils import format_duration
from ...utils import merge_dicts

   
    
class ChronoParametersBase(object):
    """Base class for stepwise chronoamperometry/chronopotentiometry.
    
    Provides common properties for techniques with multiple time-based steps.
    
    :ivar step_durations: Duration of each step (seconds)
    :vartype step_durations: list
    """
    step_durations: list
    
    @property
    def num_steps(self):
        """Get number of steps in technique.
        
        :return: Number of steps
        :rtype: int
        """
        return len(self.step_durations)
    
    

@dataclass
class _CPParameters(object):
    """Internal CP (Chronopotentiometry) parameter storage.
    
    Base class containing CP-specific parameters. Used with multiple
    inheritance to combine with HardwareParameters.
    
    :param step_currents: Applied current for each step (A)
    :type step_currents: Union[list, ndarray]
    :param step_durations: Duration of each step (seconds)
    :type step_durations: Union[list, ndarray]
    :param record_dt: Recording time interval (seconds)
    :type record_dt: Union[float, List[float]]
    :param i_vs: Current measurement reference (default: IVs.NONE)
    :type i_vs: Union[IVs, List[IVs]]
    :param v_limits: Voltage limits for each step (V)
    :type v_limits: Optional[List[float]]
    :param dq_limits: Charge limits for each step
    :type dq_limits: Optional[List[float]]
    :param dq_units: Units for charge limits (default: DQUnits.AH)
    :type dq_units: DQUnits
    :param record_average: Record averaged voltage if True (default: False)
    :type record_average: bool
    :param record_dv_mV: Voltage change threshold for recording (mV, default: 0.0)
    :type record_dv_mV: float
    :param goto_ns: Loop target step number (default: 0)
    :type goto_ns: int
    :param nc_cycles: Number of loop cycles (default: 0)
    :type nc_cycles: int
    """
    step_currents: Union[list, ndarray]
    step_durations: Union[list, ndarray]
    record_dt: Union[float, List[float]]
    i_vs: Union[IVs, List[IVs]] = IVs.NONE
    v_limits: Optional[List[float]] = None
    dq_limits: Optional[List[float]] = None
    dq_units: DQUnits = DQUnits.AH
    record_average: bool = False
    record_dv_mV: float = 0.0  # mV
    
    # Placeholders
    goto_ns: int = 0
    nc_cycles: int = 0
    
    technique_name = "Chronopotentiometry"
    abbreviation = "CP"
    
    _param_map = merge_dicts(
        {
            'Ns': 'step_index',
            'Is': '_step_currents_scaled',
            'unit Is': '_step_currents_unit',
            'vs.': 'i_vs',
            'ts (h:m:s)': '_step_durations_formatted',
            'EM (V)': 'v_limits',
            'dQM': '_dq_limits_scaled',
            'unit dQM': '_dq_limits_unit',
            'record': '_record',
            'dEs (mV)': 'record_dv_mV',
            'dts (s)': 'record_dt' 
        },
        HARDWARE_PARAM_MAP,
        LOOP_PARAM_MAP
    )
    
@dataclass
class CPParameters(HardwareParameters, _CPParameters, ChronoParametersBase, StepwiseTechniqueParameters):
    """Chronopotentiometry (CP) technique parameters.
    
    Configures a chronopotentiometry measurement that applies constant current
    and records the resulting voltage response. Supports multiple sequential
    current steps.
    
    :param step_currents: Applied current for each step (A)
    :type step_currents: Union[list, ndarray]
    :param step_durations: Duration of each step (seconds)
    :type step_durations: Union[list, ndarray]
    :param record_dt: Recording time interval (seconds)
    :type record_dt: Union[float, List[float]]
    :param i_vs: Current measurement reference (default: IVs.NONE)
    :type i_vs: Union[IVs, List[IVs]]
    :param v_limits: Voltage limits for each step (V, optional)
    :type v_limits: Optional[List[float]]
    :param dq_limits: Charge limits for each step (optional)
    :type dq_limits: Optional[List[float]]
    :param dq_units: Units for charge limits (default: A·h)
    :type dq_units: DQUnits
    :param record_average: Record averaged voltage if True (default: False)
    :type record_average: bool
    :param record_dv_mV: Voltage change threshold for recording (mV, default: 0.0)
    :type record_dv_mV: float
    
    Example::
    
        # Single-step CP at 10 µA for 100 seconds
        cp = CPParameters(
            step_currents=[10e-6],
            step_durations=[100.0],
            record_dt=1.0
        )
        
        # Multi-step CP with voltage limits
        cp_multi = CPParameters(
            step_currents=[10e-6, -10e-6, 10e-6],
            step_durations=[50.0, 50.0, 50.0],
            record_dt=1.0,
            v_limits=[1.0, -1.0, 1.0]
        )
    """
    
    def __post_init__(self):
        # super().__post_init__()
        # Format stepwise settings as lists
        self.step_currents = list(self.step_currents)
        self.step_durations = list(self.step_durations)
        
        # Process stepwise list arguments
        self.listify_attr("i_vs")
        self.listify_attr("record_dt")
        self.listify_attr("v_limits", replace_none="pass")
        # With scaling and unit selection
        self.listify_attr("step_currents", base_unit="A")
        self.listify_attr("dq_limits", base_unit=self.dq_units.value, replace_none=0.0)
        
        # Checks
        if len(self.step_currents) != self.num_steps:
            raise ValueError('Length of step_currents must match length of step_durations')
        for name in ["i_vs", "v_limits", "dq_limits"]:
            if len(getattr(self, name)) != self.num_steps:
                raise ValueError(f'{name} must either be a single value of a list of same length as step_durations')
        
        # TODO: check IRange behavior. Should this be set based only on ac_amp?
        if self.i_range is None:
            self.i_range = get_i_range(np.max(np.abs(self.step_currents)))
            
        if self.num_steps == 1:
            # If there is only one step, we don't write Ns to mps file
            # _param_map is a class attribute, so we need to copy it first
            self._param_map = self._param_map.copy()
            del self._param_map["Ns"]
            
    @property
    def _record(self):
        if self.record_average:
            return "<Ewe>"
        return "Ewe"
   
    @property
    def _step_durations_formatted(self):
        return [format_duration(t) for t in self.step_durations]


@dataclass
class _CAParameters(object):
    """Internal CA (Chronoamperometry) parameter storage.
    
    Base class containing CA-specific parameters. Used with multiple
    inheritance to combine with HardwareParameters.
    
    :param step_voltages: Applied voltage for each step (V)
    :type step_voltages: Union[list, ndarray]
    :param step_durations: Duration of each step (seconds)
    :type step_durations: Union[list, ndarray]
    :param record_dt: Recording time interval (seconds)
    :type record_dt: Union[float, List[float]]
    :param v_vs: Voltage measurement reference (default: EweVs.REF)
    :type v_vs: Union[EweVs, List[EweVs]]
    :param i_limits_min: Minimum current limits for each step (A)
    :type i_limits_min: Optional[List[float]]
    :param i_limits_max: Maximum current limits for each step (A)
    :type i_limits_max: Optional[List[float]]
    :param dq_limits: Charge limits for each step
    :type dq_limits: Optional[List[float]]
    :param dq_units: Units for charge limits (default: DQUnits.AH)
    :type dq_units: DQUnits
    :param record_average: Record averaged current if True (default: False)
    :type record_average: bool
    :param record_di: Current change threshold for recording (A, default: 0.0)
    :type record_di: float
    :param record_dq: Charge change threshold for recording (default: 0.0)
    :type record_dq: float
    :param goto_ns: Loop target step number (default: 0)
    :type goto_ns: int
    :param nc_cycles: Number of loop cycles (default: 0)
    :type nc_cycles: int
    """
    step_voltages: Union[list, ndarray]
    step_durations: Union[list, ndarray]
    record_dt: Union[float, List[float]]
    v_vs: Union[EweVs, List[EweVs]] = EweVs.REF
    i_limits_min: Optional[List[float]] = None
    i_limits_max: Optional[List[float]] = None
    dq_limits: Optional[List[float]] = None
    dq_units: DQUnits = DQUnits.AH
    record_average: bool = False
    record_di: float = 0.0  # mV
    record_dq: float = 0.0
    
    # Placeholders
    goto_ns: int = 0
    nc_cycles: int = 0
    
    technique_name = "Chronoamperometry / Chronocoulometry"
    abbreviation = "CA"
    
    _param_map = merge_dicts(
        {
            'Ns': 'step_index',
            'Ei (V)': 'step_voltages',
            'vs.': 'v_vs',
            'ti (h:m:s)': '_step_durations_formatted',
            'Imax': '_i_limits_max_scaled',
            'unit Imax': '_i_limits_max_unit',
            'Imin': '_i_limits_min_scaled',
            'unit Imin': '_i_limits_min_unit',
            'dQM': '_dq_limits_scaled',
            'unit dQM': '_dq_limits_unit',
            'record': '_record',
            'dI': '_record_di_scaled',
            'unit dI': '_record_di_unit',
            'dQ': '_record_dq_scaled',
            'unit dQ': '_record_dq_unit',
            'dt (s)': 'record_dt',
            'dta (s)': 'record_dt'
        },
        HARDWARE_PARAM_MAP_ILIMIT,
        LOOP_PARAM_MAP
    )
    
    
@dataclass
class CAParameters(HardwareParameters, _CAParameters, ChronoParametersBase, StepwiseTechniqueParameters):
    """Chronoamperometry/Chronocoulometry (CA) technique parameters.
    
    Configures a chronoamperometry measurement that applies constant voltage
    and records the resulting current response. Supports multiple sequential
    voltage steps and current limiting.
    
    :param step_voltages: Applied voltage for each step (V)
    :type step_voltages: Union[list, ndarray]
    :param step_durations: Duration of each step (seconds)
    :type step_durations: Union[list, ndarray]
    :param record_dt: Recording time interval (seconds)
    :type record_dt: Union[float, List[float]]
    :param v_vs: Voltage measurement reference (default: REF)
    :type v_vs: Union[EweVs, List[EweVs]]
    :param i_limits_min: Minimum current limits (A, optional)
    :type i_limits_min: Optional[List[float]]
    :param i_limits_max: Maximum current limits (A, optional)
    :type i_limits_max: Optional[List[float]]
    :param dq_limits: Charge limits for each step (optional)
    :type dq_limits: Optional[List[float]]
    :param dq_units: Units for charge limits (default: A·h)
    :type dq_units: DQUnits
    :param record_average: Record averaged current if True (default: False)
    :type record_average: bool
    :param record_di: Current change threshold for recording (A, default: 0.0)
    :type record_di: float
    :param record_dq: Charge change threshold (default: 0.0)
    :type record_dq: float
    
    Example::
    
        # Single-step CA at 0.5 V for 200 seconds
        ca = CAParameters(
            step_voltages=[0.5],
            step_durations=[200.0],
            record_dt=0.5
        )
        
        # Multi-step CA with current limits
        ca_multi = CAParameters(
            step_voltages=[0.0, 0.5, 1.0],
            step_durations=[100.0, 100.0, 100.0],
            record_dt=1.0,
            i_limits_max=[1e-3, 1e-3, 1e-3]
        )
    """
    
    def __post_init__(self):
        # super().__post_init__()
        
        # Format stepwise settings as lists
        self.step_voltages = list(self.step_voltages)
        self.step_durations = list(self.step_durations)
        
        if self.i_range is None:
            self.i_range = IRange.AUTO
        
        # Process stepwise list arguments
        self.listify_attr("i_range", replace_none=IRange.AUTO)
        for name in ["i_range_min", "i_range_max", "i_range_init"]:
            self.listify_attr(name, replace_none="Unset")
        # self.listify_attr("step_voltages")
        for name in ["v_vs", "record_dt"]:
            self.listify_attr(name)
            
        # With scaling and unit selection
        self.listify_attr("record_di", base_unit="A", replace_none=0.0)
        self.listify_attr("record_dq", base_unit=self.dq_units.value, replace_none=0.0)
        self.listify_attr("i_limits_max", base_unit="A", replace_none="pass")
        self.listify_attr("i_limits_min", base_unit="A", replace_none="pass")
        self.listify_attr("dq_limits", base_unit=self.dq_units.value, replace_none="pass")
        
        # print('num_steps:', self.num_steps)
        # print('step_voltages:', self.step_voltages, len(self.step_voltages))
        
        # Checks
        if len(self.step_voltages) != self.num_steps:
            raise ValueError('Length of step_currents must match length of step_durations')
        for name in ["v_vs", "i_limits_min", "i_limits_max", "dq_limits"]:
            if len(getattr(self, name)) != self.num_steps:
                raise ValueError(f"{name} must either be a single value of a list of same length "
                                 f"as step_durations. Received value: {getattr(self, name)}")
        
        
        if self.num_steps == 1:
            # If there is only one step, we don't write Ns to mps file
            # _param_map is a class attribute, so we need to copy it first
            self._param_map = self._param_map.copy()
            del self._param_map["Ns"]
            
    @property
    def _record(self):
        if self.record_average:
            return "<I>"
        return "I"
   
    @property
    def _step_durations_formatted(self):
        return [format_duration(t) for t in self.step_durations]        
    
    
    
