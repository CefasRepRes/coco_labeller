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


class BlobApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Blob File Loader")
        self.root.geometry("800x600")
        self.temp_dir = os.path.join(tempfile.gettempdir(), "BlobAppTemp")
        self.clone_dir = os.path.join(self.temp_dir, "cyz2json")
        os.makedirs(self.temp_dir, exist_ok=True)

        self.species_dict = {
            'a': 'Small or nothing visible',
            'b': 'Other',
            'c': 'Chaetoceros',
            'd': 'Detritus',
            'x': 'NA'
        }

        self.output_dir = ""
        self.json_file = os.path.join(self.temp_dir, "tempfile.json")
        self.csv_file = None
        self.image_label = None
        self.tif_files = []
        self.current_image_index = 0
        self.metadata = {}

        self.create_widgets()

        self.root.bind('<Shift-A>', self.set_species_a)
        self.root.bind('<Shift-B>', self.set_species_b)
        self.root.bind('<Shift-C>', self.set_species_c)
        self.root.bind('<Shift-D>', self.set_species_d)
        self.root.bind('<Shift-X>', self.set_species_x)
        self.root.bind('<Shift-space>', self.next_image)

        functions.clear_temp_folder(self.temp_dir)

    def create_widgets(self):
        self.compile_button = tk.Button(self.root, text="Download and compile cyz2json tool (required)", 
                                        command=lambda: functions.compile_cyz2json(self.clone_dir, self.path_entry))
        self.compile_button.pack(pady=10)

        self.path_label = tk.Label(self.root, text="Path to cyz2json Installation:")
        self.path_label.pack(pady=5)

        self.path_entry = tk.Entry(self.root, width=100)
        self.path_entry.insert(0, self.clone_dir + "\\bin\\Cyz2Json.dll")
        self.path_entry.pack(pady=5)

        self.url_label = tk.Label(self.root, text="Blob File URL:")
        self.url_label.pack(pady=5)
        self.url_entry = tk.Entry(self.root, width=100)
        self.url_entry.insert(0, "https://citprodflowcytosa.blob.core.windows.net/public/ThamesSTN6MA4_9%202023-10-16%2011h24.cyz")
        self.url_entry.pack(pady=5)
        self.download_button = tk.Button(self.root, text="Download", command=lambda: functions.download_file(self.url_entry, self.temp_dir, self.load_entry))
        self.download_button.pack(pady=10)

        self.load_label = tk.Label(self.root, text="Load File Path:")
        self.load_label.pack(pady=5)
        self.load_entry = tk.Entry(self.root, width=100)
        self.load_entry.insert(0, "C:/Users/JR13/Downloads/ThamesSTN6MA4_9%202023-10-16%2011h24.cyz")
        self.load_entry.pack(pady=5)

        self.load_button = tk.Button(self.root, text="Convert to json", command=lambda: functions.load_file(self.path_entry.get(), self.load_entry.get(), self.json_file))
        self.load_button.pack(pady=10)

        self.output_dir_button = tk.Button(self.root, text="Select Output Directory", command=lambda: functions.select_output_dir(self))
        self.output_dir_button.pack(pady=10)

        self.process_button = tk.Button(self.root, text="Extract images and associated data", command=self.process_file)
        self.process_button.pack(pady=10)

        self.prev_button = tk.Button(self.root, text="Previous", command=self.prev_image, state=tk.DISABLED)
        self.next_button = tk.Button(self.root, text="Next", command=self.next_image, state=tk.DISABLED)
        self.prev_button.pack(side=tk.LEFT, padx=20)
        self.next_button.pack(side=tk.RIGHT, padx=20)

        self.biological_label = tk.Label(self.root, text="Biological (Y/N):")
        self.biological_label.pack(pady=5)
        self.biological_entry = tk.Entry(self.root, width=10)
        self.biological_entry.pack(pady=5)

        self.species_label = tk.Label(self.root, text="Suspected Species:")
        self.species_label.pack(pady=5)
        self.species_entry = tk.Entry(self.root, width=100)
        self.species_entry.pack(pady=5)

    def set_species_a(self, event):
        self.species_entry.delete(0, tk.END)
        self.species_entry.insert(0, self.species_dict['a'])

    def set_species_b(self, event):
        self.species_entry.delete(0, tk.END)
        self.species_entry.insert(0, self.species_dict['b'])

    def set_species_c(self, event):
        self.species_entry.delete(0, tk.END)
        self.species_entry.insert(0, self.species_dict['c'])

    def set_species_d(self, event):
        self.species_entry.delete(0, tk.END)
        self.species_entry.insert(0, self.species_dict['d'])

    def set_species_x(self, event):
        self.species_entry.delete(0, tk.END)
        self.species_entry.insert(0, self.species_dict['x'])

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
                                self.tif_files, self.metadata, self.biological_entry, self.species_entry)
        functions.update_navigation_buttons(self.prev_button, self.next_button, 
                                            self.current_image_index, len(self.tif_files))

    def next_image(self, event=None):
        if self.current_image_index < len(self.tif_files) - 1:
            functions.save_metadata(self.current_image_index, self.tif_files, self.metadata, 
                                    self.biological_entry, self.species_entry, self.output_dir)
            self.current_image_index += 1
            functions.display_image(self, self.root, self.current_image_index, self.output_dir, self.image_label, 
                                    self.tif_files, self.metadata, self.biological_entry, self.species_entry)
            functions.update_navigation_buttons(self.prev_button, self.next_button, 
                                                self.current_image_index, len(self.tif_files))

    def prev_image(self):
        if self.current_image_index > 0:
            functions.save_metadata(self.current_image_index, self.tif_files, self.metadata, 
                                    self.biological_entry, self.species_entry, self.output_dir)
            self.current_image_index -= 1
            functions.display_image(self, self.root, self.current_image_index, self.output_dir, self.image_label, 
                                    self.tif_files, self.metadata, self.biological_entry, self.species_entry)
            functions.update_navigation_buttons(self.prev_button, self.next_button, 
                                                self.current_image_index, len(self.tif_files))

if __name__ == "__main__":
    root = tk.Tk()
    app = BlobApp(root)
    root.mainloop()
