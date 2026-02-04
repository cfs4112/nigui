"""
Main GUI application for NI-6501 control.
Uses Tkinter for cross-platform interface.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from ni_device import NiDevice
from config import Preset
from state import StateManager
from sequences import SequenceExecutor

class GuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NI-6501 Control System")
        self.devices = {}
        self.state_manager = StateManager()
        current_preset = self.state_manager.get_current_preset()
        self.preset_file = f'presets/{current_preset}'
        self.preset = Preset(self.preset_file)
        self.executor = SequenceExecutor(self, self.devices, self.preset, self.state_manager)
        self.signal_widgets = {}
        self.power_timers = {}
        self.input_thread = None
        self.running = True

        # Initialize devices
        for dev_name in self.preset.devices:
            self.devices[dev_name] = NiDevice(dev_name)
            # Load state
            for pin in self.state_manager.state.get(dev_name, {}):
                state = self.state_manager.get_pin_state(dev_name, pin)
                self.devices[dev_name].set_output(pin, state)

        # Notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Per-device tabs
        for dev_name in self.preset.devices:
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=f"Device {dev_name}")
            self.create_device_tab(tab, dev_name)

        # Control panel tab
        control_tab = ttk.Frame(self.notebook)
        self.notebook.add(control_tab, text="Control Panel")
        self.create_control_panel(control_tab)

        # Settings tab
        settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(settings_tab, text="Settings")
        self.create_settings_tab(settings_tab)

        # Start input polling
        self.start_input_polling()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_device_tab(self, tab, dev_name):
        device = self.devices[dev_name]
        frame = ttk.Frame(tab)
        frame.pack(pady=10)
        for port in range(3):
            ttk.Label(frame, text=f"Port {port}").grid(row=port*9, column=0, columnspan=8)
            for line in range(8):
                pin = f"p{port}.{line}"
                state = self.state_manager.get_pin_state(dev_name, pin)
                btn = tk.Button(frame, text=f"{pin}: {'High' if state else 'Low'}",
                                command=lambda p=pin, d=dev_name: self.toggle_pin(d, p))
                btn.grid(row=port*9 + line + 1, column=0, columnspan=2)
                self.signal_widgets[(dev_name, pin)] = btn

    def create_control_panel(self, tab):
        # Signals
        signals_frame = ttk.LabelFrame(tab, text="Signals")
        signals_frame.pack(fill=tk.X, padx=10, pady=5)
        for signal_name, config in self.preset.signals.items():
            sig_type = config['type']
            label = config.get('label', signal_name)
            if sig_type == 'output':
                btn = tk.Button(signals_frame, text=label,
                                command=lambda s=signal_name: self.toggle_signal(s))
                btn.pack(side=tk.LEFT, padx=5)
                self.signal_widgets[signal_name] = btn
                self.update_signal(signal_name, self.get_signal_state(signal_name))
            elif sig_type == 'input':
                lbl = tk.Label(signals_frame, text=label, bg='gray')
                lbl.pack(side=tk.LEFT, padx=5)
                self.signal_widgets[signal_name] = lbl
            elif sig_type == 'power':
                btn = tk.Button(signals_frame, text=label, bg='red',
                                command=lambda s=signal_name: self.toggle_power(s))
                btn.pack(side=tk.LEFT, padx=5)
                self.signal_widgets[signal_name] = btn
                self.power_timers[signal_name] = None

        # Groups
        groups_frame = ttk.LabelFrame(tab, text="Groups")
        groups_frame.pack(fill=tk.X, padx=10, pady=5)
        for group_name, config in self.preset.groups.items():
            btn = tk.Button(groups_frame, text=group_name.replace('_', ' ').title(),
                            command=lambda g=group_name: self.execute_group(g))
            btn.pack(side=tk.LEFT, padx=5)

        # Sequences
        seq_frame = ttk.LabelFrame(tab, text="Sequences")
        seq_frame.pack(fill=tk.X, padx=10, pady=5)
        self.seq_progress = tk.Label(seq_frame, text="Ready")
        self.seq_progress.pack()
        for seq_name in self.preset.sequences:
            btn = tk.Button(seq_frame, text=seq_name.replace('_', ' ').title(),
                            command=lambda s=seq_name: self.executor.execute_sequence(s))
            btn.pack(side=tk.LEFT, padx=5)

    def toggle_pin(self, dev_name, pin):
        current = self.state_manager.get_pin_state(dev_name, pin)
        new_state = not current
        self.devices[dev_name].set_output(pin, new_state)
        self.state_manager.set_pin_state(dev_name, pin, new_state)
        self.signal_widgets[(dev_name, pin)].config(text=f"{pin}: {'High' if new_state else 'Low'}")

    def toggle_signal(self, signal_name):
        config = self.preset.get_signal_config(signal_name)
        pin = config['pin']
        dev_name = self.preset.get_device_for_signal(signal_name)
        self.toggle_pin(dev_name, pin)
        self.update_signal(signal_name, self.get_signal_state(signal_name))

    def toggle_power(self, signal_name):
        if self.power_timers.get(signal_name):
            messagebox.showinfo("Cooldown", "Power is on cooldown")
            return
        config = self.preset.get_signal_config(signal_name)
        cooldown = config.get('cooldown', 0)
        self.toggle_signal(signal_name)
        if cooldown > 0:
            self.power_timers[signal_name] = cooldown
            self.signal_widgets[signal_name].config(state=tk.DISABLED)
            threading.Thread(target=self._power_cooldown, args=(signal_name,)).start()

    def _power_cooldown(self, signal_name):
        while self.power_timers[signal_name] > 0:
            time.sleep(1)
            self.power_timers[signal_name] -= 1
            self.root.after(0, lambda: self.signal_widgets[signal_name].config(text=f"{self.preset.signals[signal_name]['label']} ({self.power_timers[signal_name]}s)"))
        self.power_timers[signal_name] = None
        self.root.after(0, lambda: self.signal_widgets[signal_name].config(state=tk.NORMAL, text=self.preset.signals[signal_name]['label']))

    def execute_group(self, group_name):
        config = self.preset.get_group_config(group_name)
        for signal in config['signals']:
            sig_config = self.preset.get_signal_config(signal)
            dev_name = self.preset.get_device_for_signal(signal)
            if sig_config['type'] == 'power':
                if messagebox.askyesno("Confirm", f"Toggle power for {signal}?"):
                    self.devices[dev_name].set_output(sig_config['pin'], config['state'])
                    self.state_manager.set_pin_state(dev_name, sig_config['pin'], config['state'])
                    self.update_signal(signal, config['state'])
            else:
                self.devices[dev_name].set_output(sig_config['pin'], config['state'])
                self.state_manager.set_pin_state(dev_name, sig_config['pin'], config['state'])
                self.update_signal(signal, config['state'])

    def get_signal_state(self, signal_name):
        config = self.preset.get_signal_config(signal_name)
        pin = config['pin']
        dev_name = self.preset.get_device_for_signal(signal_name)
        return self.state_manager.get_pin_state(dev_name, pin)

    def update_signal(self, signal_name, state):
        config = self.preset.get_signal_config(signal_name)
        sig_type = config['type']
        widget = self.signal_widgets.get(signal_name)
        if sig_type == 'output':
            on_color = config.get('on_color', 'green')
            off_color = config.get('off_color', 'gray')
            widget.config(bg=on_color if state else off_color)
            secondary = config.get('secondary_label', {})
            text = secondary.get('on' if state else 'off', config['label'])
            widget.config(text=text)
        elif sig_type == 'input':
            active = config.get('active_high', True)
            color = 'yellow' if (state == active) else 'gray'
            widget.config(bg=color)
        elif sig_type == 'power':
            on_color = config.get('on_color', 'red')
            off_color = config.get('off_color', 'black')
            widget.config(bg=on_color if state else off_color)

    def create_settings_tab(self, tab):
        import os
        presets = [f for f in os.listdir('presets') if f.endswith('.json')]
        ttk.Label(tab, text="Select Preset:").pack(pady=10)
        self.preset_var = tk.StringVar(value=self.state_manager.get_current_preset())
        combo = ttk.Combobox(tab, textvariable=self.preset_var, values=presets)
        combo.pack()
        combo.bind("<<ComboboxSelected>>", self.on_preset_change)
        ttk.Button(tab, text="Reload Preset", command=self.reload_preset).pack(pady=10)

    def reload_preset(self):
        self.preset = Preset(self.preset_file)
        self.executor = SequenceExecutor(self, self.devices, self.preset, self.state_manager)
        # Recreate control panel
        for i, tab_id in enumerate(self.notebook.tabs()):
            if self.notebook.tab(tab_id, "text") == "Control Panel":
                self.notebook.forget(i)
                new_tab = ttk.Frame(self.notebook)
                self.notebook.insert(i, new_tab, text="Control Panel")
                self.create_control_panel(new_tab)
                break

    def on_preset_change(self, event):
        selected = self.preset_var.get()
        self.state_manager.set_current_preset(selected)
        self.preset_file = f'presets/{selected}'
        self.preset = Preset(self.preset_file)
        self.executor = SequenceExecutor(self, self.devices, self.preset, self.state_manager)
        # Recreate control panel
        for i, tab_id in enumerate(self.notebook.tabs()):
            if self.notebook.tab(tab_id, "text") == "Control Panel":
                self.notebook.forget(i)
                new_tab = ttk.Frame(self.notebook)
                self.notebook.insert(i, new_tab, text="Control Panel")
                self.create_control_panel(new_tab)
                break

    def start_input_polling(self):
        self.input_thread = threading.Thread(target=self._poll_inputs)
        self.input_thread.daemon = True
        self.input_thread.start()

    def _poll_inputs(self):
        while self.running:
            for signal_name, config in self.preset.signals.items():
                if config['type'] == 'input':
                    pin = config['pin']
                    dev_name = self.preset.get_device_for_signal(signal_name)
                    state = self.devices[dev_name].get_input(pin)
                    self.root.after(0, lambda s=signal_name, st=state: self.update_signal(s, st))
            time.sleep(0.5)

    def on_close(self):
        self.running = False
        for device in self.devices.values():
            device.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = GuiApp(root)
    root.mainloop()
