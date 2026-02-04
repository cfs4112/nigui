import tkinter as tk
from tkinter import ttk
from tabs.utilities_tab import setup_utilities_tab

root = tk.Tk()
root.title("Control Panel")
root.geometry("600x400")

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=10, pady=10)

control_panel = ttk.Frame(notebook)
notebook.add(control_panel, text="Control Panel")

utilities = ttk.Frame(notebook)
notebook.add(utilities, text="Utilities")
setup_utilities_tab(utilities, notebook)

root.mainloop()