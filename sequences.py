"""
Sequence execution engine.
Handles running sequences in background threads.
"""

import threading
import time
from tkinter import messagebox

class SequenceExecutor:
    """
    Executes sequences defined in presets.
    """
    def __init__(self, gui, devices, preset, state_manager):
        self.gui = gui
        self.devices = devices
        self.preset = preset
        self.state_manager = state_manager

    def execute_sequence(self, sequence_name):
        sequence = self.preset.get_sequence_config(sequence_name)
        if not sequence:
            messagebox.showerror("Error", f"Sequence {sequence_name} not found")
            return
        thread = threading.Thread(target=self._run_sequence, args=(sequence,))
        thread.daemon = True
        thread.start()

    def _run_sequence(self, sequence):
        for step in sequence:
            action = step['action']
            if action == 'set':
                signal = step['signal']
                value = step['value']
                config = self.preset.get_signal_config(signal)
                pin = config['pin']
                device_name = self._get_device_for_signal(signal)
                device = self.devices[device_name]
                device.set_output(pin, value)
                self.state_manager.set_pin_state(device_name, pin, value)
                self.gui.update_signal(signal, value)
            elif action == 'wait':
                duration = step['duration']
                time.sleep(duration)
            elif action == 'wait_input':
                signal = step['signal']
                expected = step['value']
                config = self.preset.get_signal_config(signal)
                pin = config['pin']
                device_name = self._get_device_for_signal(signal)
                device = self.devices[device_name]
                while device.get_input(pin) != expected:
                    time.sleep(0.1)
            # Update progress in GUI if needed
            self.gui.update_sequence_progress(step)

    def _get_device_for_signal(self, signal):
        return self.preset.get_device_for_signal(signal)