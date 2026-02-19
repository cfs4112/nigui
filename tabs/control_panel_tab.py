import json
import os
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

        self.status = None
        if self.secondary_label:
            self.columnconfigure(1, weight=0)
            self.status = tk.Label(self, width=10, relief="flat", padx=10, pady=6)
            self.status.grid(row=0, column=1, sticky="nsew")

        self.refresh()

    def _status_text(self, is_on):
        if self.secondary_label:
            return self.secondary_label.get("on") if is_on else self.secondary_label.get("off")
        return "ON" if is_on else "OFF"

    def refresh(self):
        is_on = bool(self.state_manager.get_pin_state(self.device, self.pin))
        if self.status is not None:
            self.status.configure(text=self._status_text(is_on))
            if self.on_color is not None and self.off_color is not None:
                self.status.configure(bg=self.on_color if is_on else self.off_color)
        else:
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

    info = None
    if preset_info:
        info = ttk.Label(
            control_panel,
            text=preset_info
        )
        info.pack(anchor="w", padx=10, pady=(0, 10))
    else:
        preset_label.pack_configure(pady=(10, 2))

    def update_preset_info(new_info):
        nonlocal info
        if new_info:
            if info is None:
                info = ttk.Label(control_panel, text=new_info)
                info.pack(anchor="w", padx=10, pady=(0, 10))
            else:
                info.configure(text=new_info)
            preset_label.pack_configure(pady=(10, 5))
        else:
            if info is not None:
                info.destroy()
                info = None
            preset_label.pack_configure(pady=(10, 2))

    control_panel.update_preset_info = update_preset_info

    def create_outputs_section():
        existing = getattr(control_panel, "outputs_section", None)
        if existing is not None and existing.winfo_exists():
            existing.destroy()
        section = ttk.LabelFrame(control_panel, text="Outputs", padding=(6, 4))
        section.pack(side="left", fill="y", expand=False, anchor="n", padx=6, pady=(0, 6))
        section.pack_propagate(True)
        control_panel.outputs_section = section
        return section

    outputs_section = create_outputs_section()

    def build_output_controls(preset_path):
        output_controls = []
        section = control_panel.outputs_section
        for child in section.winfo_children():
            child.destroy()

        configured_devices = set()
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                cfg = json.load(f) or {}
            configured_devices = set(cfg.get("devices", []))

        preset = load_preset_file(preset_path)
        layout = preset.get("layout", {})
        controls = layout.get("controls", [])

        for control in controls:
            if control.get("type", "").lower() != "output":
                continue
            output_widget = OutputControl(
                section,
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

        control_panel.output_controls = output_controls

    def rebuild_from_preset(preset_path):
        create_outputs_section()
        build_output_controls(preset_path)

    control_panel.rebuild_from_preset = rebuild_from_preset

    def refresh_output_controls():
        for output_control in getattr(control_panel, "output_controls", []):
            output_control.refresh()

    control_panel.refresh_output_controls = refresh_output_controls

    build_output_controls(preset_file)

    return control_panel
