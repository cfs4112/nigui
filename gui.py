import tkinter as tk
from tkinter import ttk
import json
import os
from tabs.utilities_tab import setup_settings_frame
from tabs.device_tab import create_device_tab
from tabs.control_panel_tab import create_control_panel_tab

class StateManager:
    """
    Manages persistent state of device pins.
    """
    def __init__(self, state_file='state.json'):
        self.state_file = state_file
        self.state = self.load_state()
        self._update_callbacks = []

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
        self._notify_update(device, pin, value)

    def register_update_callback(self, callback):
        if callback not in self._update_callbacks:
            self._update_callbacks.append(callback)

    def _notify_update(self, device, pin, value):
        for callback in list(self._update_callbacks):
            callback(device, pin, value)

    def get_current_preset(self):
        return self.state.get('current_preset', 'default.json')

    def set_current_preset(self, preset):
        self.state['current_preset'] = preset
        self.save_state()

root = tk.Tk()
root.title("Control Panel")
root.geometry("600x400")
root.minsize(600, 400)

state_manager = StateManager()

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=10, pady=10)

control_panel = create_control_panel_tab(notebook, state_manager)

def refresh_all_tabs(device, pin, value):
    for tab_id in notebook.tabs():
        tab_widget = notebook.nametowidget(tab_id)
        if hasattr(tab_widget, "refresh_from_state"):
            tab_widget.refresh_from_state()
        if hasattr(tab_widget, "refresh_output_controls"):
            tab_widget.refresh_output_controls()

state_manager.register_update_callback(refresh_all_tabs)

# Load config and add device tabs
config_file = 'config.json'
if os.path.exists(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)
    devices = config.get('devices', [])
    for dev in devices:
        create_device_tab(notebook, dev, state_manager)

settings_frame = ttk.Frame(root)
setup_settings_frame(settings_frame, root, notebook, state_manager, control_panel)

# Bottom frame for settings button
bottom_frame = ttk.Frame(root)
bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

btn_text = tk.StringVar(value="⚙ Settings")
root.btn_text = btn_text
settings_btn = ttk.Button(bottom_frame, textvariable=btn_text, command=lambda: toggle_view())
settings_btn.pack(side=tk.RIGHT, padx=10, pady=5)

def toggle_view():
    if notebook.winfo_ismapped():
        notebook.pack_forget()
        settings_frame.pack(fill="both", expand=True)
        btn_text.set("Back")
    else:
        settings_frame.pack_forget()
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        btn_text.set("⚙ Settings")

root.mainloop()