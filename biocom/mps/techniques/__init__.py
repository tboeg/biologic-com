"""Electrochemical technique parameters for BioLogic devices.

This module provides parameter classes for configuring electrochemical techniques
in EC-Lab settings files (.mps). Each technique has a dedicated parameter class
that handles validation and formatting of technique-specific settings.

Available techniques include:
    - OCV (Open Circuit Voltage)
    - Chronoamperometry/Chronopotentiometry
    - EIS (Electrochemical Impedance Spectroscopy)
    - GCPL (Galvanostatic Cycling with Potential Limitation)
    - Modulo Bat (MB) sequences
    - Loop

The TechniqueSequence class manages ordered collections of techniques
and handles writing them to MPS files.
"""
