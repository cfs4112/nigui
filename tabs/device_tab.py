from tkinter import ttk
import tkinter as tk

BUTTON_PADX = 15
ON_COLOR  = "#4CAF50"   # green
OFF_COLOR = "#cac9c8"   # default bg
UTIL_COLOR = "#B0BEC5"   # muted gray


def create_device_tab(notebook, dev, state_manager):
    states = state_manager.state.get(dev, {})
    buttons = {}
    button_vars = {}  # Store IntVars to revert checkbutton states
    button_frames = {}  # Store frames around checkbuttons for styling
    diagram_labels = {}
    diagram_window = None
    staged_changes = {}  # Track changes not yet written
    dev_tab = ttk.Frame(notebook)
    notebook.add(dev_tab, text=dev)

    # Frame around buttons
    signals_frame = ttk.LabelFrame(dev_tab, text="Digital Signals", padding=(5, 2))
    signals_frame.pack(padx=15, pady=20, anchor="w")
    
    # Get the default background color for frames (cross-platform)
    default_bg = tk.Frame(signals_frame).cget('background')

    # No dynamic spacing to keep compact

    def update_diagram_colors():
        """Update all diagram label colors based on current states"""
        for key, label in diagram_labels.items():
            state = states.get(key, False)
            label.configure(bg=ON_COLOR if state else OFF_COLOR)

    def toggle_signal(port, bit, var):
        """Stage a signal change with visual indication"""
        key = f"p{port}.{bit}"
        new_state = bool(var.get())
        
        # Stage the change
        staged_changes[key] = new_state
        
        # Change outline color to indicate pending change
        if key in button_frames:
            button_frames[key].configure(highlightbackground="blue", highlightcolor="blue")
    
    def write_ports():
        """Write all staged changes to state manager and update displays"""
        for key, new_state in staged_changes.items():
            states[key] = new_state
            state_manager.set_pin_state(dev, key, new_state)
            
            # Reset outline to default background
            if key in button_frames:
                button_frames[key].configure(highlightbackground=default_bg)
        
        # Clear staged changes
        staged_changes.clear()
        
        # Update diagram
        update_diagram_colors()
    
    def revert_changes():
        """Revert all staged changes back to their original states"""
        for key in list(staged_changes.keys()):
            # Reset checkbutton to match actual state
            if key in button_vars:
                original_state = states.get(key, False)
                button_vars[key].set(1 if original_state else 0)
            
            # Remove blue outline
            if key in button_frames:
                button_frames[key].configure(highlightbackground=default_bg)
        
        # Clear staged changes
        staged_changes.clear()

    for port in range(3):
        for bit in range(8):
            key = f"p{port}.{bit}"
            state = states.get(key, False)
            label = ttk.Label(signals_frame, text=key)
            label.grid(row=port*3, column=bit, padx=5, pady=(5,0), sticky="n")
            
            # Frame around checkbutton for styling - fixed size to prevent resizing
            chk_frame = tk.Frame(signals_frame, highlightthickness=2, highlightbackground=default_bg, width=25, height=25)
            chk_frame.grid(row=port*3+1, column=bit, padx=BUTTON_PADX, pady=(0,0))
            chk_frame.grid_propagate(False)  # Maintain fixed size
            button_frames[key] = chk_frame
            
            var = tk.IntVar(value=1 if state else 0)
            button_vars[key] = var
            chk = ttk.Checkbutton(chk_frame, variable=var, command=lambda p=port, b=bit, v=var: toggle_signal(p, b, v), takefocus=0)
            chk.place(relx=0.5, rely=0.5, anchor="center")  # Center horizontally and vertically
            
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

            lbl_left.grid(row=row+1, column=0, padx=2, pady=2)

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

            lbl_right.grid(row=row+1, column=2, padx=2, pady=2)

    # Buttons frame
    buttons_frame = ttk.Frame(dev_tab)
    buttons_frame.pack(padx=15, pady=(0, 10), anchor="w")
    
    # Write Ports button
    write_button = ttk.Button(buttons_frame, text="Write Ports", command=write_ports, style="Accent.TButton")
    write_button.pack(side="left", padx=(0, 10))
    
    # Revert button
    revert_button = ttk.Button(buttons_frame, text="Revert Changes", command=revert_changes)
    revert_button.pack(side="left", padx=(0, 10))
    
    # Device diagram button
    diagram_button = ttk.Button(buttons_frame, text="Open Device Diagram", command=open_diagram_window)
    diagram_button.pack(side="left")


