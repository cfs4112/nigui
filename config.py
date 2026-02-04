"""
Configuration management for presets.
Loads and parses JSON preset files.
"""

import json
import os

def parse_pin(pin):
    """
    Parse pin string like 'p0.0' or 'd1p0.0' to (device_index, port, line)
    """
    if pin.startswith('d'):
        parts = pin.split('p')
        d_part = parts[0][1:]  # after d
        device_index = int(d_part)
        p_line = parts[1].split('.')
        port = int(p_line[0])
        line = int(p_line[1])
    else:
        device_index = 0
        port = int(pin[1])
        line = int(pin[3])
    return device_index, port, line

class Preset:
    """
    Represents a preset configuration loaded from JSON.
    """
    def __init__(self, preset_file):
        with open(preset_file, 'r') as f:
            self.data = json.load(f)
        self.devices = self.data.get('devices', [])
        self.signals = self.data.get('signals', {})
        self.groups = self.data.get('groups', {})
        self.sequences = self.data.get('sequences', {})

    def get_signal_config(self, signal_name):
        return self.signals.get(signal_name, {})

    def get_group_config(self, group_name):
        return self.groups.get(group_name, {})

    def get_sequence_config(self, sequence_name):
        return self.sequences.get(sequence_name, [])

    def get_device_for_signal(self, signal_name):
        config = self.get_signal_config(signal_name)
        pin = config.get('pin', 'p0.0')
        device_index, _, _ = parse_pin(pin)
        return self.devices[device_index]