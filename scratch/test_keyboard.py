"""Simple test to verify VirtualKeyboard works."""
import sys
sys.path.insert(0, "d:/1/Ahmed/projects/mariam_pro/AI")

import customtkinter as ctk
import tkinter as tk
from gui.widgets.keyboard import VirtualKeyboard

app = ctk.CTk()
app.geometry("800x600")
app.title("Keyboard Test")

# Main frame
main_frame = ctk.CTkFrame(app)
main_frame.pack(fill="both", expand=True)

# Content area
label = ctk.CTkLabel(main_frame, text="Click on the entry below to show keyboard:")
label.pack(pady=10)

entry1 = ctk.CTkEntry(main_frame, placeholder_text="Type here...")
entry1.pack(pady=10, padx=20, fill="x")

entry2 = ctk.CTkEntry(main_frame, placeholder_text="Another field...")
entry2.pack(pady=10, padx=20, fill="x")

# Create keyboard (parent is main_frame)
keyboard = VirtualKeyboard(main_frame)

def find_input(widget):
    if isinstance(widget, (ctk.CTkEntry, ctk.CTkTextbox)):
        return widget
    if isinstance(widget, (tk.Entry, tk.Text)):
        if hasattr(widget, 'master') and isinstance(widget.master, (ctk.CTkEntry, ctk.CTkTextbox)):
            return widget.master
    parent = widget
    for _ in range(5):
        parent = parent.master if hasattr(parent, 'master') else None
        if parent is None:
            break
        if isinstance(parent, (ctk.CTkEntry, ctk.CTkTextbox)):
            return parent
    return None

def on_click(event):
    clicked = event.widget
    
    # Skip if clicking keyboard itself
    w = clicked
    while w:
        if w == keyboard:
            return
        w = w.master if hasattr(w, 'master') else None
    
    input_w = find_input(clicked)
    if input_w:
        print(f"Opening keyboard for: {input_w}")
        app.after(150, lambda: keyboard.show(input_w))
    else:
        if keyboard.is_visible:
            print("Hiding keyboard")
            keyboard.hide()

app.bind_all("<Button-1>", on_click)

app.mainloop()
