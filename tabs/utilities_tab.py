import tkinter as tk
from tkinter import ttk
import json
import os
from .device_tab import create_device_tab
from .control_panel_tab import load_preset_data

def setup_settings_frame(frame, root, notebook, state_manager, control_panel=None):
    # Load config
    config_file = 'config.json'
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
        devices = config.get('devices', ['Dev1'])
        selected_preset = config.get('selected_preset', 'default.json')
        max_devices = config.get('max_devices', 3)
    else:
        devices = ['Dev1']
        selected_preset = 'default.json'
        max_devices = 3

    num_devices = len(devices)

    # Preset selection section
    preset_frame = ttk.LabelFrame(frame, text="Preset Selection", padding=(10, 5))
    preset_frame.pack(fill="x", padx=10, pady=10)

    ttk.Label(preset_frame, text="Select Preset:").pack(side=tk.LEFT, padx=5)
    presets = [f for f in os.listdir('presets') if f.endswith('.json')]
    preset_var = tk.StringVar(value=selected_preset)
    preset_combo = ttk.Combobox(preset_frame, textvariable=preset_var, values=presets, state="readonly")
    preset_combo.pack(side=tk.LEFT, padx=5)

    # Separator
    ttk.Separator(frame, orient="horizontal").pack(fill="x", padx=10, pady=5)

    # Device configuration section
    device_frame = ttk.LabelFrame(frame, text="Device Configuration", padding=(10, 5))
    device_frame.pack(fill="x", padx=10, pady=10)

    def validate_num(value):
        if value == "":
            return False
        try:
            num = int(value)
            return 1 <= num <= max_devices
        except ValueError:
            return False

    vcmd = (device_frame.register(validate_num), '%P')

    num_frame = ttk.Frame(device_frame)
    num_frame.pack(fill="x", pady=5)
    ttk.Label(num_frame, text="Number of NI Devices:").pack(side=tk.LEFT, padx=5)
    num_devices_var = tk.IntVar(value=num_devices)
    num_devices_spin = tk.Spinbox(num_frame, from_=1, to=max_devices, textvariable=num_devices_var, validate="key", validatecommand=vcmd, width=5)
    num_devices_spin.pack(side=tk.LEFT, padx=5)

    device_labels = []
    device_entries = []
    device_frames = []

    def update_device_fields(*args):
        num = num_devices_var.get()
        # Remove extra
        while len(device_entries) > num:
            device_frames[-1].destroy()
            device_labels.pop()
            device_entries.pop()
            device_frames.pop()
        # Add new
        for i in range(len(device_entries), num):
            dev_frame = ttk.Frame(device_frame)
            dev_frame.pack(fill="x", pady=2)
            label = ttk.Label(dev_frame, text=f"Device {i+1} Name:")
            label.pack(side=tk.LEFT, padx=5)
            entry = ttk.Entry(dev_frame)
            entry.pack(side=tk.LEFT, padx=5, fill="x", expand=True)
            entry.insert(0, devices[i] if i < len(devices) else f"Dev{i+1}")
            device_labels.append(label)
            device_entries.append(entry)
            device_frames.append(dev_frame)

    num_devices_var.trace_add("write", update_device_fields)
    update_device_fields()  # Initial

    def apply_devices():
        num = num_devices_var.get()
        devices = [entry.get() for entry in device_entries[:num]]
        selected_preset = preset_var.get()
        print(f"Configured devices: {devices}, Preset: {selected_preset}")
        # Save to config
        config = {'devices': devices, 'selected_preset': selected_preset, 'max_devices': max_devices}
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        state_manager.set_current_preset(selected_preset)
        if control_panel is not None:
            preset_path = os.path.join('presets', selected_preset)
            preset_data = load_preset_data(preset_path)
            if hasattr(control_panel, "update_preset_title"):
                control_panel.update_preset_title(preset_data["title"])
            if hasattr(control_panel, "update_preset_info"):
                control_panel.update_preset_info(preset_data["info"])
            if hasattr(control_panel, "rebuild_from_preset"):
                control_panel.rebuild_from_preset(preset_path)
        # Remove existing device tabs
        for tab_id in notebook.tabs():
            tab_text = notebook.tab(tab_id, "text")
            if tab_text not in ["Control Panel"]:
                notebook.forget(tab_id)
        # Add tabs for each device
        for dev in devices:
            create_device_tab(notebook, dev, state_manager)

    # Apply button
    apply_frame = ttk.Frame(frame)
    apply_frame.pack(fill="x", padx=10, pady=10)
    ttk.Button(apply_frame, text="Apply Settings", command=apply_devices).pack(side=tk.RIGHT, padx=5)
