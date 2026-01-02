# This script creates an MPS file containing an OCV step, a PEIS step, another OCV step, and a ChronoPotentiometry (CP) step.
from pathlib import Path

from biocom.mps.techniques.eis import PEISParameters
from biocom.mps.techniques.ocv import OCVParameters
from biocom.mps.techniques.chrono import CPParameters
from biocom.mps.techniques.sequence import TechniqueSequence
from biocom.mps.common import EweVs, Bandwidth, BLDeviceModel, SampleType
from biocom.mps.config import set_versions, set_defaults
from biocom.mps.write import write_techniques

# Directory in which to write file
destdir = Path("./")


if __name__ == "__main__":
    
    # Set the software and firmware version to match your instance of EC-Lab
    set_versions("11.61")
    
    # Make TechniqueParameters instances to configure the measurement steps
    
    ocv_params = OCVParameters(
        10.0, # Duration (s)
        1.0, # Sample period (s)
    )
    
    peis_params = PEISParameters(
        0.0, # DC voltage (V)
        0.01, # AC amplitude (V),
        dc_vs=EweVs.EOC, # DC voltage relative to EOC (open circuit),
        f_max=1e6, # Maximum frequency (Hz)
        f_min=1, # Minimum frequency (Hz)
        points=10, # points per decade,
        average=2, # Number of cycles per frequency to average,
        v_range_max=10,
        v_range_min=-10,
        bandwidth=Bandwidth.BW7
    )
    
    cp_params = CPParameters(
        [0, 1e-6, -1e-6, 0], # step currents (A)
        [10, 10, 10, 10],  # step durations (s)
        1e-2, # Sample period (s)
    )
    
    # Combine the techniques in an ordered sequence
    sequence = TechniqueSequence([ocv_params, peis_params, ocv_params, cp_params])
    
    # Create a configuration for running the measurement
    # This contains the details that you see in the Safety/Adv. Settings 
    # tab of EC-Lab, as well as Cell Characteristics
    config = set_defaults(BLDeviceModel.SP150, sequence, SampleType.CORROSION)
    
    # Filename in which to write mps file
    mps_file = destdir.joinpath("OCV-PEIS-OCV-CP.mps")
    
    # Write the settings to an mps file 
    write_techniques(sequence, config, mps_file)



