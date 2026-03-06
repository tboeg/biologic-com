"""Common enumerations and types for BioLogic device configuration.

This module defines enums and utility functions used throughout the MPS module
for configuring BioLogic electrochemical devices. It includes control modes,
voltage/current ranges, device models, and sample types.
"""
from enum import Enum, StrEnum, auto


def to_sentence_case(x: str):
    """Convert string to sentence case.
    
    Capitalizes the first letter and converts remaining letters to lowercase.
    
    :param x: Input string to convert
    :type x: str
    :return: String in sentence case
    :rtype: str
    """
    return x[0].upper() + x[1:].lower()
    

class SentenceCaseEnum(StrEnum):
    """String enum with automatic sentence case conversion.
    
    An enumeration where the default value is automatically set to the 
    entry name converted to sentence case.
    
    Example:
        >>> class MyEnum(SentenceCaseEnum):
        ...     FIRST_OPTION = auto()
        >>> MyEnum.FIRST_OPTION.value
        'First option'
    """
    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list[str]) -> str:
        return to_sentence_case(name)

class LowerCaseEnum(StrEnum):
    """String enum with automatic lower case conversion.
    
    An enumeration where the default value is automatically set to the 
    entry name converted to lower case.
    
    Example:
        >>> class MyEnum(SentenceCaseEnum):
        ...     FIRST_OPTION = auto()
        >>> MyEnum.FIRST_OPTION.value
        'first option'
    """
    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list[str]) -> str:
        return name.lower()

EweVs = SentenceCaseEnum('EweVs', ['REF', 'EOC', 'ECTRL', 'EMEAS'])
# If potential control is set to Ewe-Ece, then REF becomes CE

    
class ControlMode(StrEnum):
    """Electrochemical control mode enumeration.
    
    :cvar POT: Potentiostatic (voltage control) mode
    :cvar GALV: Galvanostatic (current control) mode
    """
    POT = "Potentiostatic"
    GALV = "Galvanostatic"
    

class IVs(SentenceCaseEnum):
    """Current measurement/control options.
    
    :cvar NONE: No current monitoring
    :cvar ICTRL: Control current
    :cvar IMEAS: Measure current
    """
    NONE  = "<None>"
    ICTRL = auto()
    IMEAS = auto()
    
class TriggerType(StrEnum):
    """Trigger edge type for external triggers.
    
    :cvar RISING: Trigger on rising edge
    :cvar FALLING: Trigger on falling edge
    """
    RISING = "Rising Edge"
    FALLING = "Falling Edge"
    

ChannelGrounding = SentenceCaseEnum("ChannelGrounding", ["FLOATING", "GROUNDED"])

class IRange(StrEnum):
    """Current range settings for BioLogic devices.
    
    Defines available current ranges from 10 nA to 1 A, with automatic
    range selection options.
    
    :cvar AUTO: Automatic range selection
    :cvar AUTOLIMIT: Automatic with limits
    :cvar n10: 10 nA range
    :cvar n100: 100 nA range
    :cvar u1: 1 µA range
    :cvar u10: 10 µA range
    :cvar u100: 100 µA range
    :cvar m1: 1 mA range
    :cvar m10: 10 mA range
    :cvar m100: 100 mA range
    :cvar a1: 1 A range
    """
    AUTO      = "Auto"
    AUTOLIMIT = "Auto Limited"
    n10       = "10 nA"
    n100      = "100 nA"
    u1        = f"1 {chr(181)}A"
    u10       = f"10 {chr(181)}A"
    u100      = f"100 {chr(181)}A"
    m1        = "1 mA"
    m10       = "10 mA"
    m100      = "100 mA"
    a1        = "1 A"
    
    
class Bandwidth(Enum):
    """Bandwidth settings for signal acquisition.
    
    Defines the measurement bandwidth from slow (BW1) to fast (BW9).
    Note that BW8 and BW9 are only available on SP-300 series devices.
    
    :cvar BW1: Bandwidth 1 (slow)
    :cvar BW2: Bandwidth 2
    :cvar BW3: Bandwidth 3
    :cvar BW4: Bandwidth 4
    :cvar BW5: Bandwidth 5 (medium)
    :cvar BW6: Bandwidth 6
    :cvar BW7: Bandwidth 7 (fast)
    :cvar BW8: Bandwidth 8 (SP-300 series only)
    :cvar BW9: Bandwidth 9 (SP-300 series only)
    """
    BW1 = 1  # "Slow"
    BW2 = 2
    BW3 = 3
    BW4 = 4
    BW5 = 5  # "Medium"
    BW6 = 6
    BW7 = 7  # "Fast"
    # NOTE: 8 and 9 only available for SP300 series
    BW8 = 8
    BW9 = 9
    
    
    
class Filter(StrEnum):
    """Low-pass filter frequencies.
    
    Defines available filter settings for signal conditioning.
    Note that filtering is only available on SP-300 series devices.
    
    :cvar NONE: No filtering
    :cvar k50: 50 kHz filter
    :cvar k1: 1 kHz filter
    :cvar h5: 5 Hz filter
    """
    NONE = "<None>"
    k50  = "50 kHz"
    k1   = "1 kHz"
    h5   = "5 Hz"
    
    
class PotentialControl(StrEnum):
    """Potential control mode configuration.
    
    :cvar EWE: Control working electrode potential vs reference
    :cvar EWE_ECE: Control working electrode potential vs counter electrode
    """
    EWE     = "Ewe"
    EWE_ECE = "Ewe-Ece"
    
# TODO: check other cable types
CableType = LowerCaseEnum("CableType", ["STANDARD"])
    
class TurnToOCV(StrEnum):
    TRUE  = "Turn to OCV between techniques"
    FALSE = "Do not turn to OCV between techniques"
    
    @classmethod
    def from_bool(cls, val: bool):
        return getattr(cls, str(val).upper())
    
class ElectrodeConnection(StrEnum):
    """Electrode connection configuration.
    
    :cvar STANDARD: Standard 3-electrode configuration
    :cvar CETOGND: Counter electrode grounded
    :cvar WETOGND: Working electrode grounded
    """
    STANDARD = "standard"
    CETOGND  = "CE to ground"
    WETOGND  = "WE to ground"
    
class CycleDefinition(StrEnum):
    """Battery cycling sequence definition.
    
    :cvar CHARGE_DISCHARGE: Cycle starts with charging
    :cvar DISCHARGE_CHARGE: Cycle starts with discharging
    """
    CHARGE_DISCHARGE = "Charge/Discharge"
    DISCHARGE_CHARGE = "Discharge/Charge"
    
class ReferenceElectrode(StrEnum):
    """Standard reference electrode types with potentials.
    
    Common reference electrodes used in electrochemistry with their
    standard potentials vs. SHE (Standard Hydrogen Electrode).
    
    :cvar NONE: No reference electrode specified
    :cvar AgAgClKCl3_5M: Ag/AgCl in 3.5M KCl (0.205 V)
    :cvar AgAgClKClSat: Ag/AgCl in saturated KCl (0.197 V)
    :cvar AgAgClNaClSat: Ag/AgCl in saturated NaCl (0.194 V)
    :cvar HgHg2SO4K2SO4Sat: Hg/Hg2SO4 in saturated K2SO4 (0.650 V)
    :cvar NHE: Normal Hydrogen Electrode (0.000 V)
    :cvar SCE: Saturated Calomel Electrode (0.241 V)
    :cvar SSCE: Sodium Saturated Calomel Electrode (0.236 V)
    """
    NONE = "(unspecified)"
    AgAgClKCl3_5M = "Ag/AgCl / KCl (3.5M) (0.205 V)"
    AgAgClKClSat = "Ag/AgCl / KCl (sat'd) (0.197 V)"
    AgAgClNaClSat = "Ag/AgCl / NaCl (sat'd) (0.194 V)"
    HgHg2SO4K2SO4Sat = "Hg/Hg2SO4 / K2SO4 (sat'd) (0.650 V)"
    NHE = "NHE Normal Hydrogen Electrode (0.000 V)"
    SCE = "SCE Saturated Calomel Electrode (0.241 V)"
    SSCE = "SSCE Sodium Saturated Calomel Electrode (0.236 V)"
    
    
class SampleType(SentenceCaseEnum):
    """Sample type for electrochemical experiments.
    
    :cvar CORROSION: Corrosion studies
    :cvar BATTERY: Battery/energy storage studies
    :cvar MATERIALS: Materials characterization
    """
    CORROSION = auto()
    BATTERY   = auto()
    MATERIALS = auto()
    
    
class BLDeviceModel(StrEnum):
    """BioLogic device model enumeration.
    
    Supported BioLogic potentiostat/galvanostat models with device-specific
    capabilities for bandwidth and filtering.
    
    :cvar SP150: SP-150 model
    :cvar SP200: SP-200 model
    :cvar SP300: SP-300 model
    :cvar VMP300: VMP-300 model
    :cvar VSP300: VSP-300 model
    """
    SP150 = "SP-150"
    SP200 = "SP-200"
    SP300 = "SP-300"
    VMP300 = "VMP-300"
    VSP300 = "VSP-300"
    
    @property
    def series(self):
        """Get the device series number.
        
        :return: Series number (e.g., 150, 200, 300)
        :rtype: int
        """
        return int(self.value.split('-')[1])
    
    @property
    def max_bandwidth(self):
        """Get maximum supported bandwidth for this device.
        
        :return: Maximum bandwidth value (7 or 9)
        :rtype: int
        """
        if self.series == 300:
            # 300-series go up to 9
            return 9
        else:
            # Other devices only go to 7
            return 7
        
    @property
    def has_filtering(self):
        """Check if device supports signal filtering.
        
        :return: True if device supports filtering
        :rtype: bool
        """
        # Only 300-series devices have filters
        return self.series == 300
    
    def validate_bandwidth(self, bandwidth: Bandwidth):
        """Validate bandwidth setting for this device.
        
        :param bandwidth: Bandwidth setting to validate
        :type bandwidth: Bandwidth
        :raises ValueError: If bandwidth exceeds device maximum
        """
        if Bandwidth.value > self.max_bandwidth:
            raise ValueError(f"The maximum bandwidth for model {self.value} is {self.max_bandwidth}, "
                             f"but a bandwidth of {bandwidth.value} was specified.")
            
    def validate_filter(self, filtering: Filter):
        """Validate filter setting for this device.
        
        :param filtering: Filter setting to validate
        :type filtering: Filter
        :raises ValueError: If filtering not supported by device
        """
        if (not self.has_filtering) and filtering != Filter.NONE:
            raise ValueError(f"Filtering is not available for model {self.value}.")
    
    
def get_i_range(i_max: float):
    """Select appropriate current range based on maximum current.
    
    Automatically selects the smallest current range that can accommodate
    the specified maximum current value.
    
    :param i_max: Maximum absolute current expected (A)
    :type i_max: float
    :return: Appropriate current range setting
    :rtype: IRange
    """
    i_max = abs(i_max)
    
    if i_max < 1e-8:
        return IRange.n10
    elif i_max < 1e-7:
        return IRange.n100
    elif i_max < 1e-6:
        return IRange.u1
    elif i_max < 10e-6:
        return IRange.u10
    elif i_max < 100e-6:
        return IRange.u100
    elif i_max < 1e-3:
        return IRange.m1
    elif i_max < 1e-2:
        return IRange.m10
    elif i_max < 1e-1:
        return IRange.m100
    else:
        return IRange.a1


class DQUnits(Enum):
    """Charge/capacity units.
    
    :cvar C: Coulombs
    :cvar AH: Ampere-hours
    """
    C   = "C"
    # mC  = "mC"
    AH  = "A.h"
    
    
    
    



    
  