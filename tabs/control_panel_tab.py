import json
import os
import time
import tkinter as tk
from tkinter import ttk


class HoverTooltip:
    """Simple hover tooltip with delay."""

    def __init__(self, widget, text, delay_ms=3000):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._after_id = None
        self._tip_window = None

        self.widget.bind("<Enter>", self._schedule)
        self.widget.bind("<Leave>", self._hide)
        self.widget.bind("<ButtonPress>", self._hide)

    def _schedule(self, _event=None):
        self._cancel()
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _cancel(self, _event=None):
        if self._after_id is not None:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self):
        if self._tip_window is not None:
            return
        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self._tip_window = tk.Toplevel(self.widget)
        self._tip_window.wm_overrideredirect(True)
        self._tip_window.wm_attributes("-topmost", True)
        for option, value in (("-type", "tooltip"), ("-toolwindow", True), ("-takefocus", 0)):
            try:
                self._tip_window.wm_attributes(option, value)
            except tk.TclError:
                pass
        self._tip_window.transient(self.widget)
        self._tip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self._tip_window,
            text=self.text,
            background="#1f1f1f",
            foreground="#ffffff",
            relief="solid",
            borderwidth=1,
            padx=6,
            pady=4,
        )
        label.pack()

    def _hide(self, _event=None):
        self._cancel()
        if self._tip_window is not None:
            self._tip_window.destroy()
            self._tip_window = None


class OutputControl(ttk.Frame):
    """UI control for an output-type signal in the control panel."""

    def __init__(self, parent, state_manager, device, pin, label,
                 on_color=None, off_color=None, secondary_label=None,
                 write_callback=None):
        super().__init__(parent)
        self.state_manager = state_manager
        self.device = device
        self.pin = pin
        self.on_color = on_color
        self.off_color = off_color
        self.secondary_label = secondary_label
        self.base_label = label
        self.write_callback = write_callback

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.button = tk.Button(self, text=label, command=self.toggle)
        self.button.grid(row=0, column=0, sticky="nsew")
        self.default_button_bg = self.button.cget("background")
        self.default_button_fg = self.button.cget("foreground")

        device_label = self.device or "Unknown"
        pin_label = self.pin or "Unknown"
        tooltip_text = f"Device: {device_label}\nLine: {pin_label}"
        HoverTooltip(self.button, tooltip_text)

        self.refresh()

    def _status_text(self, is_on):
        if self.secondary_label:
            return self.secondary_label.get("on") if is_on else self.secondary_label.get("off")
        return "ON" if is_on else "OFF"

    def refresh(self):
        is_on = bool(self.state_manager.get_pin_state(self.device, self.pin))
        if self.secondary_label:
            self.button.configure(text=f"{self.base_label}: {self._status_text(is_on)}")
        if self.on_color is not None and self.off_color is not None:
            self.button.configure(
                background=self.on_color if is_on else self.off_color,
                activebackground=self.on_color if is_on else self.off_color,
                foreground="#ffffff" if is_on else self.default_button_fg,
            )
        else:
            self.button.configure(
                background=self.default_button_bg,
                activebackground=self.default_button_bg,
                foreground=self.default_button_fg,
            )

    def set_state(self, value):
        self.state_manager.set_pin_state(self.device, self.pin, bool(value))
        if self.write_callback is not None:
            self.write_callback(self.device, self.pin, bool(value))
        self.refresh()

    def toggle(self):
        current = bool(self.state_manager.get_pin_state(self.device, self.pin))
        self.set_state(not current)


class GroupControl(ttk.Frame):
    """UI control for a group-type action button."""

    def __init__(self, parent, state_manager, label, actions,
                 on_color="#4CAF50", off_color="#cac9c8"):
        super().__init__(parent)
        self.state_manager = state_manager
        self.label = label
        self.actions = actions
        self.on_color = on_color
        self.off_color = off_color

        self.button = tk.Button(self, text=label, command=self.apply_group)
        self.button.pack(fill="x", expand=True)
        self.default_button_bg = self.button.cget("background")
        self.default_button_fg = self.button.cget("foreground")

        self.log_callback = None
        self.refresh()

    def _is_active(self):
        for action in self.actions:
            dev = action.get("device", "")
            pin = action.get("pin", "")
            state = bool(action.get("state", False))
            if self.state_manager.get_pin_state(dev, pin) != state:
                return False
        return True if self.actions else False

    def refresh(self):
        is_active = self._is_active()
        if is_active:
            self.button.configure(
                background=self.on_color,
                activebackground=self.on_color,
                foreground="#ffffff",
            )
        else:
            self.button.configure(
                background=self.off_color,
                activebackground=self.off_color,
                foreground=self.default_button_fg,
            )

    def apply_group(self):
        for action in self.actions:
            dev = action.get("device", "")
            pin = action.get("pin", "")
            state = bool(action.get("state", False))
            self.state_manager.set_pin_state(dev, pin, state)
        if self.log_callback is not None:
            self.log_callback(f"Group applied: {self.label}")
        self.refresh()


class SequenceControl(ttk.Frame):
    """UI control for a sequence-type action button."""

    def __init__(self, parent, state_manager, label, steps, disable_callback, enable_callback, log_callback=None):
        super().__init__(parent)
        self.state_manager = state_manager
        self.label = label
        self.steps = steps
        self.disable_callback = disable_callback
        self.enable_callback = enable_callback
        self.log_callback = log_callback
        self._running = False

        self.button = tk.Button(self, text=label, command=self.start)
        self.button.pack(fill="x", expand=True)

    def start(self):
        if self._running:
            return
        self._running = True
        if self.log_callback is not None:
            self.log_callback(f"Sequence started: {self.label}")
        self.disable_callback()
        self._run_step(0, time.monotonic())

    def _run_step(self, index, start_time):
        if index >= len(self.steps):
            self._finish()
            return
        step = self.steps[index]
        action = step.get("action", "")

        if action == "set":
            dev = step.get("device", "")
            pin = step.get("pin", "")
            state = bool(step.get("state", False))
            self.state_manager.set_pin_state(dev, pin, state)
            if self.log_callback is not None:
                self.log_callback(f"Sequence {self.label}: set {dev} {pin} -> {state}")
            self.after(10, lambda: self._run_step(index + 1, start_time))
        elif action == "wait":
            seconds = float(step.get("seconds", 0))
            if self.log_callback is not None:
                self.log_callback(f"Sequence {self.label}: wait {seconds}s")
            self.after(int(seconds * 1000), lambda: self._run_step(index + 1, start_time))
        elif action == "wait_for":
            dev = step.get("device", "")
            pin = step.get("pin", "")
            desired = bool(step.get("state", False))
            timeout = float(step.get("timeout_seconds", 0))
            poll_ms = int(step.get("poll_ms", 200))
            if self.state_manager.get_pin_state(dev, pin) == desired:
                if self.log_callback is not None:
                    self.log_callback(f"Sequence {self.label}: condition met {dev} {pin} == {desired}")
                self.after(10, lambda: self._run_step(index + 1, start_time))
                return
            if timeout > 0 and (time.monotonic() - start_time) >= timeout:
                if self.log_callback is not None:
                    self.log_callback(f"Sequence {self.label}: timeout waiting for {dev} {pin}")
                self._finish()
                return
            if self.log_callback is not None:
                self.log_callback(f"Sequence {self.label}: waiting for {dev} {pin} == {desired}")
            self.after(poll_ms, lambda: self._run_step(index, start_time))
        else:
            if self.log_callback is not None:
                self.log_callback(f"Sequence {self.label}: unknown step")
            self._finish()

    def _finish(self):
        self._running = False
        self.enable_callback()
        if self.log_callback is not None:
            self.log_callback(f"Sequence finished: {self.label}")


class PowerControl(ttk.Frame):
    """UI control for a power-type signal with cooldown timer."""

    def __init__(self, parent, state_manager, device, pin, label,
                 on_color=None, off_color=None, secondary_label=None,
                 cooldown_seconds=0, write_callback=None):
        super().__init__(parent)
        self.state_manager = state_manager
        self.device = device
        self.pin = pin
        self.on_color = on_color
        self.off_color = off_color
        self.secondary_label = secondary_label
        self.base_label = label
        self.cooldown_seconds = int(cooldown_seconds or 0)
        self.write_callback = write_callback
        self._cooldown_after = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.button = tk.Button(self, text=label, command=self.toggle)
        self.button.grid(row=0, column=0, sticky="nsew")
        self.default_button_bg = self.button.cget("background")
        self.default_button_fg = self.button.cget("foreground")

        device_label = self.device or "Unknown"
        pin_label = self.pin or "Unknown"
        tooltip_text = f"Device: {device_label}\nLine: {pin_label}"
        HoverTooltip(self.button, tooltip_text)

        self.cooldown_label = tk.Label(self, text="", fg="#b00020")
        self.cooldown_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 0))

        self.refresh()

    def _status_text(self, is_on):
        if self.secondary_label:
            return self.secondary_label.get("on") if is_on else self.secondary_label.get("off")
        return "ON" if is_on else "OFF"

    def _start_cooldown(self):
        if self.cooldown_seconds <= 0:
            return
        if self._cooldown_after is not None:
            self.after_cancel(self._cooldown_after)
        self.button.configure(state="disabled")
        self._tick_cooldown(self.cooldown_seconds)

    def _tick_cooldown(self, remaining):
        if remaining <= 0:
            self.cooldown_label.configure(text="")
            self.button.configure(state="normal")
            self._cooldown_after = None
            return
        self.cooldown_label.configure(text=f"Cooldown {remaining}s")
        self._cooldown_after = self.after(1000, lambda: self._tick_cooldown(remaining - 1))

    def refresh(self):
        is_on = bool(self.state_manager.get_pin_state(self.device, self.pin))
        if self.secondary_label:
            self.button.configure(text=f"{self.base_label}: {self._status_text(is_on)}")
        if self.on_color is not None and self.off_color is not None:
            self.button.configure(
                background=self.on_color if is_on else self.off_color,
                activebackground=self.on_color if is_on else self.off_color,
                foreground="#ffffff" if is_on else self.default_button_fg,
            )
        else:
            self.button.configure(
                background=self.default_button_bg,
                activebackground=self.default_button_bg,
                foreground=self.default_button_fg,
            )

    def set_state(self, value):
        self.state_manager.set_pin_state(self.device, self.pin, bool(value))
        if self.write_callback is not None:
            self.write_callback(self.device, self.pin, bool(value))
        self.refresh()
        self._start_cooldown()

    def toggle(self):
        current = bool(self.state_manager.get_pin_state(self.device, self.pin))
        self.set_state(not current)


class InputControl(ttk.Frame):
    """UI control for an input-type signal in the control panel."""

    def __init__(self, parent, state_manager, device, pin, label,
                 on_color=None, off_color=None, active_level="ACTIVE_HIGH"):
        super().__init__(parent)
        self.state_manager = state_manager
        self.device = device
        self.pin = pin
        self.on_color = on_color
        self.off_color = off_color
        self.active_level = (active_level or "ACTIVE_HIGH").upper()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.label = ttk.Label(self, text=label)
        self.label.grid(row=0, column=0, sticky="w")

        self.indicator = tk.Canvas(
            self,
            width=16,
            height=16,
            highlightthickness=0,
            bd=0,
            relief="flat",
        )
        self.indicator.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self._indicator_rect = self.indicator.create_rectangle(
            0,
            0,
            15,
            15,
            fill=self.indicator.cget("background"),
            outline="#5a5a5a",
            width=1,
        )

        device_label = self.device or "Unknown"
        pin_label = self.pin or "Unknown"
        tooltip_text = f"Device: {device_label}\nLine: {pin_label}"
        HoverTooltip(self.label, tooltip_text)
        HoverTooltip(self.indicator, tooltip_text)

        self.refresh()

    def refresh(self):
        raw_state = bool(self.state_manager.get_pin_state(self.device, self.pin))
        is_active = raw_state if self.active_level == "ACTIVE_HIGH" else not raw_state
        if self.on_color is not None and self.off_color is not None:
            color = self.on_color if is_active else self.off_color
        else:
            color = self.indicator.cget("background")
        self.indicator.itemconfig(self._indicator_rect, fill=color)


def load_preset_data(preset_file, default_title="", default_info=""):
    if os.path.exists(preset_file):
        with open(preset_file, "r") as f:
            preset_data = json.load(f) or {}
        return {
            "title": preset_data.get("title", default_title),
            "info": preset_data.get("info", default_info),
        }
    return {"title": default_title, "info": default_info}


def load_preset_file(preset_file):
    if os.path.exists(preset_file):
        with open(preset_file, "r") as f:
            return json.load(f) or {}
    return {}


def create_control_panel_tab(notebook, state_manager):
    """Create and add the Control Panel tab to the notebook."""
    control_panel = ttk.Frame(notebook)
    notebook.add(control_panel, text="Control Panel")

    preset_title = ""
    preset_info = ""
    config_file = "config.json"
    preset_file = "presets/default.json"
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            config = json.load(f)
        preset_file = os.path.join("presets", config.get("selected_preset", "default.json"))

    preset_data = load_preset_data(preset_file, preset_title, preset_info)
    preset_title = preset_data["title"]
    preset_info = preset_data["info"]

    preset_label = ttk.Label(
        control_panel,
        text=f"{preset_title}",
        font=("TkDefaultFont", 12, "bold")
    )
    
    preset_label.pack(anchor="w", padx=10, pady=(10, 5))

    def update_preset_title(new_title):
        preset_label.configure(text=new_title)

    control_panel.update_preset_title = update_preset_title

    content_frame = ttk.Frame(control_panel)
    content_frame.pack(fill="both", expand=True)
    content_frame.rowconfigure(0, weight=1)

    info = None
    if preset_info:
        info = ttk.Label(
            control_panel,
            text=preset_info
        )
        info.pack(anchor="w", padx=10, pady=(0, 10), before=content_frame)
    else:
        preset_label.pack_configure(pady=(10, 2))

    def update_preset_info(new_info):
        nonlocal info
        if new_info:
            if info is None:
                info = ttk.Label(control_panel, text=new_info)
                info.pack(anchor="w", padx=10, pady=(0, 10), before=content_frame)
            else:
                info.configure(text=new_info)
            preset_label.pack_configure(pady=(10, 5))
        else:
            if info is not None:
                info.destroy()
                info = None
            preset_label.pack_configure(pady=(10, 2))

    control_panel.update_preset_info = update_preset_info


    def clear_section(name):
        existing = getattr(control_panel, name, None)
        if existing is not None and existing.winfo_exists():
            existing.destroy()
        setattr(control_panel, name, None)

    def create_io_section(column_index, expand):
        clear_section("io_section")
        section = ttk.LabelFrame(content_frame, text="I/O", padding=(6, 4))
        section.grid(row=0, column=column_index, sticky="nsew" if expand else "ns", padx=6, pady=(0, 6))
        section.pack_propagate(True)
        control_panel.io_section = section
        return section

    def create_right_column(column_index, expand):
        clear_section("right_column")
        right_column = ttk.Frame(content_frame)
        right_column.grid(row=0, column=column_index, sticky="nsew" if expand else "ns", padx=6, pady=(0, 6))
        right_column.columnconfigure(0, weight=1)
        control_panel.right_column = right_column
        return right_column

    def create_group_sequence_section(right_column, fill_space=False):
        clear_section("group_sequence_section")
        section = ttk.LabelFrame(right_column, text="Groups / Sequences", padding=(6, 4))
        section.grid(row=0, column=0, sticky="nsew" if fill_space else "ew", pady=(0, 6))
        section.columnconfigure(0, weight=1)
        section.pack_propagate(True)
        control_panel.group_sequence_section = section
        return section

    def create_log_section(right_column):
        clear_section("log_section")
        section = ttk.LabelFrame(right_column, text="Event Log", padding=(6, 4))
        section.grid(row=1, column=0, sticky="nsew", pady=(0, 6))
        section.columnconfigure(0, weight=1)
        section.rowconfigure(0, weight=1)
        text = tk.Text(section, height=6, wrap="word", state="disabled")
        text.grid(row=0, column=0, sticky="nsew")
        control_panel.log_section = section
        control_panel.log_text = text
        return section

    def create_power_section(right_column):
        clear_section("power_section")
        section = ttk.LabelFrame(right_column, text="Power", padding=(6, 4))
        section.grid(row=2, column=0, sticky="ew")
        section.columnconfigure(0, weight=1)
        section.pack_propagate(True)
        control_panel.power_section = section
        return section

    def log_event(message):
        log_text = getattr(control_panel, "log_text", None)
        if log_text is None:
            return
        timestamp = time.strftime("%H:%M:%S")
        log_text.configure(state="normal")
        log_text.insert("end", f"[{timestamp}] {message}\n")
        log_text.see("end")
        log_text.configure(state="disabled")

    control_panel.log_event = log_event

    def set_controls_state(state):
        for output_control in getattr(control_panel, "output_controls", []):
            output_control.button.configure(state=state)
        for input_control in getattr(control_panel, "input_controls", []):
            input_control.label.configure(state=state)
        for power_control in getattr(control_panel, "power_controls", []):
            power_control.button.configure(state=state)
        for group_control in getattr(control_panel, "group_controls", []):
            group_control.button.configure(state=state)
        for sequence_control in getattr(control_panel, "sequence_controls", []):
            sequence_control.button.configure(state=state)

    def build_io_controls(preset_path):
        output_controls = []
        input_controls = []
        power_controls = []
        group_controls = []
        sequence_controls = []
        clear_section("io_section")
        clear_section("power_section")
        clear_section("group_sequence_section")
        clear_section("log_section")
        clear_section("right_column")
        control_panel.log_text = None

        power_row = None
        power_index = 0

        configured_devices = set()
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                cfg = json.load(f) or {}
            configured_devices = set(cfg.get("devices", []))

        preset = load_preset_file(preset_path)
        layout = preset.get("layout", {})
        controls = layout.get("controls", [])
        event_log_enabled = bool(preset.get("event_log", False))

        has_io = any(c.get("type", "").lower() in {"output", "input", "break"} for c in controls)
        has_power = any(c.get("type", "").lower() == "power" for c in controls)
        has_group_seq = any(c.get("type", "").lower() in {"group", "sequence"} for c in controls)
        has_right = has_power or has_group_seq or event_log_enabled

        if has_io and not has_right:
            content_frame.columnconfigure(0, weight=1)
            content_frame.columnconfigure(1, weight=0)
            io_section = create_io_section(column_index=0, expand=True)
            right_column = None
        elif has_right and not has_io:
            content_frame.columnconfigure(0, weight=1)
            content_frame.columnconfigure(1, weight=0)
            io_section = None
            right_column = create_right_column(column_index=0, expand=True)
        else:
            content_frame.columnconfigure(0, weight=0)
            content_frame.columnconfigure(1, weight=1)
            io_section = create_io_section(column_index=0, expand=False) if has_io else None
            right_column = create_right_column(column_index=1, expand=True) if has_right else None

        group_container = None
        power_container = None
        if right_column is not None:
            right_column.rowconfigure(0, weight=1 if (has_group_seq and not event_log_enabled) else 0)
            right_column.rowconfigure(1, weight=1 if event_log_enabled else 0)
            if has_group_seq:
                group_container = create_group_sequence_section(right_column, fill_space=not event_log_enabled)
            if event_log_enabled:
                create_log_section(right_column)
            if has_power:
                power_container = create_power_section(right_column)
                power_row = ttk.Frame(power_container)
                power_row.grid(row=0, column=0, sticky="ew")
                power_row.columnconfigure(0, weight=1)

        for control in controls:
            control_type = control.get("type", "").lower()
            if control_type == "output":
                if io_section is None:
                    continue
                output_widget = OutputControl(
                    io_section,
                    state_manager,
                    control.get("device", ""),
                    control.get("pin", ""),
                    control.get("label", control.get("id", "")),
                    on_color=control.get("on_color"),
                    off_color=control.get("off_color"),
                    secondary_label=control.get("secondary_label"),
                )
                if output_widget.device not in configured_devices:
                    output_widget.button.configure(state="disabled", foreground="#b00020")
                output_widget.pack(fill="x", anchor="w", pady=2)
                output_controls.append(output_widget)
            elif control_type == "input":
                if io_section is None:
                    continue
                input_widget = InputControl(
                    io_section,
                    state_manager,
                    control.get("device", ""),
                    control.get("pin", ""),
                    control.get("label", control.get("id", "")),
                    on_color=control.get("on_color"),
                    off_color=control.get("off_color"),
                    active_level=control.get("active_level", "ACTIVE_HIGH"),
                )
                input_widget.pack(fill="x", anchor="w", pady=2)
                input_controls.append(input_widget)
            elif control_type == "power":
                if power_container is None:
                    continue
                power_widget = PowerControl(
                    power_row,
                    state_manager,
                    control.get("device", ""),
                    control.get("pin", ""),
                    control.get("label", control.get("id", "")),
                    on_color=control.get("on_color"),
                    off_color=control.get("off_color"),
                    secondary_label=control.get("secondary_label"),
                    cooldown_seconds=control.get("cooldown_seconds", 0),
                )
                if power_widget.device not in configured_devices:
                    power_widget.button.configure(state="disabled", foreground="#b00020")
                power_widget.grid(row=0, column=power_index, padx=4, pady=2, sticky="ew")
                power_row.columnconfigure(power_index, weight=1)
                power_index += 1
                power_controls.append(power_widget)
            elif control_type == "group":
                if group_container is None:
                    continue
                group_widget = GroupControl(
                    group_container,
                    state_manager,
                    control.get("label", control.get("id", "")),
                    control.get("actions", []),
                    on_color=control.get("on_color", "#4CAF50"),
                    off_color=control.get("off_color", "#cac9c8"),
                )
                group_widget.log_callback = log_event
                group_widget.pack(fill="x", anchor="w", pady=2)
                group_controls.append(group_widget)
            elif control_type == "sequence":
                if group_container is None:
                    continue
                seq_widget = SequenceControl(
                    group_container,
                    state_manager,
                    control.get("label", control.get("id", "")),
                    control.get("steps", []),
                    disable_callback=lambda: set_controls_state("disabled"),
                    enable_callback=lambda: set_controls_state("normal"),
                    log_callback=log_event,
                )
                seq_widget.pack(fill="x", anchor="w", pady=2)
                sequence_controls.append(seq_widget)
            elif control_type == "break":
                if io_section is None:
                    continue
                spacer = ttk.Frame(io_section, height=8)
                spacer.pack(fill="x", pady=4)

        control_panel.output_controls = output_controls
        control_panel.input_controls = input_controls
        control_panel.power_controls = power_controls
        control_panel.group_controls = group_controls
        control_panel.sequence_controls = sequence_controls

    def rebuild_from_preset(preset_path):
        build_io_controls(preset_path)

    control_panel.rebuild_from_preset = rebuild_from_preset

    def refresh_output_controls():
        for output_control in getattr(control_panel, "output_controls", []):
            output_control.refresh()

    control_panel.refresh_output_controls = refresh_output_controls

    def refresh_input_controls():
        for input_control in getattr(control_panel, "input_controls", []):
            input_control.refresh()

    control_panel.refresh_input_controls = refresh_input_controls

    def refresh_group_controls():
        for group_control in getattr(control_panel, "group_controls", []):
            group_control.refresh()

    control_panel.refresh_group_controls = refresh_group_controls

    def refresh_power_controls():
        for power_control in getattr(control_panel, "power_controls", []):
            power_control.refresh()

    control_panel.refresh_power_controls = refresh_power_controls

    build_io_controls(preset_file)

    return control_panel
