"""Loop technique parameters for technique sequences.

This module provides the LoopParameters class for creating loops within
technique sequences, allowing techniques to be repeated a specified
number of times.
"""
from dataclasses import dataclass

from .technique import TechniqueParameters


@dataclass
class LoopParameters(TechniqueParameters):
    """Loop technique for repeating technique sequences.
    
    Creates a loop that repeats from a specified technique number
    back to a previous technique a given number of times.
    
    :param goto_Ne: Target technique number to loop to (1-indexed)
    :type goto_Ne: int
    :param nt: Number of times to repeat the loop
    :type nt: int
    
    Example::
    
        # Loop techniques 2-4 three times
        loop = LoopParameters(
            goto_Ne=2,  # Go back to technique 2
            nt=3        # Repeat 3 times
        )
    
    Note:
        The loop is typically added after the techniques to be repeated.
        Technique numbering is 1-indexed as displayed in EC-Lab.
    """
    goto_Ne: int
    nt: int
    
    technique_name = "Loop"
    abbreviation = "Loop"
    
    _param_map = {
        "goto Ne": "goto_Ne",
        "nt times": "nt"
    }
    