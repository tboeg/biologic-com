"""ExtApp technique parameters for technique sequences.

This module provides the ExtAppParameters class for calling external executables within
technique sequences and passing parameters to them.
"""
from dataclasses import dataclass

from .technique import TechniqueParameters, pad_text, value2str


@dataclass
class ExtAppParameters(TechniqueParameters):
    """External application technique parameters.
    
    Allows calling external executables within technique sequences and passing
    parameters to them.
    
    :param file_path: Path to the external executable to be called
    :type file_path: str
    :param parameters: Parameters to be passed to the external executable
    :type parameters: list of str
    :paraM wait_for_completion: Whether to wait for the external executable to close before proceeding
    :type wait_for_completion: bool
    
    Example::
    
        # Loop techniques 2-4 three times
        extapp = ExtAppParameters(
            file_path="C:/Program Files/example.exe", # call the excecutable example.exe
            parameters="--arg1=5", # pass parameter arg1 to the executable
            wait_for_completion=True # wait for the executable to close before proceeding
        )
    
    """
    file_path: str
    parameters: str = ""
    wait_for_completion: bool = True
    
    technique_name = "External Application"
    abbreviation = "EXTAPP"
    
    _param_map = {
        "App Name": "file_path",
        "Parameters": "parameters",
        "Wait": "wait_for_completion"
    }
    
    def key2str(self, key):
        """Convert parameter key-value pair to formatted string.
        
        Handles the special case of wait_for_completion mapping:
        - True → -1 (wait for external application to close)
        - False → 0 (don't wait)
        
        :param key: Parameter key from _param_map
        :type key: str
        :return: Formatted parameter line
        :rtype: str
        """
        if key == "Wait":
            # Special handling for wait_for_completion
            # -1 = wait for completion (True), 0 = don't wait (False)
            value = -1 if self.wait_for_completion else 0
            return f'{pad_text(key)}{value2str(value)}'
        else:
            # Use parent class implementation for other parameters
            return super().key2str(key)