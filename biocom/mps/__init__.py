"""BioLogic MPS File Generation Module.

This module provides functionality for creating and writing BioLogic EC-Lab
settings files (.mps) programmatically. It handles technique sequencing,
configuration management, and file formatting for automated experiment setup.

The module includes:
    - Configuration dataclasses for experiment setup
    - Header field formatters for .mps file structure
    - Technique parameter handling
    - File writing utilities

Example:
    Basic usage for creating an MPS file::

        from biocom.mps import write_techniques, set_defaults
        from biocom.mps.techniques.sequence import TechniqueSequence
        from biocom.mps.common import BLDeviceModel, SampleType
        
        # Create technique sequence and configuration
        sequence = TechniqueSequence([technique1, technique2])
        config = set_defaults(BLDeviceModel.SP150, sequence, SampleType.BATTERY)
        
        # Write to file
        write_techniques(sequence, config, "experiment.mps")
"""
