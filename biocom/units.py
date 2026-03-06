from typing import Tuple, Optional

class UnitPrefix(object):
    """Handle scaling conversions.
    
    Supports conversion between scaled values (with prefixes like m, k, M) and raw values.
    Includes special handling for the micro (μ) prefix.
    
    :cvar dict scale_map: Mapping from prefix strings to numeric scale factors
    :cvar dict reverse_scale_map: Mapping from scale factors to prefix strings
    :cvar dict chr_map: Mapping from prefix names to special character codes (e.g., 'mu' -> 181 for μ)
    :cvar dict reverse_char_map: Mapping from special characters to prefix names
    """
    scale_map = {
        'G': 1e9,
        'M': 1e6,
        'k': 1e3,
        '': 1,
        'm': 1e-3,
        'mu': 1e-6,
        'n': 1e-9
        }

    scale_map_c_d = {
        'G': 1e9,
        'M': 1e6,
        'k': 1e3,
        '': 1,
        'd': 1e-1,
        'c': 1e-2,
        'm': 1e-3,
        'mu': 1e-6,
        'n': 1e-9
        }

    reverse_scale_map = {v: k for k, v in scale_map.items()}
    reverse_scale_map_c_d = {v: k for k, v in scale_map_c_d.items()}

    chr_map = {
        'mu': 181
    }
    
    reverse_char_map = {chr(v): k for k, v in chr_map.items()}

    def __init__(self, prefix):
        """Initialize a UnitPrefix object.
        
        :param str prefix: Unit prefix string (e.g., 'k', 'm', 'mu') or special character (e.g., 'μ')
        :raises ValueError: If prefix is not recognized
        """

        if prefix not in self.scale_map_c_d.keys():
            try:
                # Look up special characters
                prefix = self.reverse_char_map[prefix]
            except KeyError:
                raise ValueError(f"Unrecognized unit prefix: {prefix}")
        self.prefix = prefix

    @classmethod
    def from_value(cls, value, min_factor=None, max_factor=None, unit_exponent=1, include_centi_deci=False):
        """Select appropriate SI prefix based on the magnitude of a value.
        
        Chooses the largest available scale that is less than or equal to the absolute value.
        
        :param float value: Numeric value to determine prefix for
        :param float min_factor: Minimum scale factor to consider, defaults to None
        :param float max_factor: Maximum scale factor to consider, defaults to None
        :param int exponent: Exponent to apply to value before determining prefix, defaults to 1
        :param bool include_centi_deci: Whether to include centi/deci prefixes in selection
        :return: UnitPrefix object with appropriate prefix
        :rtype: UnitPrefix
        """
        # Get scale options from largest to smallest
        if include_centi_deci:
            scales = list(reversed(sorted(list(cls.reverse_scale_map_c_d.keys()))))
        else:
            scales = list(reversed(sorted(list(cls.reverse_scale_map.keys()))))
        
        # Limit available scales
        if min_factor is not None:
            scales = [s for s in scales if s >= min_factor]
        if max_factor is not None:
            scales = [s for s in scales if s <= max_factor]

        if value == 0 or value is None:
            scale = 1
        else:
            # Set floor on magnitude to ensure that a matching scale is found
            value = max(abs(value), min(scales))
            
            # Determine sign of unit exponent for correct order of scales
            sign = 1 if unit_exponent >= 0 else -1

            # Get largest scale that is less than value or first/last element of scales depending on the sign of the exponent
            scale = next((s for s in scales[::sign] if value >= s**unit_exponent), scales[0 if sign == -1 else -1])

        # Get corresponding prefix
        prefix = cls.reverse_scale_map_c_d[scale]

        return cls(prefix)


    def set_prefix(self, prefix):
        """Set the unit prefix.
        
        :param str prefix: Unit prefix string (must be in scale_map)
        :raises ValueError: If prefix is not valid
        """
        if prefix not in self.scale_map_c_d.keys():
            raise ValueError(f'Invalid prefix {prefix}. Options: {list(self.scale_map_c_d.values())}')

        self._prefix = prefix

    def get_prefix(self):
        """Get the current unit prefix.
        
        :return: Current prefix string
        :rtype: str
        """
        return self._prefix

    prefix = property(get_prefix, set_prefix)

    @property
    def scale(self):
        return self.scale_map_c_d[self.prefix]

    @property
    def char(self):
        if self.chr_map.get(self.prefix, None) is not None:
            return chr(self.chr_map[self.prefix])
        return self.prefix

    def raw_to_scaled(self, raw_value, unit_exponent=1):
        """Convert a raw (base unit) value to a scaled (prefixed unit) value.
        
        :param float raw_value: Value in base units
        :param int unit_exponent: Exponent to apply when scaling (default: 1)
        :return: Value in scaled units, or None if input is None
        :rtype: float or None
        """
        if raw_value is None:
            return None
        return raw_value / self.scale**unit_exponent

    def scaled_to_raw(self, scaled_value, unit_exponent=1):
        """Convert a scaled (prefixed unit) value to a raw (base unit) value.
        
        :param float scaled_value: Value in scaled units
        :param int unit_exponent: Exponent to apply to value when converting back to raw units (default: 1)
        :return: Value in base units, or None if input is None
        :rtype: float or None
        """
        if scaled_value is None:
            return None
        return scaled_value * self.scale**unit_exponent
    

def get_scaled_value(value, unit_exponent=1):
    """Convert a raw value to an appropriately scaled value with automatic prefix selection.
    
    :param float value: Raw numeric value
    :param int unit_exponent: Exponent to apply to value before determining prefix (default: 1)
    :return: Scaled value using automatically selected prefix, or original value if not numeric
    :rtype: float
    """
    try:
        return UnitPrefix.from_value(value, exponent=unit_exponent).raw_to_scaled(value, exponent=unit_exponent)
    except TypeError:
        return value

def get_prefix_char(value, unit_exponent=1):
    """Get the appropriate SI prefix character for a numeric value.
    
    :param float value: Numeric value to determine prefix for
    :param int unit_exponent: Exponent to apply to value before determining prefix (default: 1)
    :return: Prefix character (e.g., 'k', 'm', 'μ'), or empty string if not numeric
    :rtype: str
    """
    try:
        return UnitPrefix.from_value(value, exponent=unit_exponent).char
    except TypeError:
        return ""
    
    
def get_scaled_value_and_prefix(value, min_factor: float = None, max_factor: float = None, unit_exponent: int = 1, include_centi_deci: bool = False) -> Tuple[float, str]:
    """Get both scaled value and prefix character for a numeric value.
    
    :param float value: Raw numeric value
    :param float min_factor: Minimum scale factor to consider, defaults to None
    :param float max_factor: Maximum scale factor to consider, defaults to None
    :param int unit_exponent: Exponent to apply to value before determining prefix (default: 1)
    :return: Tuple of (scaled_value, prefix_char)
    :rtype: Tuple[float, str]
    """
    unit = UnitPrefix.from_value(value, min_factor=min_factor, max_factor=max_factor, unit_exponent=unit_exponent, include_centi_deci=include_centi_deci)
    return unit.raw_to_scaled(value, unit_exponent=unit_exponent), unit.char
    
# Enumerate all possible prefix characters
ALL_PREFIXES = [get_prefix_char(v) for v in UnitPrefix.scale_map_c_d.values()]

 
class TimeUnit(object):
    """Handle time unit conversions between days, hours, minutes, seconds, and milliseconds.
    
    :cvar dict unit_values: Mapping from unit strings to values in seconds
    :cvar dict reverse_value_map: Mapping from values in seconds to unit strings
    """
    
    unit_values = {
        "d": 3600. * 24,
        "h": 3600.,
        "mn": 60.,
        "s": 1.,
        "ms": 1e-3
    }
    
    reverse_value_map = {v: k for k, v in unit_values.items()}
    
    def __init__(self, unit):
        """Initialize a TimeUnit object.
        
        :param str unit: Time unit string ('d', 'h', 'mn', 's', or 'ms')
        :raises ValueError: If unit is not recognized
        """
        self.unit = unit
        
    def set_unit(self, unit):
        """Set the time unit.
        
        :param str unit: Time unit string (must be 'd', 'h', 'mn', 's', or 'ms')
        :raises ValueError: If unit is not valid
        """
        if unit not in self.unit_values.keys():
            raise ValueError(f"Unrecognized unit: {unit}. Options: {list(self.unit_values.keys())}")
        self._unit = unit
        
    def get_unit(self):
        """Get the current time unit.
        
        :return: Current time unit string
        :rtype: str
        """
        return self._unit
    
    unit = property(get_unit, set_unit)
    
    @property
    def value(self):
        return self.unit_values[self.unit]
        
    def convert(self, value: float, output_unit: str):
        """Convert a time value from this unit to another time unit.
        
        :param float value: Time value in the current unit
        :param str output_unit: Target time unit string
        :return: Converted time value
        :rtype: float
        """
        input_val = self.value
        output_val = self.unit_values[output_unit]
        
        return value * input_val / output_val
        
    @classmethod
    def from_value(cls, value: float, input_unit: str = "s"):
        """Select appropriate time unit based on the magnitude of a time value.
        
        Chooses the largest time unit that is less than or equal to the value in seconds.
        
        :param float value: Time value
        :param str input_unit: Unit of the input value, defaults to 's'
        :return: TimeUnit object with appropriate unit
        :rtype: TimeUnit
        """
        # Convert to seconds
        value_s = cls(input_unit).convert(value, "s")
        
        # Get scale options from largest to smallest
        values = reversed(sorted(list(cls.unit_values.values())))

        if value_s == 0 or value_s is None:
            unit_val = 1
        else:
            # Set floor on magnitude
            value_s = max(abs(value_s), 1e-3)
            
            # Get largest scale that is less than value
            unit_val = next(v for v in values if value_s >= v)

        # Get corresponding prefix
        unit = cls.reverse_value_map[unit_val]

        return cls(unit)
    
    @staticmethod
    def split_duration(duration: float):
        """Convert duration in seconds to hours, minutes, seconds, and milliseconds.

        :param float duration: Duration in seconds
        :return: Tuple of (hours, minutes, seconds, milliseconds)
        :rtype: Tuple[float, float, float, float]
        """
        # Get hours, minutes, seconds
        h = int(duration / 3600.)
        m = int((duration % 3600.) / 60.)
        s = int(duration % 60.)

        # Get milliseconds
        ms = duration % 1
        ms = ms * 1000
        
        return h, m, s, ms
    

def get_scaled_time(t: float, input_unit: str = "s") -> Tuple[float, str]:
    """Convert time value to an appropriately scaled time unit.
    
    :param float t: Time value
    :param str input_unit: Unit of the input time, defaults to 's'
    :return: Tuple of (scaled_time_value, time_unit_string)
    :rtype: Tuple[float, str]
    """
    output_unit = TimeUnit.from_value(t, input_unit).unit
    output_value = TimeUnit(input_unit).convert(t, output_unit)
    return output_value, output_unit


# Constants
Faraday = 96485 # C / mol


def coulombs2mAh(q: float) -> float:
    """
    Coulombs to milliamp-hours
    
    :param float q: Charge in Coulombs
    :return float: Charge in mAh
    """
    return q * 1000. / 3600.


def calculate_dqdx(mass: float, mol_wt: float, ne: int) -> float:
    """Calculate change in battery capacity (dq) vs. 
    stoichiometry change (dx).

    :param float mass: Mass of active material in g.
    :param float mol_wt: Molecular weight of active material in g/mol.
    :param int ne: Number of electrons transferred.
    :return float: dq/dx in mAh
    """
    dq = (mass / mol_wt) * ne * Faraday
    return coulombs2mAh(dq)

