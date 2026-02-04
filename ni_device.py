"""
Hardware abstraction layer for NI-6501 devices.
Provides a clean interface for digital I/O operations.
"""

import json
import os
try:
    import nidaqmx
    from nidaqmx.constants import LineGrouping
    NI_AVAILABLE = True
except ImportError:
    NI_AVAILABLE = False

class NiDevice:
    """
    Represents a single NI-6501 device.
    Abstracts hardware access for digital I/O.
    """
    def __init__(self, device_name):
        self.device_name = device_name
        self.ni_available = NI_AVAILABLE
        if self.ni_available:
            try:
                self.task = nidaqmx.Task()
                # Configure all ports as digital I/O
                for port in range(3):
                    self.task.do_channels.add_do_chan(f"{device_name}/port{port}", line_grouping=LineGrouping.CHAN_PER_LINE)
                    self.task.di_channels.add_di_chan(f"{device_name}/port{port}", line_grouping=LineGrouping.CHAN_PER_LINE)
            except Exception as e:
                print(f"NI-DAQmx not available or device not found: {e}")
                self.ni_available = False
                self.task = None
        else:
            self.task = None
            print(f"Mock: Initialized device {device_name}")

    def set_output(self, pin, value):
        """
        Set a digital output pin.
        pin: e.g., 'p0.0'
        value: bool
        """
        if self.ni_available:
            # For simplicity, write to all, but in real, need per pin
            # Actually, since configured per port, need to handle properly
            # This is simplified; real implementation would need better mapping
            port, line = self._parse_pin(pin)
            # Assuming task has channels for all
            # This is placeholder; real code needs careful channel management
            data = [value] * 8  # Mock for port
            self.task.write(data, auto_start=True)
        else:
            print(f"Mock: Set {pin} to {value}")

    def get_input(self, pin):
        """
        Read a digital input pin.
        pin: e.g., 'p1.0'
        Returns: bool
        """
        if self.ni_available:
            # Similar issue
            return False  # Placeholder
        else:
            print(f"Mock: Read {pin}")
            return False

    def _parse_pin(self, pin):
        # e.g., 'p0.0' -> 0, 0
        port = int(pin[1])
        line = int(pin[3])
        return port, line

    def close(self):
        if self.ni_available:
            self.task.close()
        else:
            print(f"Mock: Closed device {self.device_name}")