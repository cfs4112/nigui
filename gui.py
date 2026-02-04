import tkinter as tk
from tkinter import ttk
from tabs.utilities_tab import setup_settings_frame

root = tk.Tk()
root.title("Control Panel")
root.geometry("600x400")

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=10, pady=10)

control_panel = ttk.Frame(notebook)
notebook.add(control_panel, text="Control Panel")

settings_frame = ttk.Frame(root)
setup_settings_frame(settings_frame, root, notebook)

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