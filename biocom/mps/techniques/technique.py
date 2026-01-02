"""Base classes for electrochemical technique parameters.

This module defines the base classes and utilities used by all specific
technique parameter classes. It provides common hardware parameters,
parameter mapping, and text formatting functionality.
"""
from dataclasses import dataclass
from typing import Optional

from ..common import Bandwidth, IRange, Filter
from ..config import FullConfiguration
from ..write_utils import format_value


# Column width for parameter tables
FIXED_WIDTH = 20


def pad_text(text):
    """Pad text to fixed column width.
    
    :param text: Text to pad
    :type text: str
    :return: Padded text
    :rtype: str
    """
    p = FIXED_WIDTH - len(text)
    return text + ' ' * p

def value2str(value):
    """Convert value to padded string.
    
    :param value: Value to convert
    :return: Formatted and padded string
    :rtype: str
    """
    return pad_text(format_value(value))


@dataclass
class HardwareParameters(object):
    """Common hardware parameters for electrochemical techniques.
    
    Defines hardware settings that can be configured for any technique,
    including voltage/current ranges, bandwidth, and filtering.
    
    :param v_range_min: Minimum voltage range (V, default: -10.0)
    :type v_range_min: float
    :param v_range_max: Maximum voltage range (V, default: 10.0)
    :type v_range_max: float
    :param i_range: Current range setting
    :type i_range: Optional[IRange]
    :param i_range_min: Minimum current range for auto-limited mode
    :type i_range_min: Optional[IRange]
    :param i_range_max: Maximum current range for auto-limited mode
    :type i_range_max: Optional[IRange]
    :param i_range_init: Initial current range for auto-limited mode
    :type i_range_init: Optional[IRange]
    :param bandwidth: Measurement bandwidth (default: BW7)
    :type bandwidth: Bandwidth
    :param filtering: Signal filter setting (default: NONE)
    :type filtering: Filter
    """
    v_range_min: float = -10.0
    v_range_max: float = 10.0
    i_range: Optional[IRange] = None
    i_range_min: Optional[IRange] = None
    i_range_max: Optional[IRange] = None
    i_range_init: Optional[IRange] = None
    bandwidth: Bandwidth = Bandwidth.BW7
    filtering: Filter = Filter.NONE
    
    @property
    def i_range_min_(self):
        return self.i_range_min or "Unset"
    
    @property
    def i_range_max_(self):
        return self.i_range_max or "Unset"
    
    @property
    def i_range_init_(self):
        return self.i_range_init or "Unset"
    
    # def apply(self, other: object):
    #     """Apply settings from this instance to a TechniqueParameters
    #     instance.

    #     :param TechniqueParameters other: _description_
    #     """
    #     for name in self.__dataclass_fields__.keys():
    #         setattr(other, name, getattr(self, name))


HARDWARE_PARAM_MAP = {
    "E range min (V)": "v_range_min",
    "E range max (V)": "v_range_max",
    "I Range": "i_range",
    "Bandwidth": "bandwidth",
}

# For techniques that allow Auto Limited IRange,
# such as CA
HARDWARE_PARAM_MAP_ILIMIT = {
    "E range min (V)": "v_range_min",
    "E range max (V)": "v_range_max",
    "I Range": "i_range",
    "I Range min": "i_range_min_",
    "I Range max": "i_range_max_",
    "I Range init": "i_range_init_",
    "Bandwidth": "bandwidth",
}

LOOP_PARAM_MAP = {
    "goto Ns'": "goto_ns",
    "nc cycles": "nc_cycles"
}



class TechniqueParameters(object):
    """Base class for all technique parameter classes.
    
    Provides common functionality for formatting technique parameters
    to MPS file format, including parameter mapping and text generation.
    
    :ivar _param_map: Dictionary mapping MPS field names to class attributes
    :vartype _param_map: dict
    :ivar technique_name: Full name of the technique
    :vartype technique_name: str
    :ivar abbreviation: Abbreviated technique name
    :vartype abbreviation: str
    
    Note:
        Subclasses should define _param_map, technique_name, and abbreviation.
    """
    _param_map: dict
    
    technique_name: str
    abbreviation: str
    
    def key2str(self, key):
        """Convert parameter key-value pair to formatted string.
        
        :param key: Parameter key from _param_map
        :type key: str
        :return: Formatted parameter line
        :rtype: str
        """
        attr = self._param_map[key]
        return f'{pad_text(key)}{value2str(getattr(self, attr))}'
    
    def apply_configuration(self, configuration: FullConfiguration):
        """Apply configuration settings to technique parameters.
        
        For techniques that need information from device/sample configuration.
        Default implementation does nothing; override in subclasses as needed.
        
        :param configuration: Full experiment configuration
        :type configuration: FullConfiguration
        """
        # For techniques that pull information from device/sample configuration
        # By default, do nothing
        pass
    
    def param_text(self, technique_number: int):
        """Generate formatted parameter text for MPS file.
        
        :param technique_number: Technique sequence number (1-indexed)
        :type technique_number: int
        :return: Formatted parameter block
        :rtype: str
        """        
        # Formatted parameters
        text_list = [
            self.key2str(key)
            for key in self._param_map.keys()
        ]
        return '\n'.join(text_list)

    