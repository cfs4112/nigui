import tkinter as tk
from tkinter import ttk
from .device_tab import create_device_tab

def setup_settings_frame(frame, root, notebook):
    # Device configuration
    def validate_num(value):
        if value == "":
            return False
        try:
            num = int(value)
            return 1 <= num <= 3
        except ValueError:
            return False

    vcmd = (frame.register(validate_num), '%P')

    ttk.Label(frame, text="Number of NI Devices:").grid(row=0, column=0, padx=5, pady=5)
    num_devices_var = tk.IntVar(value=1)
    num_devices_spin = tk.Spinbox(frame, from_=1, to=3, textvariable=num_devices_var, validate="key", validatecommand=vcmd)
    num_devices_spin.grid(row=0, column=1, padx=5, pady=5)

    device_labels = []
    device_entries = []

    def update_device_fields(*args):
        num = num_devices_var.get()
        # Remove extra
        while len(device_entries) > num:
            device_labels[-1].destroy()
            device_entries[-1].destroy()
            device_labels.pop()
            device_entries.pop()
        # Add new
        for i in range(len(device_entries), num):
            label = ttk.Label(frame, text=f"Device {i+1} Name:")
            label.grid(row=i+1, column=0, padx=5, pady=5)
            entry = ttk.Entry(frame)
            entry.grid(row=i+1, column=1, padx=5, pady=5)
            entry.insert(0, f"Dev{i+1}")
            device_labels.append(label)
            device_entries.append(entry)

    num_devices_var.trace_add("write", update_device_fields)
    update_device_fields()  # Initial

    def apply_devices():
        num = num_devices_var.get()
        devices = [entry.get() for entry in device_entries[:num]]
        print(f"Configured devices: {devices}")
        # Remove existing device tabs
        for tab_id in notebook.tabs():
            tab_text = notebook.tab(tab_id, "text")
            if tab_text not in ["Control Panel"]:
                notebook.forget(tab_id)
        # Add tabs for each device
        for dev in devices:
            create_device_tab(notebook, dev)

    ttk.Button(frame, text="Apply", command=apply_devices).grid(row=11, column=0, columnspan=2, pady=10)