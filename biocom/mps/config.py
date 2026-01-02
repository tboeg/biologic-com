"""Configuration management for BioLogic MPS files.

This module provides dataclasses and functions for managing experiment
configuration including basic settings, hardware parameters, safety limits,
and sample-specific characteristics.

The configuration system uses dataclasses to organize settings into logical
groups that can be independently created and updated.
"""
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Union, Optional


from .common import (
    BLDeviceModel, CableType, ChannelGrounding, ElectrodeConnection, 
    Filter, PotentialControl, ReferenceElectrode, TurnToOCV,
    SampleType, CycleDefinition
)


global SOFTWARE_VERSION
global SERVER_VERSION
global INTERPRETER_VERSION

SOFTWARE_VERSION = '11.50'
SERVER_VERSION = '11.50'
INTERPRETER_VERSION = '11.50'



def set_versions(
        software: str = '11.50',
        server: Optional[str] = None,
        interpreter: Optional[str] = None
    ):
    """Configure EC-Lab software version strings.
    
    Sets the version numbers for EC-Lab software, server, and command
    interpreter. This information is written to the MPS file header.
    Does NOT affect EC-Lab itself - only informs biocom of the versions
    you are using.
    
    :param software: EC-Lab software version (default: '11.50')
    :type software: str
    :param server: Internet server/firmware version (defaults to software version)
    :type server: Optional[str]
    :param interpreter: Command interpreter/firmware version (defaults to software version)
    :type interpreter: Optional[str]
    
    Example::
    
        set_versions(software='11.50', server='11.40')
    """
    global SOFTWARE_VERSION
    global SERVER_VERSION
    global INTERPRETER_VERSION 
    
    SOFTWARE_VERSION = software
    SERVER_VERSION = server or software
    INTERPRETER_VERSION = interpreter or software


@dataclass
class BasicConfig(object):
    """Basic MPS file configuration.
    
    :param num_techniques: Number of techniques in sequence
    :type num_techniques: int
    :param software_version: EC-Lab software version
    :type software_version: str
    :param server_version: EC-Lab server/firmware version
    :type server_version: str
    :param interpreter_version: Command interpreter/firmware version
    :type interpreter_version: str
    :param settings_filename: Path to MPS settings file
    :type settings_filename: Union[str, Path]
    :param device: BioLogic device model
    :type device: BLDeviceModel
    """
    num_techniques: int
    software_version: str
    server_version: str
    interpreter_version: str
    settings_filename: Union[str, Path]
    device: BLDeviceModel
    
    
@dataclass
class SafetySettings(object):
    """Safety limit configuration.
    
    Defines safety limits to automatically stop experiments when exceeded.
    All limits are optional (None means no limit).
    
    :param duration_ms: Duration threshold in milliseconds (default: 10.0)
    :type duration_ms: Optional[float]
    :param ewe_min: Minimum working electrode potential (V)
    :type ewe_min: Optional[float]
    :param ewe_max: Maximum working electrode potential (V)
    :type ewe_max: Optional[float]
    :param iabs_mA: Absolute current limit (mA)
    :type iabs_mA: Optional[float]
    :param dq_mAh: Charge difference limit (mAh)
    :type dq_mAh: Optional[float]
    :param aux1_min: Minimum auxiliary input 1 (V)
    :type aux1_min: Optional[float]
    :param aux1_max: Maximum auxiliary input 1 (V)
    :type aux1_max: Optional[float]
    :param aux2_min: Minimum auxiliary input 2 (V)
    :type aux2_min: Optional[float]
    :param aux2_max: Maximum auxiliary input 2 (V)
    :type aux2_max: Optional[float]
    :param no_start_on_overload: Prevent start if overload detected
    :type no_start_on_overload: bool
    """
    duration_ms: Optional[float] = 10.0 # ms
    ewe_min: Optional[float] = None # V
    ewe_max: Optional[float] = None # V
    iabs_mA: Optional[float] = None # mA
    dq_mAh: Optional[float] = None  # mAh
    aux1_min: Optional[float] = None # V
    aux1_max: Optional[float] = None # V
    aux2_min: Optional[float] = None # V
    aux2_max: Optional[float] = None # V
    no_start_on_overload: bool = True


@dataclass
class HardwareSettings(object):
    """Hardware and measurement configuration.
    
    :param v_range_min: Minimum voltage control range (V)
    :type v_range_min: float
    :param v_range_max: Maximum voltage control range (V)
    :type v_range_max: float
    :param filtering: Signal filter setting
    :type filtering: Filter
    :param v_comp_min: Minimum compliance voltage (V, default: -10)
    :type v_comp_min: int
    :param v_comp_max: Maximum compliance voltage (V, default: 10)
    :type v_comp_max: int
    :param potential_control: Potential control mode
    :type potential_control: PotentialControl
    :param electrode_connection: Electrode connection configuration
    :type electrode_connection: ElectrodeConnection
    :param grounding: Channel grounding setting
    :type grounding: ChannelGrounding
    """
    v_range_min: float
    v_range_max: float
    filtering: Filter
    v_comp_min: int = -10
    v_comp_max: int = 10
    potential_control: PotentialControl = PotentialControl.EWE
    electrode_connection: ElectrodeConnection = ElectrodeConnection.STANDARD
    grounding: ChannelGrounding = ChannelGrounding.FLOATING
    

@dataclass
class CellCharacteristics(object):
    """General cell and electrode characteristics.
    
    :param electrode_material: Electrode material description
    :type electrode_material: str
    :param initial_state: Initial state description
    :type initial_state: str
    :param electrolyte: Electrolyte description
    :type electrolyte: str
    :param comments: Additional comments
    :type comments: str
    :param cable: Cable type
    :type cable: CableType
    :param ref_electrode: Reference electrode type
    :type ref_electrode: ReferenceElectrode
    :param surface_area: Electrode surface area (cm²)
    :type surface_area: float
    :param char_mass: Characteristic mass (g)
    :type char_mass: float
    :param volume: Cell volume (cm³)
    :type volume: float
    """
    electrode_material: str
    initial_state: str
    electrolyte: str
    comments: str
    cable: CableType = CableType.STANDARD
    ref_electrode: ReferenceElectrode = ReferenceElectrode.NONE
    surface_area: float = 0.001
    char_mass: float = 0.001
    volume: float = 0.001
    

@dataclass
class BatteryCharacteristics(object):
    """Battery-specific sample characteristics.
    
    :param active_mass_mg: Active material mass (mg, default: 0.001)
    :type active_mass_mg: float
    :param active_x: Stoichiometric coefficient x (default: 0.0)
    :type active_x: float
    :param active_mol_wt_g: Molecular weight of active material (g/mol, default: 0.001)
    :type active_mol_wt_g: float
    :param ion_at_wt_g: Atomic weight of intercalated ion (g/mol, default: 0.001)
    :type ion_at_wt_g: float
    :param x0: Initial stoichiometric coefficient (default: 0.0)
    :type x0: float
    :param num_electrons: Number of electrons transferred per ion (default: 1)
    :type num_electrons: int
    :param capacity_mAh: Battery capacity (mAh, default: 0.0)
    :type capacity_mAh: float
    """
    active_mass_mg: float = 0.001
    active_x: float = 0.0
    active_mol_wt_g: float = 0.001
    ion_at_wt_g: float = 0.001
    x0: float = 0.0
    num_electrons: int = 1
    capacity_mAh: float = 0.0
    

@dataclass
class CorrosionCharacteristics(object):
    """Corrosion-specific sample characteristics.
    
    :param equiv_wt: Equivalent weight (g/eq, default: 0.0)
    :type equiv_wt: float
    :param density: Material density (g/cm³, default: 0.0)
    :type density: float
    """
    equiv_wt: float = 0.0
    density: float = 0.0
    

@dataclass
class MaterialsCharacteristics(object):
    """Materials characterization sample properties.
    
    :param thickness: Sample thickness (cm, default: 0.0)
    :type thickness: float
    :param diameter: Sample diameter (cm, default: 0.0)
    :type diameter: float
    :param cell_constant: Cell constant k=t/A (cm⁻¹, default: 0.0)
    :type cell_constant: float
    """
    thickness: float = 0.0
    diameter: float = 0.0
    cell_constant: float = 0.0
    

@dataclass
class RecordingOptions(object):
    """Data recording options.
    
    :param ece: Record counter electrode potential
    :type ece: bool
    :param power: Record power data
    :type power: bool
    :param aux1: Record auxiliary input 1
    :type aux1: bool
    :param aux2: Record auxiliary input 2
    :type aux2: bool
    :param eis_quality: Record EIS quality indicators
    :type eis_quality: bool
    """
    ece: bool = False
    power: bool = False
    aux1: bool = False
    aux2: bool = False
    eis_quality: bool = False
    
@dataclass
class MiscOptions(object):
    """Miscellaneous experiment options.
    
    :param turn_to_ocv: Return to OCV between techniques
    :type turn_to_ocv: TurnToOCV
    :param cycle_definition: Battery cycle definition
    :type cycle_definition: CycleDefinition
    :param one_file_per_loop: Create separate file for each loop iteration
    :type one_file_per_loop: bool
    """
    turn_to_ocv: TurnToOCV = TurnToOCV.FALSE
    cycle_definition: CycleDefinition = CycleDefinition.CHARGE_DISCHARGE
    one_file_per_loop: bool = False
    
    
@dataclass
class FullConfiguration(object):
    """Complete experiment configuration.
    
    Aggregates all configuration settings for writing MPS files.
    
    :param basic: Basic configuration (versions, device, etc.)
    :type basic: BasicConfig
    :param hardware: Hardware settings (voltage range, filtering, etc.)
    :type hardware: HardwareSettings
    :param sample: Sample-specific characteristics
    :type sample: Union[CorrosionCharacteristics, BatteryCharacteristics, MaterialsCharacteristics]
    :param cell: Cell and electrode characteristics
    :type cell: CellCharacteristics
    :param safety: Safety limit settings
    :type safety: SafetySettings
    :param recording: Data recording options
    :type recording: RecordingOptions
    :param misc: Miscellaneous options
    :type misc: MiscOptions
    """
    basic: BasicConfig
    hardware: HardwareSettings
    sample: Union[CorrosionCharacteristics, BatteryCharacteristics, MaterialsCharacteristics]
    cell: CellCharacteristics
    safety: SafetySettings
    recording: RecordingOptions
    misc: MiscOptions
    
    # def __init__(self, 
    #              basic: BasicConfig,
    #              hardware: HardwareSettings,
    #              sample: Union[CorrosionCharacteristics, BatteryCharacteristics, MaterialsCharacteristics],
    #              cell: CellCharacteristics,
    #              safety: SafetySettings,
    #              recording: RecordingOptions,
    #              misc: MiscOptions
    #              ):
    #     self.basic = basic
    #     self.hardware = hardware
    #     self.sample = sample
    #     self.cell = cell
    #     self.safety = safety
    #     self.recording = recording
    #     self.misc = misc
        
    
_settings_classes = {
    'basic': BasicConfig,
    'hardware': HardwareSettings,
    'safety': SafetySettings,
    'recording': RecordingOptions,
    'cell': CellCharacteristics,
    'misc': MiscOptions
}




def make_or_update_config(
    current_settings: Union[FullConfiguration, None], 
    name: str, 
    kwargs: dict,
    sample_type: Optional[SampleType] = None
    ):  
    
    if current_settings is None:
        # Make a new settings instance
        if name == 'sample':
            if sample_type is None:
                raise ValueError("To create a new sample settings instance, "
                                 "sample_type must be provided")
            if sample_type == SampleType.CORROSION:
                cls = CorrosionCharacteristics
            elif sample_type == SampleType.BATTERY:
                cls = BatteryCharacteristics
            elif sample_type == SampleType.MATERIALS:
                cls = MaterialsCharacteristics
        else:
            cls = _settings_classes[name]
        return cls(**kwargs)
    else:
        # If a configuration object already exist, update the 
        # corresponding dataclass with the new kwargs.
        # Update the FullConfiguration instance in place
        new = replace(getattr(current_settings, name), **kwargs)
        setattr(current_settings, name, new)
    

def set_recording_options(
        ece: bool = False,
        power: bool = False,
        aux1: bool = False,
        aux2: bool = False,
        eis_quality: bool = False,
        current_settings: Optional[FullConfiguration] = None
    ):
    """Set data recording options.
    
    :param ece: Record counter electrode potential (default: False)
    :type ece: bool
    :param power: Record power (default: False)
    :type power: bool
    :param aux1: Record auxiliary input 1 (default: False)
    :type aux1: bool
    :param aux2: Record auxiliary input 2 (default: False)
    :type aux2: bool
    :param eis_quality: Record EIS quality indicators (default: False)
    :type eis_quality: bool
    :param current_settings: Existing configuration to update (optional)
    :type current_settings: Optional[FullConfiguration]
    :return: Recording options instance
    :rtype: RecordingOptions
    """
    kwargs = {k:v for k,v in locals().items() if k != 'current_settings'}
    
    return make_or_update_config(current_settings, 'recording', kwargs)
    # if current_settings is None:
    #     return RecordingOptions(**kwargs)
    # else:
    #     return replace(current_settings.recording, **kwargs)



def set_safety_limits(
        duration_ms: Optional[float] = 10.0,
        ewe_min: Optional[float] = None, # V
        ewe_max: Optional[float] = None, # V
        iabs_mA: Optional[float] = None, # mA
        dq_mAh: Optional[float] = None,  # mAh
        aux1_min: Optional[float] = None, # V
        aux1_max: Optional[float] = None, # V
        aux2_min: Optional[float] = None, # V
        aux2_max: Optional[float] = None, # V
        no_start_on_overload: bool = True,
        current_settings: Optional[FullConfiguration] = None
    ):
    """Set safety limits for experiment protection.
    
    :param duration_ms: Duration threshold in milliseconds (default: 10.0)
    :type duration_ms: Optional[float]
    :param ewe_min: Minimum working electrode potential (V)
    :type ewe_min: Optional[float]
    :param ewe_max: Maximum working electrode potential (V)
    :type ewe_max: Optional[float]
    :param iabs_mA: Absolute current limit (mA)
    :type iabs_mA: Optional[float]
    :param dq_mAh: Charge difference limit (mAh)
    :type dq_mAh: Optional[float]
    :param aux1_min: Minimum auxiliary input 1 (V)
    :type aux1_min: Optional[float]
    :param aux1_max: Maximum auxiliary input 1 (V)
    :type aux1_max: Optional[float]
    :param aux2_min: Minimum auxiliary input 2 (V)
    :type aux2_min: Optional[float]
    :param aux2_max: Maximum auxiliary input 2 (V)
    :type aux2_max: Optional[float]
    :param no_start_on_overload: Prevent start if overload detected
    :type no_start_on_overload: bool
    :param current_settings: Existing configuration to update (optional)
    :type current_settings: Optional[FullConfiguration]
    :return: Safety settings instance
    :rtype: SafetySettings
    """
    kwargs = {k:v for k,v in locals().items() if k != 'current_settings'}
    # If there are no limits requiring a duration, 
    # remove the duration setting
    if not any([ewe_min, ewe_max, iabs_mA, dq_mAh, 
                aux1_min, aux1_max,
                aux2_min, aux2_max,
        ]):
        kwargs['duration_ms'] = None
        
        
    return make_or_update_config(current_settings, 'safety', kwargs)
    
    # if current_settings is None:
    #     return SafetySettings(**kwargs)
    # else:
    #     return replace(current_settings.safety, **kwargs)
 
    
    

def set_basic_config(
        num_techniques: int,
        software_version: str,
        server_version: str,
        interpreter_version: str,
        settings_filename: Union[str, Path],
        device: BLDeviceModel,
        current_settings: Optional[FullConfiguration] = None
    ):
    """Set basic MPS file configuration.
    
    :param num_techniques: Number of techniques in sequence
    :type num_techniques: int
    :param software_version: EC-Lab software version
    :type software_version: str
    :param server_version: Server/firmware version
    :type server_version: str
    :param interpreter_version: Command interpreter version
    :type interpreter_version: str
    :param settings_filename: Path to settings file
    :type settings_filename: Union[str, Path]
    :param device: BioLogic device model
    :type device: BLDeviceModel
    :param current_settings: Existing configuration to update (optional)
    :type current_settings: Optional[FullConfiguration]
    :return: Basic configuration instance
    :rtype: BasicConfig
    """
    kwargs = {k:v for k,v in locals().items() if k != 'current_settings'}
    return make_or_update_config(current_settings, 'basic', kwargs)
    
    # return BasicConfig(**locals())

def set_hardware(
        device: BLDeviceModel,
        v_range_min: float,
        v_range_max: float,
        filtering: Filter = Filter.NONE,
        v_comp_min: int = -10,
        v_comp_max: int = 10,
        potential_control: PotentialControl = PotentialControl.EWE,
        electrode_connection: ElectrodeConnection = ElectrodeConnection.STANDARD,
        grounding: ChannelGrounding = ChannelGrounding.FLOATING,
        current_settings: Optional[FullConfiguration] = None
    ):
    """Set hardware configuration.
    
    :param device: BioLogic device model
    :type device: BLDeviceModel
    :param v_range_min: Minimum voltage range (V)
    :type v_range_min: float
    :param v_range_max: Maximum voltage range (V)
    :type v_range_max: float
    :param filtering: Signal filter setting (default: NONE)
    :type filtering: Filter
    :param v_comp_min: Minimum compliance voltage (V, default: -10)
    :type v_comp_min: int
    :param v_comp_max: Maximum compliance voltage (V, default: 10)
    :type v_comp_max: int
    :param potential_control: Potential control mode
    :type potential_control: PotentialControl
    :param electrode_connection: Electrode connection type
    :type electrode_connection: ElectrodeConnection
    :param grounding: Channel grounding setting
    :type grounding: ChannelGrounding
    :param current_settings: Existing configuration to update (optional)
    :type current_settings: Optional[FullConfiguration]
    :return: Hardware settings instance
    :rtype: HardwareSettings
    :raises ValueError: If filter not supported by device
    """
    kwargs = {k:v for k, v in locals().items() if k not in ['device', 'current_settings']}
    # print(kwargs)
    device.validate_filter(filtering)
    
    return make_or_update_config(current_settings, 'hardware', kwargs)
    
    
    # return HardwareSettings(
    #     v_range_min,
    #     v_range_max,
    #     filtering,
    #     v_comp_min,
    #     v_comp_max,
    #     potential_control,
    #     electrode_connection,
    #     grounding
    # )
    
def set_cell_characteristics(
        electrode_material: str = '',
        initial_state: str = '',
        electrolyte: str = '',
        comments: str = '',
        cable: CableType = CableType.STANDARD,
        ref_electrode: ReferenceElectrode = ReferenceElectrode.NONE,
        surface_area: float = 0.001,
        char_mass: float = 0.001,
        volume: float = 0.001,
        current_settings: Optional[FullConfiguration] = None
    ):
    """Set cell and electrode characteristics.
    
    :param electrode_material: Electrode material description
    :type electrode_material: str
    :param initial_state: Initial state description
    :type initial_state: str
    :param electrolyte: Electrolyte description
    :type electrolyte: str
    :param comments: Additional comments
    :type comments: str
    :param cable: Cable type
    :type cable: CableType
    :param ref_electrode: Reference electrode type
    :type ref_electrode: ReferenceElectrode
    :param surface_area: Electrode surface area (cm², default: 0.001)
    :type surface_area: float
    :param char_mass: Characteristic mass (g, default: 0.001)
    :type char_mass: float
    :param volume: Cell volume (cm³, default: 0.001)
    :type volume: float
    :param current_settings: Existing configuration to update (optional)
    :type current_settings: Optional[FullConfiguration]
    :return: Cell characteristics instance
    :rtype: CellCharacteristics
    """
    kwargs = {k:v for k,v in locals().items() if k != 'current_settings'}
    # return CellCharacteristics(**locals())
    return make_or_update_config(current_settings, 'cell', kwargs)
    

    
def set_battery_characteristics(
        active_mass_mg: float = 0.001,
        active_x: float = 0.0,
        active_mol_wt_g: float = 0.001,
        ion_at_wt_g: float = 0.001,
        x0: float = 0.0,
        num_electrons: int = 1,
        capacity_mAh: float = 0.0,
        current_settings: Optional[FullConfiguration] = None
    ):
    """Set battery-specific sample characteristics.
    
    :param active_mass_mg: Active material mass (mg, default: 0.001)
    :type active_mass_mg: float
    :param active_x: Stoichiometric coefficient x (default: 0.0)
    :type active_x: float
    :param active_mol_wt_g: Molecular weight of active material (g/mol, default: 0.001)
    :type active_mol_wt_g: float
    :param ion_at_wt_g: Atomic weight of intercalated ion (g/mol, default: 0.001)
    :type ion_at_wt_g: float
    :param x0: Initial stoichiometric coefficient (default: 0.0)
    :type x0: float
    :param num_electrons: Electrons transferred per ion (default: 1)
    :type num_electrons: int
    :param capacity_mAh: Battery capacity (mAh, default: 0.0)
    :type capacity_mAh: float
    :param current_settings: Existing configuration to update (optional)
    :type current_settings: Optional[FullConfiguration]
    :return: Battery characteristics instance
    :rtype: BatteryCharacteristics
    """
    kwargs = {k:v for k,v in locals().items() if k != 'current_settings'}
    # return BatteryCharacteristics(**locals())
    return make_or_update_config(current_settings, 'sample', kwargs, SampleType.BATTERY)
    


def set_materials_characteristics(
        thickness: float = 0.0,
        diameter: float = 0.0,
        cell_constant: float = 0.0,
        current_settings: Optional[FullConfiguration] = None
    ):
    """Set materials characterization sample properties.
    
    :param thickness: Sample thickness (cm, default: 0.0)
    :type thickness: float
    :param diameter: Sample diameter (cm, default: 0.0)
    :type diameter: float
    :param cell_constant: Cell constant k=t/A (cm⁻¹, default: 0.0)
    :type cell_constant: float
    :param current_settings: Existing configuration to update (optional)
    :type current_settings: Optional[FullConfiguration]
    :return: Materials characteristics instance
    :rtype: MaterialsCharacteristics
    """
    kwargs = {k:v for k,v in locals().items() if k != 'current_settings'}
    # return MaterialsCharacteristics(**locals())
    return make_or_update_config(current_settings, 'sample', kwargs, SampleType.MATERIALS)


def set_corrosion_characteristics(
        equiv_wt: float = 0.0,
        density: float = 0.0,
        current_settings: Optional[FullConfiguration] = None
    ):
    """Set corrosion-specific sample characteristics.
    
    :param equiv_wt: Equivalent weight (g/eq, default: 0.0)
    :type equiv_wt: float
    :param density: Material density (g/cm³, default: 0.0)
    :type density: float
    :param current_settings: Existing configuration to update (optional)
    :type current_settings: Optional[FullConfiguration]
    :return: Corrosion characteristics instance
    :rtype: CorrosionCharacteristics
    """
    kwargs = {k:v for k,v in locals().items() if k != 'current_settings'}
    return make_or_update_config(current_settings, 'sample', kwargs, SampleType.CORROSION)
    # return CorrosionCharacteristics(**locals())

def set_misc_options(
        turn_to_ocv: bool = True,
        cycle_definition: CycleDefinition = CycleDefinition.CHARGE_DISCHARGE,
        one_file_per_loop: bool = False,
        current_settings: Optional[FullConfiguration] = None
    ):
    """Set miscellaneous experiment options.
    
    :param turn_to_ocv: Return to OCV between techniques (default: True)
    :type turn_to_ocv: bool
    :param cycle_definition: Battery cycle definition
    :type cycle_definition: CycleDefinition
    :param one_file_per_loop: Create separate file per loop (default: False)
    :type one_file_per_loop: bool
    :param current_settings: Existing configuration to update (optional)
    :type current_settings: Optional[FullConfiguration]
    :return: Miscellaneous options instance
    :rtype: MiscOptions
    """
    kwargs = {k:v for k,v in locals().items() if k != 'current_settings'}
    kwargs['turn_to_ocv'] = TurnToOCV.from_bool(turn_to_ocv)
    return make_or_update_config(current_settings, 'misc', kwargs)
    # return MiscOptions(
    #     TurnToOCV.from_bool(turn_to_ocv),
    #     cycle_definition,
    #     one_file_per_loop
    # )
    

def set_defaults(
        device: BLDeviceModel,
        technique_sequence,
        sample_type: SampleType
    ):
    """Create default configuration for experiment.
    
    Generates a complete FullConfiguration with sensible defaults based on
    device model, technique sequence, and sample type.
    
    :param device: BioLogic device model
    :type device: BLDeviceModel
    :param technique_sequence: Sequence of techniques
    :type technique_sequence: TechniqueSequence
    :param sample_type: Type of sample (battery, corrosion, or materials)
    :type sample_type: SampleType
    :return: Complete configuration with defaults
    :rtype: FullConfiguration
    
    Example::
    
        config = set_defaults(
            BLDeviceModel.SP150,
            technique_sequence,
            SampleType.BATTERY
        )
    """
    
    global SOFTWARE_VERSION
    global SERVER_VERSION
    global INTERPRETER_VERSION

    basic = set_basic_config(
        technique_sequence.num_techniques,
        SOFTWARE_VERSION,
        SERVER_VERSION,
        INTERPRETER_VERSION,
        settings_filename=None,  # Placeholder
        device=device
    )
    
    recording = set_recording_options()
    safety = set_safety_limits()
    
    hardware = set_hardware(
        device,
        # Take v range from first technique
        technique_sequence[0].v_range_min,
        technique_sequence[0].v_range_max,
    )
    
    cell = set_cell_characteristics()
    
    misc = set_misc_options()
    
    if sample_type == SampleType.CORROSION:
        sample = set_corrosion_characteristics()
    elif sample_type == SampleType.BATTERY:
        sample = set_battery_characteristics()
    elif sample_type == SampleType.MATERIALS:
        sample = set_materials_characteristics()
        
    return FullConfiguration(
        basic,
        hardware,
        sample,
        cell,
        safety,
        recording,
        misc
    )
    
    
def validate_configuration(config: FullConfiguration):
    device: BLDeviceModel = config.basic.device
    
    device.validate_bandwidth(config.hardware.bandwidth)
    device.validate_filter(config.hardware.filtering)
    
    