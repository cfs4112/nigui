from tkinter import ttk
import tkinter as tk

BUTTON_PADX = 15
ON_COLOR  = "#4CAF50"   # green
OFF_COLOR = "#B0BEC5"   # muted gray


def create_device_tab(notebook, dev, state_manager):
    states = state_manager.state.get(dev, {})
    buttons = {}
    dev_tab = ttk.Frame(notebook)
    notebook.add(dev_tab, text=dev)

    # Frame around buttons
    signals_frame = ttk.LabelFrame(dev_tab, text="Digital Signals", padding=(5, 2))
    signals_frame.pack(padx=15, pady=20, anchor="w")

    # No dynamic spacing to keep compact

    def toggle_signal(port, bit, var):
        key = f"p{port}.{bit}"
        new_state = bool(var.get())
        states[key] = new_state
        state_manager.set_pin_state(dev, key, new_state)

    for port in range(3):
        for bit in range(8):
            key = f"p{port}.{bit}"
            state = states.get(key, False)
            label = ttk.Label(signals_frame, text=key)
            label.grid(row=port*3, column=bit, padx=5, pady=(5,0), sticky="n")
            var = tk.IntVar(value=1 if state else 0)
            chk = ttk.Checkbutton(signals_frame, variable=var, command=lambda p=port, b=bit, v=var: toggle_signal(p, b, v))
            chk.grid(row=port*3+1, column=bit, padx=BUTTON_PADX, pady=(0,0), sticky="n")
            status_label = ttk.Label(signals_frame, text="")
            status_label.grid(row=port*3+2, column=bit, padx=5, pady=(0,5), sticky="n")
            buttons[key] = chk

    # Device diagram

    pin_functions = { 1: "GND", 2: "+5V", 3: "p0.0", 4: "p0.1", 5: "p0.2", 6: "p0.3", 7: "GND", 8: "GND", 9: "p0.4", 10: "p0.5", 11: "p0.6", 12: "p0.7", 13: "p1.0", 14: "p1.1", 15: "p1.2", 16: "p1.3", 17: "p1.4", 18: "p1.5", 19: "p1.6", 20: "p1.7", 21: "p2.0", 22: "p2.1", 23: "p2.2", 24: "p2.3", 25: "GND", 26: "GND", 27: "p2.4", 28: "p2.5", 29: "p2.6", 30: "p2.7", 31: "+5V", 32: "GND" }

    diagram_frame = ttk.LabelFrame(dev_tab, text="Device Diagram", padding=(5,2))
    diagram_frame.pack(padx=15, pady=10, anchor="w")

    diagram_labels = {}

    for row in range(16):
        # ---------- Right rail (pins 1–16) ----------
        pin_right = 16 - row
        func_right = pin_functions.get(pin_right, "NC")

        lbl_right = tk.Label(
            diagram_frame,
            text=f"Pin {pin_right} : {func_right}",
            relief="sunken",
            width=12,
            justify="center"
        )

        if func_right.startswith("p"):
            state = states.get(func_right, False)
            lbl_right.configure(bg=ON_COLOR if state else OFF_COLOR)
            diagram_labels[func_right] = lbl_right

        lbl_right.grid(row=row, column=0, padx=2, pady=2)

        # ---------- Device body (center box) ----------
        if row == 4:
            body = tk.Label(
                diagram_frame,
                text="USB-6501\n24-line Digital I/O",
                relief="groove",
                width=22,
                height=6,
                justify="center",
                font=("TkDefaultFont", 9, "bold")
            )
            body.grid(row=row, column=1, rowspan=8, padx=10, pady=2)

        # ---------- Left rail (pins 17–32) ----------
        pin_left = 32 - row
        func_left = pin_functions.get(pin_left, "NC")

        lbl_left = tk.Label(
            diagram_frame,
            text=f"Pin {pin_left} : {func_left}",
            relief="sunken",
            width=12,
            justify="center"
        )

        if func_left.startswith("p"):
            state = states.get(func_left, False)
            lbl_left.configure(bg=ON_COLOR if state else OFF_COLOR)
            diagram_labels[func_left] = lbl_left

        lbl_left.grid(row=row, column=2, padx=2, pady=2)
