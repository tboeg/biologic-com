# `biologic-com`: a Python package for programmable experiments with BioLogic potentiostats
`biologic-com` is a Python package that enables programmatic creation of `.mps` settings files and real-time control of BioLogic devices via the EC-Lab OLECOM interface. With `biologic-com`, you can:
* Create customized `.mps` settings files for a variety of experiments using Python scripts
* Use EC-Lab as a server to load, execute, and stop experiments via Python
* Asynchronously control/monitor multiple channels or devices

For installation, documentation, and citation see Jake Huang's upstream directory

## Differences to upstream repository
* Support for WAIT and EXTAPP techniques
* Enhanced unit handling (capable of treating units with exponentials different than 1)
* Enhanced support for cell characterics fields