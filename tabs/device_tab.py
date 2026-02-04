from tkinter import ttk
import tkinter as tk

BUTTON_PADX = 15
ON_COLOR  = "#4CAF50"   # green
OFF_COLOR = "#cac9c8"   # default bg
UTIL_COLOR = "#B0BEC5"   # muted gray


def create_device_tab(notebook, dev, state_manager):
    states = state_manager.state.get(dev, {})
    buttons = {}
    diagram_labels = {}
    diagram_window = None
    dev_tab = ttk.Frame(notebook)
    notebook.add(dev_tab, text=dev)

    # Frame around buttons
    signals_frame = ttk.LabelFrame(dev_tab, text="Digital Signals", padding=(5, 2))
    signals_frame.pack(padx=15, pady=20, anchor="w")

    # No dynamic spacing to keep compact

    def update_diagram_colors():
        """Update all diagram label colors based on current states"""
        for key, label in diagram_labels.items():
            state = states.get(key, False)
            label.configure(bg=ON_COLOR if state else OFF_COLOR)

    def toggle_signal(port, bit, var):
        key = f"p{port}.{bit}"
        new_state = bool(var.get())
        states[key] = new_state
        state_manager.set_pin_state(dev, key, new_state)
        update_diagram_colors()

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

    def open_diagram_window():
        nonlocal diagram_window
        if diagram_window is not None and diagram_window.winfo_exists():
            diagram_window.lift()
            return
        
        diagram_window = tk.Toplevel(dev_tab)
        diagram_window.title(f"{dev} - Device Diagram")
        diagram_window.geometry("600x650")
        diagram_window.minsize(400, 500)
        
        create_diagram(diagram_window, pin_functions, states, diagram_labels)

    def create_diagram(parent, pin_functions, states, diagram_labels):
        """Create device diagram in given parent widget"""
        diagram_frame = ttk.Frame(parent, padding=(10,10))
        diagram_frame.pack(expand=True)

        # Device name header
        device_header = tk.Label(
            diagram_frame,
            text=f"Device: {dev}",
            font=("TkDefaultFont", 12, "bold"),
            pady=10
        )
        device_header.grid(row=0, column=0, columnspan=3, pady=(0, 10))

        # Device body (center box) - full height
        body = tk.Label(
            diagram_frame,
            text="USB-6501\n24-line Digital I/O",
            relief="groove",
            width=22,
            justify="center",
            font=("TkDefaultFont", 9, "bold")
        )
        body.grid(row=1, column=1, rowspan=16, padx=10, pady=2, sticky="ns")

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
            else:
                lbl_right.configure(bg=UTIL_COLOR)

            lbl_right.grid(row=row+1, column=0, padx=2, pady=2)

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
            else:
                lbl_left.configure(bg=UTIL_COLOR)

            lbl_left.grid(row=row+1, column=2, padx=2, pady=2)

    # Button to open diagram window
    diagram_button = ttk.Button(dev_tab, text="Open Device Diagram", command=open_diagram_window)
    diagram_button.pack(padx=15, pady=10, anchor="w")


