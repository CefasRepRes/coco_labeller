import tempfile
import requests
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import csv
import os
import pandas as pd
import functions
from tkinter import ttk
import numpy as np
import plotly

class BlobApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Blob File Loader")
        self.root.geometry("800x600")
        self.temp_dir = os.path.join(tempfile.gettempdir(), "BlobAppTemp")
        self.clone_dir = os.path.join(self.temp_dir, "cyz2json")
        self.r_dir = os.path.join(self.temp_dir, "")
        os.makedirs(self.temp_dir, exist_ok=True)

        self.species_dict = {
            'z': 'Small or nothing present',
            'x': 'Detritus',
            'c': 'Not clear or not sure of species',
            'v': 'Other species or type of object',
            'b': 'Multiple objects or single object that seems to have been broken up',
            'a': 'Chaetoceros',
            's': 'Rhizosolenia',
            'd': 'Leptocylindrus',
            'f': 'Melosira'
        }

        self.output_dir = ""
        self.json_file = os.path.join(self.temp_dir, "tempfile.json")
        self.listmode_file = os.path.join(self.temp_dir, "tempfile.csv")
        self.inferences_file = os.path.join(self.temp_dir, "predictions.csv")
        self.csv_file = None
        self.image_label = None
        self.tif_files = []
        self.current_image_index = 0
        self.metadata = {}


        self.create_widgets()

        for key in self.species_dict.keys():
            self.root.bind(f'<Shift-{key.upper()}>', self.set_species)
        
        self.root.bind('<plus>', self.increase_confidence)
        self.root.bind('<minus>', self.decrease_confidence)
        self.root.bind('<Shift-space>', self.next_image)
        
        functions.clear_temp_folder(self.temp_dir)


    def create_widgets(self):
        # Frame for image and navigation buttons
        image_frame = tk.Frame(self.root)
        image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Key bindings table on the right side
        table_frame = tk.Frame(self.root)
        table_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        
        key_table_label = tk.Label(table_frame, text="Key Bindings:")
        key_table_label.pack(pady=5)
        
        key_table = ttk.Treeview(table_frame, columns=("Key", "Description"), show="headings", height=8)
        key_table.heading("Key", text="Key")
        key_table.heading("Description", text="Description")
        key_table.column("Key", anchor="center", width=80)
        key_table.column("Description", anchor="w", width=400)
        key_table.pack(pady=5)
        
        for key, description in self.species_dict.items():
            key_table.insert("", "end", values=(f"Shift+{key.upper()}", description))
        
        # Buttons and other inputs on the left (image frame)
        self.compile_button = tk.Button(image_frame, text="Download and compile cyz2json tool (required)", 
                                        command=lambda: functions.compile_cyz2json(self.clone_dir, self.path_entry))
        self.compile_button.pack(pady=10)
        
        self.path_label = tk.Label(image_frame, text="Path to cyz2json Installation:")
        self.path_label.pack(pady=5)


        
        self.path_entry = tk.Entry(image_frame, width=100)
        self.path_entry.insert(0, self.clone_dir + "\\bin\\Cyz2Json.dll")
        self.path_entry.pack(pady=5)


        # r stuff
        self.rcompile_button = tk.Button(image_frame, text="Download r requirements", 
                                        command=lambda: functions.compile_r_requirements(self.r_dir, self.rpath_entry))
        self.rcompile_button.pack(pady=10)
        
        self.rpath_label = tk.Label(image_frame, text="Path to r Installation:")
        self.rpath_label.pack(pady=5)
        
        self.rpath_entry = tk.Entry(image_frame, width=100)
        self.rpath_entry.insert(0, self.r_dir + "./R-4.3.3/bin/Rscript.exe")
        self.rpath_entry.pack(pady=5)

        
        self.url_label = tk.Label(image_frame, text="Blob File URL:")
        self.url_label.pack(pady=5)
        self.url_entry = tk.Entry(image_frame, width=100)
        self.url_entry.insert(0, "https://citprodflowcytosa.blob.core.windows.net/public/ThamesSTN6MA4_9%202023-10-16%2011h24.cyz")
        self.url_entry.pack(pady=5)
        
        self.download_button = tk.Button(image_frame, text="Download", command=lambda: functions.download_file(self.url_entry, self.temp_dir, self.load_entry))
        self.download_button.pack(pady=10)
        
        self.load_label = tk.Label(image_frame, text="Load File Path:")
        self.load_label.pack(pady=5)
        self.load_entry = tk.Entry(image_frame, width=100)
        self.load_entry.insert(0, "C:/Users/JR13/Downloads/ThamesSTN6MA4_9%202023-10-16%2011h24.cyz")
        self.load_entry.pack(pady=5)
        
        
        self.load_button = tk.Button(image_frame, text="Convert to json", command=lambda: functions.load_file(self.path_entry.get(), self.load_entry.get(), self.json_file))
        self.load_button.pack(pady=10)

        self.listmode_button = tk.Button(image_frame, text="Convert to listmode csv", command=lambda: functions.to_listmode(self.json_file, self.listmode_file))
        self.listmode_button.pack(pady=10)
                
        self.infer_button = tk.Button(image_frame, text="Apply r inference to listmode csv", command=lambda: functions.apply_r(self.listmode_file, self.inferences_file, self.rpath_entry.get()))
        self.infer_button.pack(pady=10)
                
        self.plot_button = tk.Button(image_frame, text="Make 3d plot", command=lambda: functions.plot3d(self.inferences_file))
        self.plot_button.pack(pady=10)
                
        self.output_dir_button = tk.Button(image_frame, text="Select Output Directory", command=lambda: functions.select_output_dir(self))
        self.output_dir_button.pack(pady=10)
                
        self.prev_button = tk.Button(image_frame, text="Previous", command=self.prev_image, state=tk.DISABLED)
        self.next_button = tk.Button(image_frame, text="Next", command=self.next_image, state=tk.DISABLED)
        self.prev_button.pack(side=tk.LEFT, padx=20)
        self.next_button.pack(side=tk.RIGHT, padx=20)
        
        self.confidence_label = tk.Label(image_frame, text="Optional: Assign a confidence to your label with + -")
        self.confidence_label.pack(pady=5)
        self.confidence_entry = tk.Entry(image_frame, width=10)
        self.confidence_entry.pack(pady=5)
        
        self.species_label = tk.Label(image_frame, text="Suspected Species:")
        self.species_label.pack(pady=5)
        self.species_entry = tk.Entry(image_frame, width=100)
        self.species_entry.pack(pady=5)

    
    
    def set_species(self, event):
        key_pressed = event.keysym.lower()
        if key_pressed in self.species_dict:
            self.species_entry.delete(0, tk.END)
            self.species_entry.insert(0, self.species_dict[key_pressed])


    def increase_confidence(self, event):
        current_value = self.confidence_entry.get()
        try:
            new_value = int(current_value) + 1
        except ValueError:
            new_value = 1
        self.confidence_entry.delete(0, tk.END)
        self.confidence_entry.insert(0, str(new_value))

    def decrease_confidence(self, event):
        current_value = self.confidence_entry.get()
        try:
            new_value = int(current_value) - 1
        except ValueError:
            new_value = -1  # Set a default value if invalid
        self.confidence_entry.delete(0, tk.END)
        self.confidence_entry.insert(0, str(new_value))


    def process_file(self):
        if not self.output_dir:
            messagebox.showerror("Output Directory Not Set", "Please select an output directory.")
            return
        self.csv_file = os.path.join(self.output_dir, "particles_data.csv")
        try:
            subprocess.run(["python", "./listmode.py", self.json_file, '--output', self.csv_file, self.output_dir, self.output_dir], check=True)
            particles_with_images = pd.read_csv(self.csv_file)['id'].tolist()
            json_data = functions.load_json(self.json_file)
            selected_particles = functions.select_particles(json_data, particle_ids=particles_with_images)
            pulses = functions.get_pulses(selected_particles)
            pulsesdf = pd.DataFrame.from_dict(pulses, orient='index').reset_index(drop=True)
            csv_df = pd.read_csv(self.csv_file).reset_index(drop=True)
            pulsesdf = pd.concat([pulsesdf, csv_df], axis=1)
            pulsesdf['filename'] = self.load_entry.get()
            pulsesdf.to_csv(self.csv_file, index=False)
            messagebox.showinfo("Success", f"Files processed successfully. Output in: {self.csv_file}")
            self.show_images()
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Processing Error", f"Failed to process file: {e}")

    def show_images(self):
        self.tif_files = [f for f in os.listdir(self.output_dir) if f.endswith('.tif')]
        if not self.tif_files:
            messagebox.showinfo("No Images", "No .tif files found in the directory!")
            return
        self.current_image_index = 0
        functions.display_image(self, self.root, self.current_image_index, self.output_dir, self.image_label, 
                                self.tif_files, self.metadata, self.confidence_entry, self.species_entry)
        functions.update_navigation_buttons(self.prev_button, self.next_button, 
                                            self.current_image_index, len(self.tif_files))

    def next_image(self, event=None):
        if self.current_image_index < len(self.tif_files) - 1:
            functions.save_metadata(self.current_image_index, self.tif_files, self.metadata, 
                                    self.confidence_entry, self.species_entry, self.output_dir)
            self.current_image_index += 1
            functions.display_image(self, self.root, self.current_image_index, self.output_dir, self.image_label, 
                                    self.tif_files, self.metadata, self.confidence_entry, self.species_entry)
            functions.update_navigation_buttons(self.prev_button, self.next_button, 
                                                self.current_image_index, len(self.tif_files))

    def prev_image(self):
        if self.current_image_index > 0:
            functions.save_metadata(self.current_image_index, self.tif_files, self.metadata, 
                                    self.confidence_entry, self.species_entry, self.output_dir)
            self.current_image_index -= 1
            functions.display_image(self, self.root, self.current_image_index, self.output_dir, self.image_label, 
                                    self.tif_files, self.metadata, self.confidence_entry, self.species_entry)
            functions.update_navigation_buttons(self.prev_button, self.next_button, 
                                                self.current_image_index, len(self.tif_files))

if __name__ == "__main__":
    root = tk.Tk()
    app = BlobApp(root)
    root.mainloop()
