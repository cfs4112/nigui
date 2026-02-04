"""
State persistence management.
Loads and saves device states to JSON.
"""

import json
import os

class StateManager:
    """
    Manages persistent state of device pins.
    """
    def __init__(self, state_file='state.json'):
        self.state_file = state_file
        self.state = self.load_state()

    def load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {}

    def save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def get_pin_state(self, device, pin):
        return self.state.get(device, {}).get(pin, False)

    def set_pin_state(self, device, pin, value):
        if device not in self.state:
            self.state[device] = {}
        self.state[device][pin] = value
        self.save_state()

    def get_current_preset(self):
        return self.state.get('current_preset', 'default.json')

    def set_current_preset(self, preset):
        self.state['current_preset'] = preset
        self.save_state()