import os
import json
import csv
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from PIL import Image, ImageTk
import pandas as pd
import torch
import time

# Function to load and filter Aphia data
def load_aphia_data(csv_path):
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=['AphiaID'])
    return df.groupby('model_18_21May.pth')['AphiaID'].apply(list).to_dict()

# Class for the COCO Annotator GUI
class COCOAnnotator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.aphia_data = load_aphia_data('current_trainingsetclasses - Sheet1.csv')
        self.title("COCO Metadata Annotator")
        self.fixed_values = {}
        self.output_name = ""
        self.current_image_index = 0
        self.labeled_images_count = 0
        self.selected_classes = set()
        self.device = self.get_device()

        self.image_fields = {
            "location": "", "latitude": "", "longitude": "",
            "datetime": "", "species": "", "genus": "",
            "aphiaID": "", "life stage or biotype": "",
            "shape": "", "partial": "", "what the partial part is": "",
            "person classifying": "", "uncertain about class": "",
            "predicted_label": "", "taxonomist": "fixed",
            "institute": "fixed", "survey": "fixed"
        }

        self.entries = {}
        self.checkboxes = {}
        self.image_directory = os.path.join(os.getcwd(), "example_images_folder")
        self.labels_directory = os.path.join(os.getcwd(), "example_images_folder")
        self.data = {"images": [], "image_fields": self.image_fields}

        self.setup_ui()
        self.load_labels()
        self.load_images()
        self.display_current_image()

    def get_device(self):
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def load_labels(self):
        with open("labels.json", 'r') as json_file:
            data = json.load(json_file)
            labels_dict = data.get('labels', {})
            self.LABELS = {int(num): name for num, name in labels_dict.items()}

    def setup_ui(self):
        self.select_labels_dir_button = tk.Button(self, text="1: Provide save output directory for labels", command=self.select_labels_directory)
        self.select_labels_dir_button.grid(row=2, column=0, columnspan=2, pady=5, sticky="ew")

        self.select_dir_button = tk.Button(self, text="2: Provide input images directory", command=self.select_image_directory)
        self.select_dir_button.grid(row=3, column=0, columnspan=2, pady=5, sticky="ew")

        self.import_config_button = tk.Button(self, text="Optional: Import custom labeling standard", command=self.import_config)
        self.import_config_button.grid(row=4, column=0, columnspan=2, pady=5, sticky="ew")

        self.process_all_button = tk.Button(self, text="Optional: Process All", command=self.process_all_images)
        self.process_all_button.grid(row=5, column=0, columnspan=2, pady=5, sticky="ew")

        self.main_frame = tk.Frame(self)
        self.main_frame.grid(row=6, column=0, columnspan=2, sticky="nsew")

        self.canvas = tk.Canvas(self.main_frame, width=500, height=500)
        self.canvas.grid(row=0, column=0, padx=5, pady=5)

        self.fields_frame = tk.Frame(self.main_frame)
        self.fields_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ns")

        self.next_button = tk.Button(self, text="Next Image", command=self.save_fields_and_next_image)
        self.next_button.grid(row=7, column=0, columnspan=2, pady=5, sticky="ew")

        self.bind_keys()

    def bind_keys(self):
        for i in range(1, 10):
            self.bind(f"<Alt-Key-{i}>", self.focus_nth_entry)
        self.bind("<Control-n>", lambda event: self.save_fields_and_next_image())
        self.bind("<Control-s>", self.save_data)

    def focus_nth_entry(self, event):
        try:
            n = int(event.char)
            if n <= len(self.entries):
                entry = list(self.entries.values())[n - 1]
                entry.focus_set()
        except (ValueError, IndexError):
            pass

    def select_labels_directory(self):
        self.labels_directory = filedialog.askdirectory()
        if self.labels_directory:
            self.output_name = simpledialog.askstring("Output Name", "Name your outputs (without extension):")
            if self.output_name:
                messagebox.showinfo("Selected Directory and Output Name", f"Directory: {self.labels_directory}\nOutput Name: {self.output_name}")

    def select_image_directory(self):
        self.image_directory = filedialog.askdirectory()
        if self.image_directory:
            messagebox.showinfo("Selected Directory", self.image_directory)
            self.load_images()
            self.display_current_image()

    def load_images(self):
        self.images = load_images_from_directory(self.image_directory)

    def display_current_image(self):
        if self.images:
            image_path = self.images[self.current_image_index]
            self.show_image(image_path)
            self.populate_fields(image_path)
        else:
            print("No images found to display")

    def show_image(self, image_path):
        image = Image.open(image_path)
        image.thumbnail((500, 500))
        self.photo = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)


    def populate_fields(self, image_path):
        for widget in self.fields_frame.winfo_children():
            widget.destroy()

        folder_name = os.path.basename(os.path.dirname(image_path))
        tk.Label(self.fields_frame, text="Folder Name:").grid(row=0, column=0)
        self.folder_name_entry = tk.Entry(self.fields_frame)
        self.folder_name_entry.grid(row=0, column=1)
        self.folder_name_entry.insert(0, folder_name)

        self.entries = {}
        self.checkboxes = {}
        
        row = 1
        for field, default_value in self.image_fields.items():
            tk.Label(self.fields_frame, text=f"{field}:").grid(row=row, column=0)

            if field == "aphiaID":
                self.create_aphiaID_field(row)
            else:
                self.create_standard_field(field, default_value, row)

                # Set the entry value if it's a fixed field
                if default_value == "fixed" and field in self.fixed_values:
                    self.entries[field].insert(0, self.fixed_values[field])

            row += 1



    def create_aphiaID_field(self, row):
        tk.Label(self.fields_frame, text="Select or Enter aphiaID:").grid(row=row, column=0)
        self.aphiaID_var = tk.StringVar(self)
        self.aphiaID_var.set("")
        
        self.aphiaID_menu = tk.OptionMenu(self.fields_frame, self.aphiaID_var, *[""])
        self.aphiaID_menu.grid(row=row, column=2)

        self.custom_aphiaID_entry = tk.Entry(self.fields_frame)
        self.custom_aphiaID_entry.grid(row=row, column=1)

        self.entries["aphiaID"] = (self.aphiaID_var, self.custom_aphiaID_entry)

    def create_standard_field(self, field, default_value, row):
        entry = tk.Entry(self.fields_frame)
        entry.grid(row=row, column=1)
        self.entries[field] = entry

        if default_value == "fixed":
            checkbox_var = tk.BooleanVar()
            checkbox = tk.Checkbutton(self.fields_frame, variable=checkbox_var)
            checkbox.grid(row=row, column=2)
            checkbox_var.set(field in self.fixed_values)  
            self.checkboxes[field] = checkbox_var

    def save_fields_and_next_image(self):
        if self.images:
            image_path = self.images[self.current_image_index]
            self.save_image_data(image_path)

            self.current_image_index += 1
            if self.current_image_index < len(self.images):
                self.display_current_image()
            else:
                messagebox.showinfo("Completed", "All images have been processed.")
                save_to_files(self.data, self.labels_directory, self.output_name)
                
    def import_config(self):
        config_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if config_path:
            with open(config_path, 'r') as config_file:
                config = json.load(config_file)
                self.image_fields = config.get("image_fields", self.image_fields)
                messagebox.showinfo("Config Imported", f"Configuration imported from {config_path}")
                if self.images:
                    self.display_current_image()
                

    def save_image_data(self, image_path):
        selected_aphiaID = self.aphiaID_var.get()
        custom_aphiaID = self.custom_aphiaID_entry.get().strip()
        aphiaID = custom_aphiaID if custom_aphiaID else selected_aphiaID

        image_data = {field: self.get_field_value(field, aphiaID) for field in self.image_fields}
        image_data["file_name"] = os.path.basename(image_path)
        image_data["folder_name"] = self.folder_name_entry.get()

        for field, checkbox_var in self.checkboxes.items():
            if checkbox_var.get():
                self.fixed_values[field] = self.entries[field].get()
        
        self.data["images"].append(image_data)
        self.labeled_images_count += 1

        if self.labeled_images_count % 5 == 0:
            self.save_data()

    def get_field_value(self, field, aphiaID):
        if field == "aphiaID":
            return aphiaID
        return self.entries[field].get()

    def save_data(self):
        with open(os.path.join(self.labels_directory, f"{self.output_name}.json"), 'w') as json_file:
            json.dump(self.data, json_file)

    def process_all_images(self):
        for image_path in self.images:
            self.save_image_data(image_path)

# Function to load images from the directory
def load_images_from_directory(directory):
    return [os.path.join(directory, filename) for filename in os.listdir(directory) if filename.lower().endswith(('.png', '.PNG', '.jpg', '.JPG', '.jpeg', '.JPEG', '.bmp', '.BMP', '.gif', '.GIF',        '.tiff', '.TIFF', '.tif', '.TIF', '.ico', '.ICO', '.webp', '.WEBP', '.svg', '.SVG', '.heic', '.HEIC', '.heif', '.HEIF', '.jfif', '.JFIF', '.pjpeg', '.PJPEG', '.pjp', '.PJP', '.avif', '.AVIF'))]



if __name__ == "__main__":
    COCOAnnotator().mainloop()
