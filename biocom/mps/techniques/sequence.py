"""Technique sequence management for MPS files.

This module provides the TechniqueSequence class for managing ordered
collections of electrochemical techniques and generating the technique
parameter sections of MPS files.
"""
import numpy as np
import warnings
from typing import List

from .technique import HardwareParameters, TechniqueParameters
from ..write_utils import FilePath
from .mb import MBSequence
from ..config import FullConfiguration



class TechniqueSequence(list):
    """Ordered sequence of electrochemical techniques.
    
    Manages a list of TechniqueParameters objects and handles voltage
    range validation, configuration application, and MPS file formatting.
    Inherits from list to provide familiar sequence operations.
    
    :param techniques: List of technique parameter objects
    :type techniques: List[TechniqueParameters]
    
    Example::
    
        from biocom.mps.techniques.ocv import OCVParameters
        from biocom.mps.techniques.sequence import TechniqueSequence
        
        ocv1 = OCVParameters(duration=10.0)
        ocv2 = OCVParameters(duration=20.0)
        sequence = TechniqueSequence([ocv1, ocv2])
    
    Note:
        EC-Lab requires all techniques in a sequence to use the same
        voltage range. This class automatically enforces consistent
        voltage limits across techniques.
    """
    # def __init__(self, techniques: List[TechniqueParameters]) -> None:
    #     self.technique_list = techniques

    def __init__(self, techniques: List[TechniqueParameters]) -> None:
        super().__init__(techniques)

        self.set_v_limits()
        
        
    def apply_configuration(self, configuration: FullConfiguration):
        """Apply configuration to all techniques in sequence.
        
        :param configuration: Full experiment configuration
        :type configuration: FullConfiguration
        """
        for t in self:
            t.apply_configuration(configuration)


    def set_v_limits(self):
        """Validate and harmonize voltage limits across techniques.
        
        EC-Lab requires a single voltage range for all techniques.
        If multiple ranges are provided, uses the min/max across all
        techniques and issues a warning.
        
        :raises Warning: If multiple voltage limits detected
        """
        # Check v ranges: EC-Lab uses the same voltage range for all techniques
        for agg in ["min", "max"]:
            long_agg = "minimum" if agg == "min" else "maximum"
            v_lim = [getattr(t, f"v_range_{agg}") for t in self if hasattr(t, f"v_range_{agg}")]
            if len(np.unique(v_lim)) > 1:
                # Multiple voltage ranges provided. Set a single voltage range
                v_lim = getattr(np, agg)(v_lim)
                warnings.warn(f"Multiple {long_agg} voltage limits were provided in the technique "
                            "sequence, but EC-Lab requires a single voltage limit."
                            f"The {long_agg} voltage will be set to the {long_agg} provided value "
                            "across all techniques: {:.1f} V.".format(v_lim)
                            )
                for t in self:
                    setattr(t, f"v_range_{agg}", v_lim)

    def append(self, technique):
        """Add technique to sequence and update voltage limits.
        
        :param technique: Technique parameters to add
        :type technique: TechniqueParameters
        """
        super().append(technique)
        self.set_v_limits()

    @property
    def num_techniques(self) -> int:
        """Get number of techniques in sequence.
        
        :return: Number of techniques
        :rtype: int
        """
        return len(self)

    @property
    def abbreviations(self):
        """Get list of technique abbreviations.
        
        :return: List of abbreviations
        :rtype: list
        """
        return [t.abbreviation for t in self]

    def technique_text(self, index):
        """Generate formatted text for single technique.
        
        :param index: Zero-based technique index
        :type index: int
        :return: Formatted technique block
        :rtype: str
        """
        technique = self[index]

        # Header
        header = [
            f'Technique : {index + 1}',
            technique.technique_name
        ]

        # Parameter block
        param_text = technique.param_text(index + 1)

        return '\n'.join(header + [param_text])

    def sequence_text(self):
        """Generate complete formatted text for all techniques.
        
        :return: Formatted technique sequence for MPS file
        :rtype: str
        """
        # Get block for each technique
        text = [
            self.technique_text(i)
            for i in range(len(self))
        ]

        tables = []
        for i, technique in enumerate(self):
            if isinstance(technique, MBSequence):
                tables += technique.get_urban_tables(i + 1)

        # Separate techniques with double line breaks
        return '\n\n'.join(text + tables)

    def write_params(self, file: FilePath, append: bool = False):
        """Write technique parameters to file.
        
        :param file: Output file path
        :type file: Union[str, Path]
        :param append: Append to file if True, overwrite if False
        :type append: bool
        """
        if append:
            mode = "a"
        else:
            mode = "w"

        with open(file, mode) as f:
            f.write(self.sequence_text())