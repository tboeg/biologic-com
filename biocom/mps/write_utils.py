"""Utility functions for formatting values in MPS files.

This module provides helper functions for converting Python values to the
text format expected by EC-Lab settings files, including numeric formatting,
duration conversion, and decimal separator handling.
"""
import numpy as np
from enum import Enum
from pathlib import Path
from typing import Union


FilePath = Union[Path, str]

_decimal_sep_comma = False

def set_decimal_separator(comma=False):
    """Set decimal separator for numeric formatting.
    
    Configure whether to use comma or period as decimal separator in
    MPS file output. Some locales require comma as decimal separator.
    
    :param comma: Use comma if True, period if False (default: False)
    :type comma: bool
    """
    global _decimal_sep_comma
    _decimal_sep_comma = comma


def float2str(value: float, precision: int):
    """Convert float to string with specified precision.
    
    Formats float with the configured decimal separator (comma or period).
    
    :param value: Float value to format
    :type value: float
    :param precision: Number of decimal places
    :type precision: int
    :return: Formatted string
    :rtype: str
    """
    text = "{x:.{p}f}".format(x=value, p=precision)
    if _decimal_sep_comma:
        return text.replace('.', ',')
    return text


def format_value(value, precision: int = 3):
    """Format any value type for MPS file output.
    
    Handles enums, booleans, floats, and other types with appropriate
    formatting for EC-Lab settings files.
    
    :param value: Value to format (Enum, bool, float, int, or str)
    :param precision: Number of decimal places for floats (default: 3)
    :type precision: int
    :return: Formatted string representation
    :rtype: str
    """
    # Convert enums to values
    if isinstance(value, Enum):
        value = value.value

    # Convert bools to ints
    if isinstance(value, bool):
        return str(int(value))

    # Format floats with appropriate separator
    if isinstance(value, float) or isinstance(value, np.floating):
        return float2str(value, precision)

    # Strings or ints: return raw value
    return str(value)


def split_duration(duration: float):
    """Convert duration in seconds to time components.
    
    Splits duration into hours, minutes, seconds, and milliseconds.
    
    :param duration: Duration in seconds
    :type duration: float
    :return: Tuple of (hours, minutes, seconds, milliseconds)
    :rtype: Tuple[int, int, int, float]
    """
    # Get hours, minutes, seconds
    h = int(duration / 3600.)
    m = int((duration % 3600.) / 60.)
    s = int(duration % 60.)

    # Get milliseconds
    ms = duration % 1
    ms = ms * 1000
    
    return h, m, s, ms

def format_duration(duration: float):
    """Format duration as text for MPS file.
    
    Converts duration in seconds to HH:MM:SS.ssss format with the
    configured decimal separator.
    
    :param duration: Duration in seconds
    :type duration: float
    :return: Formatted duration string (HH:MM:SS.ssss)
    :rtype: str
    
    Example::
    
        >>> format_duration(3661.5)
        '01:01:01.5000'
    """
    # Get hours, minutes, seconds
    h = int(duration / 3600.)
    m = int((duration % 3600.) / 60.)
    s = int(duration % 60.)

    # Get decimal seconds
    ds = round(duration % 1, 4)
    ds = '{:.4f}'.format(ds).split('.')[1]

    text = '{:02}:{:02}:{:02}.{}'.format(h, m, s, ds)
    if _decimal_sep_comma:
        return text.replace('.', ',')
    return text

