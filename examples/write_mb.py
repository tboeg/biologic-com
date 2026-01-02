# This script creates an MPS file containing an OCV step followed by a Modulo Bat (MB) sequence.
from pathlib import Path

from biocom.mps.techniques.ocv import OCVParameters
from biocom.mps.techniques.sequence import TechniqueSequence
from biocom.mps.techniques import mb
from biocom.mps.common import  BLDeviceModel, SampleType, IRange, get_i_range
from biocom.mps.config import set_versions, set_defaults
from biocom.mps.write import write_techniques

# Directory in which to write file
destdir = Path("./")


if __name__ == "__main__":
    
    # Set the software and firmware version to match your instance of EC-Lab
    set_versions("11.61")

    
    # Outside of MB: OCV for 10 s
    ocv_params = OCVParameters(
        10.0, # Duration (s)
        1.0, # Sample period (s)
    )
    
    # Begin making MB sequence
    
    # 1. Constant current step: apply 100 mA for 60 s or until 1 V is reached, 
    # whichever happens first
    # -----------------------
    # Stop after 60 s
    cc_tlim = mb.MBLimit(mb.MBLimitType.TIME, mb.MBLimitComparison.GT, 60.0, mb.MBLimitAction.NEXT)
    # Stop if voltage exceeds 1 V
    cc_vlim = mb.MBLimit(mb.MBLimitType.EWE, mb.MBLimitComparison.GT, 1.0, mb.MBLimitAction.NEXT)
    # Record every 1 s
    cc_record = mb.MBRecordCriterion(mb.MBRecordType.TIME, 1.0)
    
    cc = mb.MBConstantCurrent(
        current=0.1, 
        limits=[cc_tlim, cc_vlim], 
        record_criteria=[cc_record]
    )
    
    # 2. Constant voltage step: hold at 1 V for 30 s or until current 
    # drops to 10 mA, whichever happens first
    # -----------------------
    cv_tlim = mb.MBLimit(mb.MBLimitType.TIME, mb.MBLimitComparison.GT, 30.0, mb.MBLimitAction.NEXT)
    cv_ilim = mb.MBLimit(mb.MBLimitType.IABS, mb.MBLimitComparison.LT, 0.01, mb.MBLimitAction.NEXT)
    # Record every 0.1 s
    cv_record = mb.MBRecordCriterion(mb.MBRecordType.TIME, 0.1)
    cv = mb.MBConstantVoltage(
        voltage=1.0, 
        limits=[cv_tlim, cv_ilim],
        record_criteria=[cv_record]
    )
    
    # 3. PEIS measurement at last measured potential
    # -----------------------
    # No limits are required - PEIS will run through all frequencies and
    # move to next step
    peis = mb.MBPEIS(
        1e6, # max frequency (Hz)
        1e-1, # min frequency (Hz)
        0.01, # AC amplitude (V)
        10, # points per decade
        limits=[]
    )
    
    # Set current ranges for MB steps
    i_ranges = [
        get_i_range(0.1), # For CC step of 100 mA
        IRange.AUTO, # For CV step
        IRange.AUTO # For PEIS step
    ]
    
    # Combine steps into MB sequence
    mbseq = mb.MBSequence([cc, cv, peis], i_range=i_ranges)
    
    # Make TechniqueSequence including OCV and MB sequence
    sequence = TechniqueSequence([ocv_params, mbseq])
    
    # Create a configuration for running the measurement
    # This contains the details that you see in the Safety/Adv. Settings 
    # tab of EC-Lab, as well as Cell Characteristics
    config = set_defaults(BLDeviceModel.SP150, sequence, SampleType.CORROSION)
    
    # Filename in which to write mps file
    mps_file = destdir.joinpath("OCV-MB.mps")
    
    # Write the settings to an mps file 
    write_techniques(sequence, config, mps_file)
    
    
    