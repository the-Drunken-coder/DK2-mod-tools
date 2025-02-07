import tkinter as tk
from tkinter import ttk, messagebox
import os

# Path to the localization text file
FILE_PATH = os.path.join("Example mod", "Baby seals", "localization", "seals_squadname_pool.txt")

class LocalizationEditor(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.text_area = None
        self.build_ui()

    def build_ui(self):
        # Create a Text widget with a Scrollbar
        self.text_area = tk.Text(self, wrap="word")
        self.text_area.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar = ttk.Scrollbar(self, command=self.text_area.yview)
        scrollbar.pack(side="right", fill="y")
        self.text_area.config(yscrollcommand=scrollbar.set)
        
        # Load file content
        self.load_file()
        
        # Save Button
        btn_save = ttk.Button(self, text="Save Changes", command=self.save_changes)
        btn_save.pack(pady=10)

    def load_file(self):
        try:
            with open(FILE_PATH, "r", encoding="utf-8") as f:
                content = f.read()
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert("1.0", content)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")

    def save_changes(self):
        try:
            content = self.text_area.get("1.0", tk.END)
            with open(FILE_PATH, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Success", "File saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")


def get_plugin_tab(parent):
    container = ttk.Frame(parent)
    editor = LocalizationEditor(container)
    editor.pack(fill="both", expand=True)
    return "Localization", container 