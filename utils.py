import tkinter as tk
from tkinter import messagebox
import xml.etree.ElementTree as ET


def load_file(file_path):
    """Load file content with error handling in a friendly manner."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        messagebox.showerror("Oops!", f"Sorry, an error occurred while opening the file:\n{file_path}\nPlease check that the file exists and try again.\nError details: {e}")
        return ""


def save_file(file_path, content):
    """Save file content with error handling in a friendly manner."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        messagebox.showinfo("Success", f"Great! Your changes have been saved to:\n{file_path}")
        return True
    except Exception as e:
        messagebox.showerror("Oops!", f"We couldn't save the file:\n{file_path}\nPlease check your permissions or filepath.\nError details: {e}")
        return False


def load_xml(file_path):
    """Load and parse XML file with error handling in a friendly manner."""
    try:
        tree = ET.parse(file_path)
        return tree, tree.getroot()
    except Exception as e:
        messagebox.showerror("XML Error", f"Oops, we couldn't parse the XML file:\n{file_path}\nPlease check the file format.\nError details: {e}")
        return None, None


def validate_xml(file_path):
    """Check if an XML file is well-formed in a user friendly way."""
    try:
        ET.parse(file_path)
        messagebox.showinfo("XML Valid", f"Great, the XML file is well-formed:\n{file_path}")
    except Exception as e:
        messagebox.showerror("XML Error", f"Oops, there is an error in the XML file:\n{file_path}\nDetails: {e}")


def load_mod_info(mod_file):
    """Load mod information from an XML file in a friendly manner."""
    try:
        tree = ET.parse(mod_file)
        root = tree.getroot()
        mod_info = "Here is the mod information from the file:\n\n"
        for attr, value in root.attrib.items():
            mod_info += f"{attr}: {value}\n"
        if list(root):
            mod_info += "\nDetails:\n"
            for child in root:
                mod_info += f"{child.tag}: {child.text}\n"
        return mod_info
    except Exception as e:
        return f"Oops, failed to load mod info.\nError details: {e}" 