"""Galvanostatic Cycling with Potential Limitation (GCPL) technique.

This module provides parameter classes for configuring GCPL measurements,
commonly used for battery cycling and electrochemical testing. GCPL applies
constant current with voltage limits to prevent over-charging or over-discharging.
"""

from enum import Enum
from dataclasses import dataclass
from numpy import ndarray
from typing import Union, Optional, List

from .stepwise import StepwiseTechniqueParameters

from ..common import (
    IVs, get_i_range, DQUnits
)
from ..config import FullConfiguration, BatteryCharacteristics
from .technique import (
    HardwareParameters, HARDWARE_PARAM_MAP, HARDWARE_PARAM_MAP_ILIMIT, LOOP_PARAM_MAP
)
from ..write_utils import format_duration
from ...utils import merge_dicts, isiterable


class CurrentSpec(Enum):
    """Current specification mode for GCPL.
    
    :cvar I: Absolute current value
    :cvar CDN: C-rate divided by N (C/N)
    :cvar CTN: C-rate multiplied by N (C×N)
    """
    I = "I"
    CDN = "C / N"
    CTN = "C x N"
    
    
    
def convert_current_scalar(i_in: float, current_spec: CurrentSpec, q_theo: float):
    """Convert current specification to absolute current.
    
    :param i_in: Input current or C-rate multiplier
    :type i_in: float
    :param current_spec: Current specification mode
    :type current_spec: CurrentSpec
    :param q_theo: Theoretical battery capacity (A·h)
    :type q_theo: float
    :return: Absolute current in A
    :rtype: float
    """
    # Get current in A based on battery capacity
    if current_spec == CurrentSpec.CTN:
        # i_in is N value (C x N)
        i_A = q_theo * i_in
    elif current_spec == CurrentSpec.CDN:
        # i_in is N value (C / N)
        i_A = q_theo / i_in
    else:
        # i_in is absolute current value in A
        i_A = i_in
    return i_A

def convert_currents(i_in, current_spec: List[CurrentSpec], q_theo: float):
    """Convert list of current specifications to absolute currents.
    
    :param i_in: Input currents or C-rate multipliers
    :param current_spec: List of current specification modes
    :type current_spec: List[CurrentSpec]
    :param q_theo: Theoretical battery capacity (A·h)
    :type q_theo: float
    :return: List of absolute currents in A
    :rtype: list
    """
    if isiterable(i_in):
        i_in = list(i_in)
        
    return [convert_current_scalar(i, cs, q_theo) for i, cs in zip(i_in, current_spec)]


@dataclass
class _GCPLParameters(object):
    
    current_spec: Union[CurrentSpec, List[CurrentSpec]]
    step_currents: Union[List[float], ndarray]
    # current_signs: Union[List[int], ndarray]
    step_durations: Union[List[float], ndarray]
    E_M: Union[List[float], ndarray]
    dE1: Union[List[float], ndarray]
    dt1: Union[List[float], ndarray]
    
    # For E_m hold
    t_M: Optional[Union[List[float], ndarray]] = None
    I_m: Optional[List[float]] = None
    dIdt_m: Optional[List[float]] = None
    dQ: Optional[List[float]] = None
    dt_q: Optional[List[float]] = None
    
    # Limits
    dQ_m: Optional[Union[List[float], ndarray]] = None
    dx_m: Optional[Union[List[float], ndarray]] = None
    dSoC: Optional[Union[List[float], ndarray]] = None
    
    # Final rest period
    t_R: Optional[Union[List[float], ndarray]] = None
    dEdt_R: Optional[Union[List[float], ndarray]] = None
    dE_R: Optional[Union[List[float], ndarray]] = None
    dt_R: Optional[Union[List[float], ndarray]] = None
    
    
    E_L: Optional[float] = None
    i_vs: Union[IVs, List[IVs]] = IVs.NONE
    dq_units: DQUnits = DQUnits.AH
    
    
    # Placeholders
    goto_ns: int = 0
    nc_cycles: int = 0
    
    technique_name = "Galvanostatic Cycling with Potential Limitation"
    abbreviation = "GCPL"
    
    _param_map = merge_dicts(
        {
            "Ns": "step_index",
            "Set I/C": "current_spec",
            "Is": "_step_i_A_scaled",
            "unit Is": "_step_i_A_unit",
            "vs.": "i_vs",
            "N": "N",
            "I sign": "_i_signs_formatted",
            "t1 (h:m:s)": "_step_durations_formatted",
        },
        {k: HARDWARE_PARAM_MAP[k] for k in ["I Range", "Bandwidth"]},
        {
            "dE1 (mV)": "dE1",
            "dt1 (s)": "dt1",
            "EM (V)": "E_M",
            "tM (h:m:s)": "_t_M_formatted",
            "Im": "_I_m_scaled",
            "unit Im": "_I_m_unit",
            "dI/dt": "_dIdt_m_scaled",
            "dunit dI/dt": "_dIdt_m_unit",
        },
        {k: HARDWARE_PARAM_MAP[k] for k in ["E range min (V)", "E range max (V)"]},
        {
            "dq": "_dQ_scaled",
            "unit dq": "_dQ_unit",
            "dtq (s)": "dt_q",
            "dQM": "_dQ_m_scaled",
            "unit dQM": "_dQ_m_unit",
            "dxM": "dx_m",
            "delta SoC (%)": "dSoC",
            "tR (h:m:s)": "_t_R_formatted",
            "dER/dt (mV/h)": "dEdt_R",
            "dER (mV)": "dE_R",
            "dtR (s)": "dt_R" ,
            "EL (V)": "E_L",
        },
        LOOP_PARAM_MAP
    )
    
@dataclass
class GCPLParameters(HardwareParameters, _GCPLParameters, StepwiseTechniqueParameters):
    
    @property
    def _step_durations_formatted(self):
        return [format_duration(t) for t in self.step_durations]
    
    @property
    def _t_M_formatted(self):
        return [format_duration(t) for t in self.t_M]
    
    @property
    def _t_R_formatted(self):
        return [format_duration(t) for t in self.t_R]
    
    @property
    def num_steps(self):
        return len(self.step_durations)
    
    @property
    def N(self):
        def get_N(x, current_spec: CurrentSpec):
            if current_spec in (CurrentSpec.CTN, CurrentSpec.CDN):
                return abs(x)
            return 1.0
        return [get_N(x, cs) for x, cs in zip(self.step_currents, self.current_spec)]
    
    @property
    def _i_signs_formatted(self):
        return ["> 0" if s >= 0 else "< 0" for s in self.step_currents]
        
        
    def apply_configuration(self, configuration: FullConfiguration):
        if not isinstance(configuration.sample, BatteryCharacteristics):
            raise TypeError("Sample type must be Battery for GCPL (SampleType.BATTERY or BatteryCharacteristics)")

        config: BatteryCharacteristics = configuration.sample
        
        # Get theoretical capacity in Ah
        self._Q_theo = config.capacity_mAh * 1e-3
        
        self.step_i_A = convert_currents(self.step_currents, self.current_spec, self._Q_theo)
            
        self.listify_attr("step_i_A", base_unit="A")
        
        # Set IRange automatically
        if self.i_range is None:
            self.i_range = [get_i_range(abs(i)) for i in self.step_i_A]
    
    
    def __post_init__(self):
        # super().__post_init__()
        # Format stepwise settings as lists
        self.step_currents = list(self.step_currents)
        self.step_durations = list(self.step_durations)
        # self.current_signs = list(self.current_signs)
        self.E_M = list(self.E_M)
        
        # Initialize
        self.step_i_A = None
        
        # Process stepwise list arguments
        # current_spec: List[CurrentSpec]
        # step_currents: Union[List[float], ndarray]
        # step_durations: Union[List[float], ndarray]
        # E_m: Union[List[float], ndarray]
        # dE1: Union[List[float], ndarray]
        # dt1: Union[List[float], ndarray]
        
        # # For E_m hold
        # tM: Optional[Union[List[float], ndarray]] = None
        # I_m: Optional[List[float]] = None
        # didt_m: Optional[List[float]] = None
        # dQ: Optional[List[float]] = None
        # dt_q: Optional[List[float]] = None
        
        # # Limits
        # dQ_m: Optional[Union[List[float], ndarray]] = None
        # dx_m: Optional[Union[List[float], ndarray]] = None
        # dSoc: Optional[Union[List[float], ndarray]] = None
        
        # # Final rest period
        # t_R: Optional[Union[List[float], ndarray]] = None
        # dEdt_R: Optional[Union[List[float], ndarray]] = None
        # dE_R: Optional[Union[List[float], ndarray]] = None
        # dt_R: Optional[Union[List[float], ndarray]] = None
        
        
        # E_L: Optional[float] = None
        # i_vs: Union[IVs, List[IVs]] = IVs.NONE
        # v_limits: Optional[List[float]] = None
        # dq_limits: Optional[List[float]] = None
        # dq_units: DQUnits = DQUnits.AH
        
        # Main box
        for name in [
            "step_currents",
            "i_vs",
            "current_spec",
            "E_M",
            "dE1",
            "dt1"
        ]:
            self.listify_attr(name)
        
            
        # For EM hold
        self.listify_attr("t_M", replace_none=0.0)
        self.listify_attr("I_m", replace_none=0.0, base_unit="A")
        self.listify_attr("dIdt_m", replace_none=0.0, base_unit="A/s")
        self.listify_attr("dQ", replace_none=0.0, base_unit=self.dq_units.value)
        self.listify_attr("dt_q", replace_none=0.0)
        
        # Limits
        self.listify_attr("dQ_m", replace_none=0.0, base_unit=self.dq_units.value)
        self.listify_attr("dx_m", replace_none=0.0)
        self.listify_attr("dSoC", replace_none="pass")
        
        # Final rest period
        self.listify_attr("t_R", replace_none=0.0)
        self.listify_attr("dEdt_R", replace_none=0.0)
        self.listify_attr("dE_R", replace_none=0.0)
        self.listify_attr("dt_R", replace_none=0.0)
        
        self.listify_attr("E_L", replace_none="pass")
        

        
        # Checks
        if len(self.step_currents) != self.num_steps:
            raise ValueError("Length of step_currents must match length of step_durations")
        # TODO: update checks
        for name in ["i_vs"]:
            if len(getattr(self, name)) != self.num_steps:
                raise ValueError(f"{name} must either be a single value of a list of same length as step_durations")
        
        
            
        if self.num_steps == 1:
            # If there is only one step, we don't write Ns to mps file
            # _param_map is a class attribute, so we need to copy it first
            self._param_map = self._param_map.copy()
            del self._param_map["Ns"]
            
    

        