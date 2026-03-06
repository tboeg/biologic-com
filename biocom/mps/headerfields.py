"""Header field formatting for BioLogic MPS files.

This module provides classes for formatting header fields in EC-Lab settings
files (.mps). Each field class handles the conversion of Python values to
the specific text format expected by EC-Lab.

The module includes field types for:
    - Simple labeled values
    - Optional fields (only written if non-default)
    - Boolean checkbox fields
    - File paths
    - Multi-line text
    - Ranges and multi-value fields
"""
from pathlib import Path
from typing import Any, Union, Optional, List, NamedTuple, Tuple

from .common import BLDeviceModel, ReferenceElectrode
from .write_utils import format_value
from .. import units


class HeaderFieldUnit(NamedTuple):
    """Named tuple describing unit handling for a header field.

    :param text: Unit string (e.g. 'mV', 'g', 'cm')
    :type text: str
    :param unit_exponent: Exponent applied to the base unit (e.g. -2 for cm^-2)
    :type unit_exponent: int
    :param scale_value: Whether the value should be scaled with SI prefixes
    :type scale_value: bool
    :param factor_range: Optional (min, max) factor limits to constrain scaling
    :type factor_range: Optional[Tuple[float, float]]
    :param include_centi_deci: Whether to include centi/deci prefixes
    :type include_centi_deci: bool
    """
    text: str
    unit_exponent: int = 1
    scale_value: bool = False
    factor_range: Optional[Tuple[float, float]] = None
    include_centi_deci: bool = False

class HeaderField(object):
    """Base class for MPS file header fields.
    
    Handles formatting of labeled values for EC-Lab settings files with
    configurable separators, units, precision, and device compatibility.
    
    :param label: Field label text
    :type label: str
    :param units: Optional unit string to append
    :type units: Optional[str]
    :param exponent: Exponent to apply when determining unit prefix (default: 1)
    :type exponent: int
    :param separator: Text between label and value (default: ' : ')
    :type separator: str
    :param precision: Number of decimal places for floats (default: 3)
    :type precision: int
    :param add_linebreak: Add extra newline after field (default: False)
    :type add_linebreak: bool
    :param devices: List of compatible devices, or None for all (default: None)
    :type devices: Optional[List[BLDeviceModel]]
    """
    def __init__(
            self, 
            label: str, 
            units: Optional[HeaderFieldUnit] = None,
            separator: str = ' : ', 
            precision: int = 3,
            add_linebreak: bool = False,
            devices: Optional[List[BLDeviceModel]] = None
                 ) -> None:
        self.label = label
        self.units = units
        self.separator = separator
        self.precision = precision
        self.add_linebreak = add_linebreak
        self.devices = devices
        
    def check_device(self, device: BLDeviceModel):
        """Check if field applies to the specified device.
        
        :param device: BioLogic device model
        :type device: BLDeviceModel
        :return: True if field is compatible with device
        :rtype: bool
        """
        # Check if this field applies to the selected device
        if self.devices is not None:
            if device not in self.devices:
                return False
        return True
        
    def __call__(self, value, device: BLDeviceModel) -> str:
        """Format field as text string for MPS file.
        
        :param value: Value to format
        :param device: BioLogic device model
        :type device: BLDeviceModel
        :return: Formatted text string, or None if not applicable
        :rtype: Optional[str]
        """
        # If the field is not relevant to the device type,
        # return None
        if not self.check_device(device):
            return None
        
        # For float values, scale the value and apply unit prefix
        formatted_value = value
        unit_string = self.units.text if self.units is not None else ""
        
        if isinstance(value, float) and self.units.scale_value == True:
            scaled_value, prefix_char = units.get_scaled_value_and_prefix(value, *self.units.factor_range, self.units.unit_exponent, self.units.include_centi_deci)
            formatted_value = scaled_value
            unit_string = f"{prefix_char}{self.units.text}"
        text = '{}{}{}'.format(self.label, self.separator, format_value(formatted_value, self.precision))
        if unit_string:
            if unit_string == 'dm³':
                unit_string = 'L'
            text += f' {unit_string}'
        
        if self.add_linebreak:
            text += "\n"
            
        return text
    
class OptionalField(HeaderField):
    """Header field that only appears for non-default values.
    
    Similar to HeaderField but suppresses output when value equals
    the default value (e.g., reference electrode when set to None).
    
    :param label: Field label text
    :type label: str
    :param default_value: Value to suppress (field not written)
    :param units: Optional unit string to append
    :type units: Optional[str]
    :param separator: Text between label and value (default: ' : ')
    :type separator: str
    :param precision: Number of decimal places for floats (default: 3)
    :type precision: int
    :param add_linebreak: Add extra newline after field (default: False)
    :type add_linebreak: bool
    :param devices: List of compatible devices, or None for all
    :type devices: Optional[List[BLDeviceModel]]
    """
    def __init__(
            self, 
            label: str, 
            default_value,
            units: str | None = None, 
            separator: str = ' : ', 
            precision: int = 3, 
            add_linebreak: bool = False,
            devices: Optional[List[BLDeviceModel]] = None
            ) -> None:
        
        super().__init__(label, units, separator, precision, add_linebreak, devices)
        self.default_value = default_value
        
    def __call__(self, value, device: BLDeviceModel) -> str:
        if value == self.default_value:
            return None
        return super().__call__(value, device)
    
class CheckboxField(HeaderField):
    """Header field for checkbox with variable value.
    
    Field only appears if checkbox is checked (value is not None),
    and displays the associated value.
    
    :param value: Value to write, or None if unchecked
    :param device: BioLogic device model
    :type device: BLDeviceModel
    :return: Formatted field text or None
    :rtype: Optional[str]
    """
    # For fields that appear only if a box is checked
    # and specify a variable value
    def __call__(self, value, device: BLDeviceModel) -> str:
        if value is None:
            # value of None indicates that box is not checked
            return None
        return super().__call__(value, device)
    
class BooleanCheckboxField(HeaderField):
    """Header field for simple boolean checkbox.
    
    Field appears only if checkbox is checked (value is True),
    displaying just the label with no additional value.
    
    :param label: Field label text
    :type label: str
    :param add_linebreak: Add extra newline after field (default: False)
    :type add_linebreak: bool
    :param devices: List of compatible devices, or None for all
    :type devices: Optional[List[BLDeviceModel]]
    """
    # For fields that appear only if a box is checked,
    # and always have the same value if checked
    def __init__(self, 
            label: str, 
            add_linebreak: bool = False, 
            devices: List[BLDeviceModel] | None = None) -> None:
        super().__init__(label, None, "", 1, add_linebreak, devices)
        
    def __call__(self, value: bool, device: BLDeviceModel) -> str:
        """Format boolean checkbox field.
        
        :param value: True if checked, False otherwise
        :type value: bool
        :param device: BioLogic device model
        :type device: BLDeviceModel
        :return: Label text if checked, None otherwise
        :rtype: Optional[str]
        """
        if not value:
            # value of None of False indicates that box is not checked
            return None
        # Value of True indicates box is checked; 
        # no text should be added to label
        return super().__call__('', device)
    
    
class PathField(HeaderField):
    """Header field for file paths.
    
    Automatically converts path to absolute path before formatting.
    
    :param value: File path (string or Path object)
    :param device: BioLogic device model
    :type device: BLDeviceModel
    :return: Formatted field with absolute path
    :rtype: Optional[str]
    """
    def __call__(self, value, device: BLDeviceModel) -> str:
        value = Path(value).absolute()
        return super().__call__(value, device)

    
class MultilineField(HeaderField):
    """Header field for multi-line text values.
    
    Each line begins with the field label. Input can be either a list
    of strings or a single string with newline characters.
    """
    def __call__(self, value: Union[str, list], device: BLDeviceModel) -> str:
        """Format multi-line field.
        
        Value can either be a list of strings (each on its own line)
        or a single string with line breaks. Each line will begin with
        the header label.
        
        :param value: String with newlines or list of strings
        :type value: Union[str, list]
        :param device: BioLogic device model
        :type device: BLDeviceModel
        :return: Multi-line formatted text
        :rtype: Optional[str]
        """
        if not self.check_device(device):
            return None
        
        if isinstance(value, str):
            # If values is a string with line breaks, 
            # split at line breaks
            lines = value.split('\n')
        else:
            # If value is a list, each entry will appear on its own line
            lines = value
        lines = [super().__call__(l, device) for l in lines]
        return '\n'.join(lines)
    
class RangeField(HeaderField):
    """Header field for value ranges (min/max pairs).
    
    Formats two values as a range with customizable separators and labels.
    
    :param label: Main field label
    :type label: str
    :param range_separator: Text between min and max values
    :type range_separator: str
    :param min_label: Optional label before minimum value
    :type min_label: Optional[str]
    :param max_label: Optional label before maximum value
    :type max_label: Optional[str]
    :param separator: Text between label and range (default: ' : ')
    :type separator: str
    :param units: Unit string for both values
    :type units: Optional[str]
    :param precision: Number of decimal places (default: 3)
    :type precision: int
    :param add_linebreak: Add extra newline after field (default: False)
    :type add_linebreak: bool
    :param devices: List of compatible devices, or None for all
    :type devices: Optional[List[BLDeviceModel]]
    """
    def __init__(self, label: str, 
                 range_separator: str,
                 min_label: Optional[str] = None, 
                 max_label: Optional[str] = None,
                 separator: str = ' : ',
                 units: Optional[str] = None, 
                 precision: int = 3,
                 add_linebreak: bool = False,
                 devices: Optional[List[BLDeviceModel]] = None
                 ) -> None:
        super().__init__(label, None, separator, precision, add_linebreak, devices)
        self.range_separator = range_separator
        self.min_label = min_label
        self.max_label = max_label
        self.range_units = units
        
    def __call__(self, min_val, max_val, device: BLDeviceModel) -> str:
        units = '' if self.range_units is None else f' {self.range_units}'
        
        value_text = "{}{}{}{}{}{}{}".format(
            self.min_label or '',
            format_value(min_val, self.precision), units, 
            self.range_separator,
            self.max_label or '',
            format_value(max_val, self.precision), units 
        )
        return super().__call__(value_text, device)
    
class MultivalueField(HeaderField):
    """Header field for multiple labeled values.
    
    Formats multiple values with individual labels, separators, and units
    in a single field.
    
    :param label: Main field label
    :type label: str
    :param value_labels: Label for each value
    :type value_labels: List[str]
    :param value_separators: Separator after each value (length = len(value_labels)-1)
    :type value_separators: List[str]
    :param value_units: Unit for each value (same length as value_labels)
    :type value_units: List[str]
    :param separator: Text between label and values (default: ' : ')
    :type separator: str
    :param precision: Number of decimal places (default: 3)
    :type precision: int
    :param add_linebreak: Add extra newline after field (default: False)
    :type add_linebreak: bool
    :param devices: List of compatible devices, or None for all
    :type devices: Optional[List[BLDeviceModel]]
    :raises ValueError: If value_units/value_separators length mismatch
    """
    def __init__(self, label: str, 
                 value_labels: List[str],
                 value_separators: List[str],
                 value_units: List[str],
                 separator: str = ' : ',
                 precision: int = 3,
                 add_linebreak: bool = False,
                 devices: Optional[List[BLDeviceModel]] = None
                 ) -> None:
        if len(value_units) != len(value_labels):
            raise ValueError("Length of value_units must match length of value_labels")
        if len(value_separators) != len(value_labels) - 1:
            raise ValueError("Length of value_separators must be one less than length of value_labels")
            
        super().__init__(label, None, separator, precision, add_linebreak, devices)
        self.value_separators = value_separators
        self.value_labels = value_labels
        self.value_units = value_units
        
    def __call__(self, values: list, device: BLDeviceModel) -> str:
        if len(values) != len(self.value_labels):
            raise ValueError(f"Length of values must match value_labels ({len(self.value_labels)})")
        
        unit_list = ['' if u is None else f' {u}' for u in self.value_units]
        
        value_texts = [
           f"{l}{format_value(v, self.precision)}{u}" 
           for l, v, u in zip(self.value_labels, values, unit_list)
        ]
        
        seps = self.value_separators + ['']
        value_text = "".join([f"{vt}{s}" for vt, s in zip(value_texts, seps)])
        
        return super().__call__(value_text, device)
    
# -----------------------
# Define header fields
# -----------------------
NumTechniques = HeaderField("Number of linked techniques", add_linebreak=True)

SoftwareVersion = HeaderField("EC-LAB for windows v", units=HeaderFieldUnit("(software)"), separator="")
InternetServerVersion = HeaderField("Internet server v", units=HeaderFieldUnit("(firmware)"), separator="")
CommandInterpreterVersion = HeaderField("Command interpretor v", units=HeaderFieldUnit("(firmware)"), separator="", add_linebreak=True)

SettingsFilename = PathField("Filename", add_linebreak=True)

DeviceField = HeaderField('Device')
ComplianceVoltage = RangeField(
    'CE vs. WE compliance from', 
    range_separator=" to ",
    units="V", 
    separator=" ",
    precision=0,
    devices=[BLDeviceModel.SP150] # TODO: which devices does this apply to?
)
ElectrodeConnectionField = HeaderField("Electrode connection")
PotentialControlField = HeaderField("Potential control")
                    
EweControlRange = RangeField(
    "Ewe ctrl range",
    range_separator=", ",
    min_label="min = ",
    max_label="max = ",
    units="V",
    precision=2
)

# Filtering applies only to 300 series
Filtering = HeaderField(
    "Ewe,I filtering", 
    devices=[
        BLDeviceModel.SP300, 
        BLDeviceModel.VMP300, 
        BLDeviceModel.VSP300
    ]
)

# Safety and advanced settings
# SafetyLimits
SafetyEweMin = CheckboxField("Ewe min", "V", separator=" = ")
SafetyEweMax = CheckboxField("Ewe max", "V", separator=" = ")
SafetyIabs = CheckboxField("|I|", "mA", separator=" = ")
SafetyDQ = CheckboxField("|Q-Qo|", "mA.h", separator=" = ")
SafetyAux1Min = CheckboxField("An In 1 min", separator=" = ")
SafetyAux1Max = CheckboxField("An In 1 max", separator=" = ")
SafetyAux2Min = CheckboxField("An In 2 min", separator=" = ")
SafetyAux2Max = CheckboxField("An In 2 max", separator=" = ")
SafetyDuration = CheckboxField("for t", "ms", separator=" > ")
SafetyNoStartOnOverload = BooleanCheckboxField("Do not start on E overload")

# Record additional variables
RecordEce = BooleanCheckboxField("Record ECE")
RecordAux1 = BooleanCheckboxField("Record Analogic IN 1")
RecordAux2 = BooleanCheckboxField("Record Analogic IN 2")
RecordPower = BooleanCheckboxField("Record Power")
RecordEISQuality = BooleanCheckboxField("Record EIS quality indicators")

# One data file per loop
CreateOneFilePerLoop = BooleanCheckboxField("Create one data file per loop")

# Cycle definition
CycleDefinitionField = HeaderField("Cycle Definition", units=HeaderFieldUnit("alternance"))


TurnToOCV = HeaderField("", separator="")

# Channel grounding applies only to 300 series (?)
ChannelGroundingField = HeaderField(
    "Channel",
    devices=[
        BLDeviceModel.SP300, 
        BLDeviceModel.VMP300, 
        BLDeviceModel.VSP300
    ]
)

# Common metadata
ElectrodeMaterial = HeaderField("Electrode material")
InitialState = HeaderField("Initial state")
Electrolyte = HeaderField("Electrolyte")
Comments = MultilineField("Comments")

# Cable type applies only to 300 series (?)
CableTypeField = HeaderField(
    "Cable",
    devices=[
        BLDeviceModel.SP300, 
        BLDeviceModel.VMP300, 
        BLDeviceModel.VSP300
    ]
)
ReferenceElectrodeField = OptionalField("Reference electrode", 
                                        default_value=ReferenceElectrode.NONE)

# Cell fields
# TODO: handle superscript? chr(178); 178=int("0x00B2", 0)
ElectrodeSurfaceArea = HeaderField("Electrode surface area", units=HeaderFieldUnit("m²", unit_exponent=2, scale_value=True, factor_range=(1e-9, 1), include_centi_deci=True))
CharacteristicMass = HeaderField("Characteristic mass", units=HeaderFieldUnit("g", scale_value=True, factor_range=(1e-6, 1e3)))
# TODO: handle superscript?: chr(179); 179=int("0x00B3", 0)
Volume = HeaderField("Volume (V)", units=HeaderFieldUnit("m³", unit_exponent=3, scale_value=True, factor_range=(1e-2, 1), include_centi_deci=True))

# Battery fields
ActiveMass = MultivalueField(
    "Mass of active material", 
    value_labels=["", "at x = "],
    value_separators=["\n "],
    value_units=[HeaderFieldUnit("mg"), None]
)
MolecularWeight = HeaderField("Molecular weight of active material (at x = 0)", units=HeaderFieldUnit("g/mol"))
AtomicWeight = HeaderField("Atomic weight of intercalated ion", units=HeaderFieldUnit("g/mol"))
AcquisitionStart = HeaderField("Acquisition started at : xo = ", separator="")
NumElectrons = HeaderField("Number of e- transfered per intercalated ion", precision=0)
DxDq = HeaderField("for DX = 1, DQ = ", units="mA.h", separator="")
BatteryCapacity = HeaderField("Battery capacity", units=HeaderFieldUnit("mA.h", scale_value=True, factor_range=(1e-6, 1)))

# Corrosion fields
EquivalentWeight = HeaderField("Equivalent Weight", units=HeaderFieldUnit("g/eq."))
Density = HeaderField("Density", units=HeaderFieldUnit("g/cm3"))


# Materials fields
Thickness = HeaderField("Thickness (t)", units=HeaderFieldUnit("m", scale_value=True, factor_range=(1e-9, 1), include_centi_deci=True))
Diameter = HeaderField("Diameter (d)", units=HeaderFieldUnit("m", scale_value=True, factor_range=(1e-9, 1), include_centi_deci=True))
CellConstant = HeaderField("Cell constant (k=t/A)", units=HeaderFieldUnit("m-1", unit_exponent=-1, scale_value=True, factor_range=(1e-9, 1), include_centi_deci=True))
