"""Electrochemical Impedance Spectroscopy (EIS) technique parameters.

This module provides parameter classes for configuring EIS measurements
including PEIS (Potentiostatic EIS) and GEIS (Galvanostatic EIS). EIS
measures impedance as a function of frequency by applying small AC signals.
"""
from enum import StrEnum
from dataclasses import dataclass
from typing import Union
import numpy as np

from ... import units
from .technique import HardwareParameters, TechniqueParameters, HARDWARE_PARAM_MAP
from ..common import (
    SentenceCaseEnum, EweVs, IVs, IRange, get_i_range
)
from ..write_utils import format_duration
from ...utils import merge_dicts


class FrequencySpacing(StrEnum):
    LIN = "Linear"
    LOG = "Logarithmic"
    
class PointDensity(StrEnum):
    PPD = "per decade"
    TOT = "from fi to ff"
    
GEISAmpVariable = SentenceCaseEnum("GEISAmpVariable", ["IA", "VA"])

def parse_frequency(f: float):
    """Parse frequency and select appropriate unit prefix.
    
    :param f: Frequency in Hz
    :type f: float
    :return: Scaled frequency value and unit string (e.g., 'kHz')
    :rtype: Tuple[float, str]
    """
    prefix = units.UnitPrefix.from_value(f)
    f_scaled = prefix.raw_to_scaled(f)
    return f_scaled, f'{prefix.prefix}Hz'



def get_freq_duration_scalar(f: float):
    """Get measurement duration for a single frequency.
    
    Uses minimum period of 0.3s for frequencies above 5 Hz,
    otherwise uses 1/f.

    :param f: Frequency in Hz
    :type f: float
    :return: Duration in seconds
    :rtype: float
    """
    # Frequency above which duration is fixed
    f_cut = 5
    # Minimum period for frequencies above f_cut
    p_min = 0.3
    # Effective period
    return p_min if f > f_cut else 1 / f
    

get_freq_duration = np.vectorize(get_freq_duration_scalar)


def estimate_duration(f_min: float, f_max: float, points: int, average: int, wait: float, point_density: PointDensity = PointDensity.PPD) -> float:
    """Estimate the duration of an EIS measurement.

    :param f_min: Minimum frequency (Hz)
    :type f_min: float
    :param f_max: Maximum frequency (Hz)
    :type f_max: float
    :param points: Number of points (per decade if PPD, total if TOT)
    :type points: int
    :param average: Number of cycles to average
    :type average: int
    :param wait: Number of periods to wait between measurements
    :type wait: float
    :param point_density: Point density mode (default: PPD)
    :type point_density: PointDensity
    :return: Total duration in seconds
    :rtype: float
    """
    if point_density == PointDensity.PPD:
        n_decades = np.log10(f_max / f_min)
        points = int(n_decades * points) + 1
    
    freq = np.logspace(f_max, f_min, points)
        
    
    durations = get_freq_duration(freq) * (average + wait)
    return np.sum(durations)
    

@dataclass
class _EISParameters(TechniqueParameters):
    """Base class for EIS parameters. Do not use directly - 
    instead, use either PEISParameters or GEISParameters"""
    dc_value: float
    ac_amp: float
    dc_vs: Union[EweVs, IVs]
    
    f_max: float 
    f_min: float
    points: int = 10
    
    # _f_max: float = field(init=False, repr=False)
    # _f_min: float = field(init=False, repr=False)
    
    point_density: PointDensity = PointDensity.PPD
    
    condition_time: float = 0.0
    record_conditioning: bool = False
    record_dt: float = 1.0
    record_ds: float = 0.0
    
    spacing: FrequencySpacing = FrequencySpacing.LOG
    # v_range_min: float = -10
    # v_range_max: float = 10
    # i_range: Optional[IRange] = None
    # bandwidth: Bandwidth = Bandwidth.BW5
    average: int = 2
    repeat: int = 0
    wait: float = 0.1
    multisine: bool = False
    drift_correction: bool = False
    
    goto_ns: int = 0
    nr_cycles: int = 0
    inc_cycle: int = 0
    # param_map: dict = field(default_factory=dict)
    
    def __post_init__(self):
        if self.multisine:
            self.excitation_signal_mode = "Multi sine"
        else:
            self.excitation_signal_mode = "Single sine"
            
        if self.i_range is None:
            self.i_range = IRange.AUTO
            
        # # Process frequencies
        # self.fi_scaled, self.fi_unit = self.parse_frequency(self.f_max)
        # self.ff_scaled, self.ff_unit = self.parse_frequency(self.f_min)
        
        # Placeholders
        # self.goto_ns = 0
        # self.nr_cycles = 0
        # self.inc_cycle = 0
        
    def _set_frequency(self, value: float, which: str):
        raw_name = f'_f_{which}'
        if which == 'min':
            name = 'ff'
        else:
            name = 'fi'
            
        f_scaled, f_unit = parse_frequency(value)
        setattr(self, f'{name}_scaled', f_scaled) 
        setattr(self, f'{name}_unit', f_unit) 
        setattr(self, raw_name, value)
    
    def _set_f_max(self, value: float):
        return self._set_frequency(value, 'max')
    
    def _set_f_min(self, value: float):
        return self._set_frequency(value, 'min')
        
    def _get_f_max(self):
        return self._f_max
    
    def _get_f_min(self):
        return self._f_min
    
    f_max = property(_get_f_max, _set_f_max)
    
    f_min = property(_get_f_min, _set_f_min)
        
    # @staticmethod
    @property
    def expected_duration(self):
        return estimate_duration(self.f_min, self.f_max, self.points, self.average, self.wait, point_density=self.point_density)
    
    @property
    def _condition_time_formatted(self):
        return format_duration(self.condition_time)
        
        
    
    
@dataclass
class PEISParameters(HardwareParameters, _EISParameters):
    # ewe_dc: float
    dc_vs: EweVs
    # v_ac: float
    
    technique_name = "Potentio Electrochemical Impedance Spectroscopy"
    abbreviation = "PEIS"
    
    # record_di: float = 1e-3
    _param_map = merge_dicts(
        {
            "Mode": "excitation_signal_mode",
            "E (V)": "dc_value",
            "vs.": "dc_vs",
            "tE (h:m:s)": "_condition_time_formatted",
            "record": "record_conditioning",
            "dI": "di_scaled",
            "unit dI": "di_unit",
            "dt (s)": "record_dt",              
            "fi": "fi_scaled",
            "unit fi": "fi_unit",
            "ff": "ff_scaled",
            "unit ff": "ff_unit",
            "Nd": "points",
            "Points": "point_density",
            "spacing": "spacing",
            "Va (mV)": "vac_mv",
            "pw": "wait",
            "Na": "average",
            "corr": "drift_correction",
            # "E range min (V)": "v_range_min",
            # "E range max (V)": "v_range_max",
            # "I Range": "i_range",
            # "Bandwidth": "bandwidth",
            # "nc cycles": "repeat",
            # "goto Ns'": "goto_ns",
            # "nr cycles": "nr_cycles",
            # "inc. cycle": "inc_cycle"
        },
        HARDWARE_PARAM_MAP,
        {
            "nc cycles": "repeat",
            "goto Ns'": "goto_ns",
            "nr cycles": "nr_cycles",
            "inc. cycle": "inc_cycle"
        }
    )

    @property
    def vac_mv(self):
        return self.ac_amp * 1000
    
    @property
    def di_scaled(self):
        return units.get_scaled_value(self.record_ds)
    
    @property
    def di_unit(self):
        return units.get_prefix_char(self.record_ds) + "A"
    
    
    
@dataclass
class GEISParameters(HardwareParameters, _EISParameters):
    dc_vs: IVs
    ac_amp_variable: GEISAmpVariable = GEISAmpVariable.IA
    
    technique_name = 'Galvano Electrochemical Impedance Spectroscopy'
    abbreviation = "GEIS"
    
    _param_map = {
        "Mode": "excitation_signal_mode",
        "Is": "idc_scaled",
        "unit Is": "idc_unit",
        "vs.": "dc_vs",
        "tIs (h:m:s)": "_condition_time_formatted",
        "record": "record_conditioning",
        "dE (mV)": "de_mv",
        "dt (s)": "record_dt",              
        "fi": "fi_scaled",
        "unit fi": "fi_unit",
        "ff": "ff_scaled",
        "unit ff": "ff_unit",
        "Nd": "points",
        "Points": "point_density",
        "spacing": "spacing",
        "Ia/Va": "ac_amp_variable",
        "Ia": "iac_scaled",
        "unit  Ia": "iac_unit",
        "va pourcent": "va_pct",
        "pw": "wait",
        "Na": "average",
        "corr": "drift_correction",
        "E range min (V)": "v_range_min",
        "E range max (V)": "v_range_max",
        "I Range": "i_range",
        "Bandwidth": "bandwidth",
        "nc cycles": "repeat",
        "goto Ns'": "goto_ns",
        "nr cycles": "nr_cycles",
        "inc. cycle": "inc_cycle"
    }
    
    def __post_init__(self):
        # TODO: check IRange behavior. Should this be set based only on ac_amp?
        # print("I range:", self.i_range)
        if self.i_range is None:
            self.i_range = get_i_range(abs(self.ac_amp))
            
        super().__post_init__()
        
        
        print("GEIS I range:", self.i_range)
        
        # Placeholders
        self.va_pct = 0.1
        
        print("GEIS Iac:", self.iac_scaled, self.iac_unit)
        
        
    @property
    def idc_scaled(self):
        return units.get_scaled_value(self.dc_value)
    
    @property
    def idc_unit(self):
        return units.get_prefix_char(self.dc_value) + "A"
    
    @property
    def iac_scaled(self):
        return units.get_scaled_value(self.ac_amp)
    
    @property
    def iac_unit(self):
        if self.ac_amp_variable == GEISAmpVariable.IA:
            base_unit = "A"
        else:
            base_unit = "V"
        return units.get_prefix_char(self.ac_amp) + base_unit
        
    
    @property
    def de_mv(self):
        return self.record_ds * 1000
    
    

