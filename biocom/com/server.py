"""OLE-COM server interface for BioLogic EC-Lab.

This module provides a Python interface to BioLogic electrochemical devices
through the EC-Lab COM server. It enables programmatic control of experiments,
including loading technique sequences, running measurements, and monitoring
channel status.

Key classes:
    - OLECOM: Main interface to the EC-Lab COM server
    - DeviceChannel: Represents a specific device channel
    - ChannelStatus: Enum for channel operational states
    - ChannelResult: Enum for experiment completion results
"""

import comtypes
from comtypes.client import CreateObject
from enum import Enum, auto
import time
import os
import numpy as np
import functools
import asyncio
from pathlib import Path
from typing import Union, Optional, Tuple, List
import warnings

from ..mps.techniques.sequence import TechniqueSequence
from ..mps.config import FullConfiguration
from ..mps.common import BLDeviceModel
from ..mps.write import write_techniques


FilePath = Union[str, Path]



def validate_and_retry(func):
    """Decorator for COM methods to retry on failure and validate return codes.
    
    Automatically retries failed COM operations and validates that they return
    success code (1). Raises RuntimeError if all retries fail.
    
    :param func: COM method to wrap
    :type func: callable
    :return: Wrapped function with retry logic
    :rtype: callable
    """
    @functools.wraps(func)
    def wrapper(obj, *args, **kwargs):
        for i in range(obj.retries + 1):
            out = func(obj, *args, **kwargs)
            if out == 1:
                # Success 
                break
            elif i < obj.retries:
                # Wait before trying again    
                time.sleep(0.5)
                if obj.show_warnings:
                    warnings.warn(f"OLE-COM method {func.__name__} failed on attempt {i + 1}. Retrying...")
            
        if out != 1 and obj._validate_return_codes:
            raise RuntimeError(f"OLE-COM method {func.__name__} failed with code {out}. "
                               f"Args: {args}; kwargs: {kwargs}")
        return out
    return wrapper


class DeviceChannel(object):
    """Represents a specific channel on a BioLogic device.
    
    Encapsulates device and channel identifiers along with metadata like
    device model, channel name, and data path.
    
    :param device_id: Numeric device identifier
    :type device_id: int
    :param channel: Channel number on the device
    :type channel: int
    :param model: BioLogic device model
    :type model: Optional[BLDeviceModel]
    :param name: User-friendly channel name
    :type name: Optional[str]
    :param data_path: Path for storing measurement data
    :type data_path: Optional[Path]
    
    :ivar i_ac: AC current range
    :ivar i_dc: DC current range
    """
    def __init__(self, device_id: int, channel: int, 
                 model: Optional[BLDeviceModel] = None,
                 name: Optional[str] = None,
                 data_path: Optional[Path] = None
                 ):
        self.device_id = device_id
        self.channel = channel
        self.model = model
        self.name = name
        self.data_path = data_path
        
        self.i_ac = None
        self.i_dc = None
        
        
    @property
    def key(self):
        """Unique identifier tuple for this device channel.
        
        :return: Tuple of (device_id, channel)
        :rtype: Tuple[int, int]
        """
        return (self.device_id, self.channel)
    
    def __str__(self) -> str:
        return f"Device {self.device_id} (Model: {self.model}), Channel {self.channel} (Name: {self.name})"
    
    

def devchannel_input(func):
    """Decorator allowing DeviceChannel objects as method arguments.
    
    Converts DeviceChannel instances to (device_id, channel) tuple arguments,
    enabling more intuitive method calls with channel objects.
    
    :param func: Method to wrap
    :type func: callable
    :return: Wrapped function accepting DeviceChannel or tuple arguments
    :rtype: callable
    """
    # Decorator for OLECOM instance methods,
    # allowing a DeviceChannel instance to be provided instead of
    # device_id and channel
    @functools.wraps(func)
    def wrapper(obj, *args, **kwargs):
        # print('args:', args)
        if isinstance(args[0], DeviceChannel):
            # Convert DeviceChannel instance to device_id, channel tuple
            device_id, channel = args[0].key
            out = func(obj, device_id, channel, *args[1:], **kwargs)
        else:
            out = func(obj, *args, **kwargs)
        return out
    return wrapper
    

class OLECOM(object):
    """OLE-COM interface to BioLogic EC-Lab server.
    
    Provides high-level control of BioLogic electrochemical devices through
    the EC-Lab COM server. Manages device connections, channel operations,
    technique loading, and measurement execution.
    
    :param validate_return_codes: Whether to validate COM method return codes
    :type validate_return_codes: bool
    :param retries: Number of retry attempts for failed COM operations
    :type retries: int
    :param show_warnings: Whether to display retry warnings
    :type show_warnings: bool
    :param print_messages: Whether to print status messages
    :type print_messages: bool
    
    :ivar server: The EC-Lab COM server instance
    :ivar channel_sequences: Mapping of channels to loaded technique sequences
    :ivar channel_settings: Mapping of channels to settings file paths
    :ivar channel_results: Mapping of channels to measurement results
    """
    def __init__(self, validate_return_codes: bool = True, retries: int = 1,
                 show_warnings: bool = True, print_messages: bool = True):
        self.server = None
        self._validate_return_codes = validate_return_codes
        self.retries = retries
        self.show_warnings = show_warnings
        self.print_messages = print_messages
        
        # TODO: store configuration somewhere
        self.channel_sequences = {}
        self.channel_settings = {}
        self.channel_results = {}
    
    def launch_server(self):
        """Launch the EC-Lab COM server.
        
        Initializes connection to the EClabCOM.EClabExe server.
        """
        prog_id = "EClabCOM.EClabExe"
        self.server = CreateObject(prog_id)
    
    def get_device_type(self, device_id: int):
        """Get the device model type.
        
        :param device_id: Device identifier
        :type device_id: int
        :return: Device type string
        :rtype: str
        """
        device_type, code = self.server.GetDeviceType(device_id)
        return device_type
    
    @validate_and_retry
    def connect_device(self, device_id: int):
        """Connect to a device.
        
        :param device_id: Device identifier
        :type device_id: int
        :return: Success code (1 = success)
        :rtype: int
        """
        return self.server.ConnectDevice(device_id)
    
    @validate_and_retry
    def disconnect_device(self, device_id: int):
        """Disconnect from a device.
        
        :param device_id: Device identifier
        :type device_id: int
        :return: Success code (1 = success)
        :rtype: int
        """
        return self.server.DisconnectDevice(device_id)
    
    @validate_and_retry
    def connect_device_by_ip(self, ip_address: str):
        """Connect to a device by IP address.
        
        :param ip_address: Device IP address
        :type ip_address: str
        :return: Success code (1 = success)
        :rtype: int
        """
        return self.server.ConnectDeviceByIP(ip_address)
    
    @devchannel_input
    @validate_and_retry
    def select_channel(self, device_id: int, channel: int):
        """Select a specific channel on a device.
        
        :param device_id: Device identifier (or DeviceChannel object)
        :type device_id: int or DeviceChannel
        :param channel: Channel number
        :type channel: int
        :return: Success code (1 = success)
        :rtype: int
        """
        return self.server.SelectChannel(device_id, channel)
    
    @devchannel_input
    @validate_and_retry
    def load_settings(self, device_id: int, channel: int, mps_file: FilePath, safe: bool = True):
        """Load technique settings from an MPS file.
        
        :param device_id: Device identifier (or DeviceChannel object)
        :type device_id: int or DeviceChannel
        :param channel: Channel number
        :type channel: int
        :param mps_file: Path to MPS settings file
        :type mps_file: FilePath
        :param safe: Whether to select channel first to avoid timing issues
        :type safe: bool
        :return: Success code (1 = success)
        :rtype: int
        """
        mps_file = Path(mps_file)
        abspath = mps_file.absolute().__str__()
        
        if safe:
            # Select the channel and wait briefly to avoid timing issues
            # Should solve:
            # 1. Inability to load settings while another channel is running
            self.select_channel(device_id, channel)
            time.sleep(1.0)
            
        out = self.server.LoadSettings(device_id, channel, abspath)
        
        if out == 1:
            # Store the settings only if successful
            self.channel_settings[(device_id, channel)] = mps_file
            
        return out
    
    @devchannel_input
    @validate_and_retry
    def run_channel(self, device_id: int, channel: int, output_file: FilePath):
        """Start measurement on a channel.
        
        :param device_id: Device identifier (or DeviceChannel object)
        :type device_id: int or DeviceChannel
        :param channel: Channel number
        :type channel: int
        :param output_file: Path for output data file
        :type output_file: FilePath
        :return: Success code (1 = success)
        :rtype: int
        """
        abspath = Path(output_file).absolute().__str__()
        code = self.server.RunChannel(device_id, channel, abspath)
        
        if code == 1:
            # If launched successfully, set channel status to running
            self.channel_results[(device_id, channel)] = ChannelResult.RUNNING
            
        return code
    
    @devchannel_input
    @validate_and_retry
    def stop_channel(self, device_id: int, channel: int):
        """Stop measurement on a channel.
        
        :param device_id: Device identifier (or DeviceChannel object)
        :type device_id: int or DeviceChannel
        :param channel: Channel number
        :type channel: int
        :return: Success code (1 = success)
        :rtype: int
        """
        return self.server.StopChannel(device_id, channel)
    
    @devchannel_input
    def get_data_filename(self, device_id: int, channel: int, technique: int):
        """Get the data filename for a specific technique.
        
        :param device_id: Device identifier (or DeviceChannel object)
        :type device_id: int or DeviceChannel
        :param channel: Channel number
        :type channel: int
        :param technique: Technique index (supports negative indexing)
        :type technique: int
        :return: Data filename
        :rtype: str
        """
        if technique < 0:
            # Convert negative index to positive
            technique = len(self.get_sequence(device_id, channel)) + technique
            
        # GetDataFileName returns a tuple of length 1
        name = self.server.GetDataFileName(device_id, channel, technique)[0]
        return name
    
    @validate_and_retry
    def toggle_popups(self, enable: bool):
        """Enable or disable EC-Lab popup message windows.
        
        Note: Not available for EC-Lab v11.50.
        
        :param enable: Whether to enable popup windows
        :type enable: bool
        :return: Success code (1 = success)
        :rtype: int
        """
        # Not availabe for v11.50
        return self.server.EnableMessagesWindows(enable)
    
    @devchannel_input
    def get_channel_info(self, device_id: int, channel: int):
        """Get detailed information about a channel.
        
        Note: Not available for EC-Lab v11.50.
        
        :param device_id: Device identifier (or DeviceChannel object)
        :type device_id: int or DeviceChannel
        :param channel: Channel number
        :type channel: int
        :return: Channel information
        :rtype: tuple
        """
        # Not availabe for v11.50
        return self.server.GetChannelInfos(device_id, channel)
    
    @devchannel_input
    def check_measure_status(self, device_id: int, channel: int):
        """Check current measurement status of a channel.
        
        :param device_id: Device identifier (or DeviceChannel object)
        :type device_id: int or DeviceChannel
        :param channel: Channel number
        :type channel: int
        :return: Dictionary of status parameters
        :rtype: dict
        """
        return dict(zip(_measure_status_keys, self.server.MeasureStatus(device_id, channel)))
    
    @devchannel_input
    def channel_is_running(self, device_id: int, channel: int):
        """Check if a channel is currently running.
        
        :param device_id: Device identifier (or DeviceChannel object)
        :type device_id: int or DeviceChannel
        :param channel: Channel number
        :type channel: int
        :return: True if channel is running
        :rtype: bool
        """
        stat = self.check_measure_status(device_id, channel)
        return all([
            # stat['Result code'] == 1,  # Valid return code
            int(stat['Connection']) == 0,  # Device is connected
            ChannelStatus(int(stat['Status'])) == ChannelStatus.RUN,  # Channel is running
        ])
        
    @devchannel_input
    def channel_is_stopped(self, device_id: int, channel: int):
        """Check if a channel is stopped.
        
        :param device_id: Device identifier (or DeviceChannel object)
        :type device_id: int or DeviceChannel
        :param channel: Channel number
        :type channel: int
        :return: True if channel is stopped
        :rtype: bool
        """
        stat = self.check_measure_status(device_id, channel)
        return all([
            # stat['Result code'] == 1,  # Valid return code
            int(stat['Connection']) == 0,  # Device is connected
            ChannelStatus(int(stat['Status'])) == ChannelStatus.STOP,  # Channel is stopped
        ])
    
    @devchannel_input
    @validate_and_retry
    def load_techniques(
            self, 
            device_id: int,
            channel: int,
            sequence: TechniqueSequence, 
            config: FullConfiguration,
            mps_file: FilePath
        ):
        """Load technique sequence directly from a TechniqueSequence object.
        
        Given a TechniqueSequence object and configuration, writes an MPS file, 
        then loads it to the specified channel. Validates device model compatibility.
        
        :param device_id: Device identifier (or DeviceChannel object)
        :type device_id: int or DeviceChannel
        :param channel: Channel number
        :type channel: int
        :param sequence: Technique sequence to load
        :type sequence: TechniqueSequence
        :param config: Full device configuration
        :type config: FullConfiguration
        :param mps_file: Path to write MPS file
        :type mps_file: FilePath
        :return: Success code (1 = success)
        :rtype: int
        :raises ValueError: If device model doesn't match configuration
        """
        
        # Get device type and convert to enum
        channel_device = BLDeviceModel(self.get_device_type(device_id))
        
        # Compare devices 
        if channel_device != config.basic.device:
            raise ValueError(f"Detected device model {channel_device.value} at device_id {device_id}, "
                             f"but received settings for device model {config.basic.device.value}.")
            
        # Write settings file
        write_techniques(sequence, config, mps_file)
        
        # Load settings
        out = self.load_settings(device_id, channel, mps_file)
        
        if out == 1:
            # Store the sequence only if successful
            self.channel_sequences[(device_id, channel)] = sequence
            
        return out
    
    @devchannel_input
    def get_settings(self, device_id: int, channel: int) -> Path:
        """Get the settings file path for a channel.
        
        :param device_id: Device identifier (or DeviceChannel object)
        :type device_id: int or DeviceChannel
        :param channel: Channel number
        :type channel: int
        :return: Path to MPS settings file
        :rtype: Path
        """
        return self.channel_settings[(device_id, channel)]
    
    @devchannel_input
    def get_sequence(self, device_id: int, channel: int) -> Path:
        """Get the technique sequence for a channel.
        
        :param device_id: Device identifier (or DeviceChannel object)
        :type device_id: int or DeviceChannel
        :param channel: Channel number
        :type channel: int
        :return: TechniqueSequence object
        :rtype: TechniqueSequence
        """
        return self.channel_sequences[(device_id, channel)]
        
    @devchannel_input
    def channel_is_done(self, device_id: int, channel: int, wait_for_buffer: bool = True) -> bool:
        """Check if a channel measurement is complete.
        
        Checks data file existence, channel status, and buffer state to determine
        if measurement is finished.
        
        :param device_id: Device identifier (or DeviceChannel object)
        :type device_id: int or DeviceChannel
        :param channel: Channel number
        :type channel: int
        :param wait_for_buffer: Whether to wait for buffer to empty
        :type wait_for_buffer: bool
        :return: True if channel is done
        :rtype: bool
        """
        # Check if data file exists for sequence
        # NOTE: all data files are created when measurement is launched, 
        # so this does not mean that the channel is done running.
        data_file = self.get_data_filename(device_id, channel, 0)
        if data_file is not None:
            # Data filename may come back as None - not yet sure in which cases this may happen
            data_status = os.path.exists(self.get_data_filename(device_id, channel, 0))    
            if not data_status:
                return data_status
        
        meas_status = self.check_measure_status(device_id, channel)
        
        # Check if channel is stopped
        is_stopped = all([
            int(meas_status['Connection']) == 0,  # Device is connected
            ChannelStatus(int(meas_status['Status'])) == ChannelStatus.STOP,  # Channel is stopped
        ])
        
        # PROBLEM: current point index seems to apply only to EIS.
        # E.g. for OCV, current point index and total point index are both frozen at values from last EIS measurement, and never get updated
        # # Check if channel has reached last point of last technique
        # # n_techniques = self.get_sequence(device_id, channel).num_techniques
        # all_points_done = all([
        #     # int(meas_status["Technique number"]) == n_techniques - 1,
        #     int(meas_status["Current point index"]) == int(meas_status["Total point index"])
        # ])
        
        # Check if the buffer is empty
        buffer_empty = (meas_status["Buffer size"] == 0 or not wait_for_buffer)
        
        # print(f"device {device_id} channel {channel}: data_status={data_status}, is_stopped={is_stopped}, buffer_empty={buffer_empty}")
        # for key in ["Current point index", "Total point index"]:
        #     print(key, meas_status[key])
        
        # return all([data_status, is_stopped, all_points_done, buffer_empty])
        return all([data_status, is_stopped, buffer_empty])
    
    def get_eis_value(self, mpr_file: Union[Path, str], index: int):
        """Read EIS data value at specific index from MPR file.
        
        :param mpr_file: Path to MPR data file
        :type mpr_file: Union[Path, str]
        :param index: Data point index
        :type index: int
        :return: Dictionary with time, frequency, and impedance values
        :rtype: dict
        :raises ValueError: If reading fails
        """
        abspath = Path(mpr_file).absolute().__str__()
        values, code = self.server.MeasureEisValue(abspath, index)
        if code == 1:
            t, f, zr, zi = values
            return {'time/s': t, 'freq/Hz': f, 'Re(Z)/Ohm': zr, '-Im(Z)/Ohm': zi}
        else:
            raise ValueError(f"Could not read EIS values at index {index} in file {mpr_file}")
    
    @devchannel_input
    async def wait_for_channel_async(
            self, 
            device_id: int, 
            channel: int, 
            min_wait: float,
            timeout: float,
            interval: float = 0.5,
            channel_status: Optional[dict] = None,
            cascading: bool = False
        ):
        """Asynchronously wait for a channel to complete measurement.
        
        :param device_id: Device identifier (or DeviceChannel object)
        :type device_id: int or DeviceChannel
        :param channel: Channel number
        :type channel: int
        :param min_wait: Minimum wait time in seconds
        :type min_wait: float
        :param timeout: Maximum wait time in seconds
        :type timeout: float
        :param interval: Status check interval in seconds
        :type interval: float
        :param channel_status: External status dictionary for async control
        :type channel_status: Optional[dict]
        :param cascading: If True, wait for upstream channels before checking 
            downstream channels to reduce IO.
        :type cascading: bool
        :return: Channel result status
        :rtype: ChannelResult
        """
        start = time.monotonic()
        
        result = ChannelResult.RUNNING
        
        def log_status(res: ChannelResult):
            self.channel_results[(device_id, channel)] = res
            
            if channel_status is not None:
                # Log status in external dict for async control
                channel_status[(device_id, channel)] = res
                
        log_status(result)
        
        while not result_is_complete(result):
            await asyncio.sleep(interval)
            elapsed = time.monotonic() - start
            
            if cascading and channel_status is not None:
                # Only check the channel if all upstream channels are done
                query = should_query(device_id, channel, channel_status)
            else:
                query = True
                
            if query:
                if self.channel_is_done(device_id, channel) and elapsed > min_wait:
                    result = ChannelResult.DONE
            
            log_status(result)
                
            if elapsed > timeout and not result_is_complete(result):
                result = ChannelResult.TIMEOUT
                break
            
        if result == ChannelResult.TIMEOUT and self.print_messages:
            print(f"WARNING: Device {device_id} Channel {channel} timed out")
            
        log_status(result)
            
        if self.print_messages:
            print("Device {} Channel {} finished in {:.1f} s with result {}".format(device_id, channel, elapsed, result.name))
            
        return result
    
    @devchannel_input
    def wait_for_channel(
            self, 
            device_id: int, 
            channel: int, 
            min_wait: float,
            timeout: float,
            interval: float = 0.5
        ):
        """Wait for a channel to complete measurement (blocking).
        
        :param device_id: Device identifier (or DeviceChannel object)
        :type device_id: int or DeviceChannel
        :param channel: Channel number
        :type channel: int
        :param min_wait: Minimum wait time in seconds
        :type min_wait: float
        :param timeout: Maximum wait time in seconds
        :type timeout: float
        :param interval: Status check interval in seconds
        :type interval: float
        :return: Channel result status
        :rtype: ChannelResult
        """
        return asyncio.run(self.wait_for_channel_async(device_id, channel, min_wait, timeout, interval))
        
    async def wait_for_channels_async(
            self,
            channels: List[DeviceChannel], 
            min_wait: float, 
            timeout: float, 
            interval: float = 0.5,
            channel_status: Optional[dict] = None,
            cascading: bool = False
            ):
        """Asynchronously wait for multiple channels to complete.
        
        :param channels: List of device channels to monitor
        :type channels: List[DeviceChannel]
        :param min_wait: Minimum wait time in seconds
        :type min_wait: float
        :param timeout: Maximum wait time in seconds
        :type timeout: float
        :param interval: Status check interval in seconds
        :type interval: float
        :param channel_status: External status dictionary for async control
        :type channel_status: Optional[dict]
        :param cascading: Wait for upstream channels sequentially
        :type cascading: bool
        :return: List of channel result statuses
        :rtype: List[ChannelResult]
        """
        if cascading and channel_status is None:
            channel_status = {}
            
        return await asyncio.gather(
            *[
                self.wait_for_channel_async(c, min_wait, timeout, interval, channel_status, cascading)
                for c in channels
            ]
        )
    
    def wait_for_channels(
            self,
            channels: List[DeviceChannel], 
            min_wait: float, 
            timeout: float, 
            interval: float = 0.5):
        """Wait for multiple channels to complete (blocking).
        
        :param channels: List of device channels to monitor
        :type channels: List[DeviceChannel]
        :param min_wait: Minimum wait time in seconds
        :type min_wait: float
        :param timeout: Maximum wait time in seconds
        :type timeout: float
        :param interval: Status check interval in seconds
        :type interval: float
        :return: List of channel result statuses
        :rtype: List[ChannelResult]
        """
        return asyncio.run(self.wait_for_channels_async(channels, min_wait, timeout, interval))
        
    @property
    def all_results_complete(self):
        """Check if all channel results are complete.
        
        :return: True if all tracked channels are done or timed out
        :rtype: bool
        """
        return check_results(self.channel_results.values())
        
        
        

    

_measure_status_keys = [
    'Status',
    'Ox/Red',
    'OCV',
    'EIS',
    'Technique number',
    'Technique code',
    'Sequence number',
    'Current loop iteration number',
    'Curent sequence within loop number',
    'Loop experiment iteration number',
    'Cycle number',
    'Counter 1',
    'Counter 2',
    'Counter 3',
    'Buffer size',
    'Time',
    'Ewe',
    'Ece',
    'Eoc',
    'I',
    'Q-Q0',
    'Aux1',
    'Aux2',
    'Irange',
    'R compensation',
    'Frequency',
    '|Z|',
    'Current point index',
    'Total point index',
    'T (deg. C)',
    'Safety limit',
    'Connection',
    'Result code'
]

class ChannelStatus(Enum):
    """Operational status of a channel.
    
    :cvar STOP: Channel is stopped
    :cvar RUN: Channel is running
    :cvar PAUSE: Channel is paused
    :cvar SYNC: Channel is in sync mode
    :cvar STOP_REC1: Channel stopped with recording type 1
    :cvar STOP_REC2: Channel stopped with recording type 2
    :cvar PAUSE_REC: Channel paused with recording
    """
    STOP = 0
    RUN = 1
    PAUSE = 2
    SYNC = 3
    STOP_REC1 = 4
    STOP_REC2 = 5
    PAUSE_REC = 6
    

class ChannelResult(Enum):
    """Result status of a channel measurement.
    
    :cvar RUNNING: Measurement is still in progress
    :cvar DONE: Measurement completed successfully
    :cvar TIMEOUT: Measurement exceeded timeout limit
    """
    RUNNING = 0
    DONE = 1
    TIMEOUT = 2
    
    
def result_is_complete(result: ChannelResult):
    """Check if a channel result indicates completion.
    
    :param result: Channel result status
    :type result: ChannelResult
    :return: True if result is DONE or TIMEOUT
    :rtype: bool
    """
    return result.value > 0

def check_results(results: List[ChannelResult]):
    """Check if all channel results are complete.
    
    :param results: List of channel results
    :type results: List[ChannelResult]
    :return: True if all results are complete
    :rtype: bool
    """
    return all([result_is_complete(r) for r in results])


def should_query(device_id: int, channel: int, channel_status: dict):
    """Determine if a channel should be queried in cascading mode.
    
    For cascading async status checks, only query downstream channels after
    all upstream channels have completed.
    
    :param device_id: Device identifier
    :type device_id: int
    :param channel: Channel number
    :type channel: int
    :param channel_status: Dictionary mapping channels to their results
    :type channel_status: dict
    :return: True if all upstream channels are complete
    :rtype: bool
    """
    # For cascading async channel status checks in wait_for_channels_async
    key = (device_id, channel)
    keys = list(channel_status.keys())
    # Get results of all upstream channels
    upstream_results = [channel_status[k] for k in keys[:keys.index(key)]]
    # If all upstream channels are done, we need to check this channel
    return check_results(upstream_results)
    