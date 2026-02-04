from tkinter import ttk

def create_device_tab(notebook, dev):
    dev_tab = ttk.Frame(notebook)
    notebook.add(dev_tab, text=dev)
    ttk.Label(dev_tab, text=f"Controls for {dev}").pack(pady=20)
    # Add more controls here if needed