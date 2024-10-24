import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import os
import json
from PIL import Image, ImageTk
import torch
from utils import resnet18, get_device, classify, save_to_files, load_images_from_directory, bind_keys, setup_ui
import time
import pandas as pd

def load_aphia_data(csv_path):
    df = pd.read_csv(csv_path)
    # Filter out rows with missing AphiaID
    df = df.dropna(subset=['AphiaID'])
    # Group by 'model_18_21May.pth' and 'class'
    aphia_data = df.groupby('model_18_21May.pth')['AphiaID'].apply(list).to_dict()
    return aphia_data
    
class COCOAnnotator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.aphia_data = load_aphia_data('current_trainingsetclasses - Sheet1.csv')  # Adjust path if necessary
        self.title("COCO Metadata Annotator")
        self.fixed_values = {}

        self.output_name = ""
        self.current_image_index = 0
        self.photo = None
        self.model = None
        self.labeled_images_count = 0


        self.aphiaID_options = [""]

        self.image_fields = {
            "location": "",
            "latitude": "",
            "longitude": "",
            "datetime": "",
            "species": "",
            "genus": "",
            "aphiaID": "",
            "life stage or biotype": "",
            "shape": "",
            "partial": "",
            "what the partial part is": "",
            "person classifying": "",
            "uncertain about class": "",
            "predicted_label": "",
            "taxonomist": "fixed",
            "institute": "fixed",
            "survey": "fixed"        
        }

        self.entries = {}
        self.checkboxes = {}
        self.selected_classes = set()

        setup_ui(self)
        bind_keys(self)

        self.device = get_device()

        # Default labels, default model, all selected by default
        with open("labels.json", 'r') as json_file:
            data = json.load(json_file)
            labels_dict = data.get('labels', {})
            self.LABELS = {int(num): name for num, name in labels_dict.items()}        
        arch = resnet18(num_classes=len(self.LABELS)).to(self.device)
        arch.load_state_dict(torch.load("model_18_21May.pth", map_location=self.device))
        self.model = arch
        print("loaded example model and model labels")
        print(self.LABELS)
        print(self.model)


        # Default images
        self.image_directory = str(os.getcwd())+"/example_images_folder"
        self.labels_directory = str(os.getcwd())+"/example_images_folder"
        self.load_images()
        self.display_current_image()

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
            image = Image.open(image_path)
            image.thumbnail((500, 500))
            self.photo = ImageTk.PhotoImage(image)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)


            for widget in self.fields_frame.winfo_children():
                widget.destroy()

            folder_name = os.path.basename(os.path.dirname(image_path))
            tk.Label(self.fields_frame, text="Folder Name:").grid(row=0, column=0)
            self.folder_name_entry = tk.Entry(self.fields_frame)
            self.folder_name_entry.grid(row=0, column=1)
            self.folder_name_entry.insert(0, folder_name)

            self.entries = {}
            self.checkboxes = {}  # Store references to the checkbuttons here
            
            row = 1
            for field, default_value in self.image_fields.items():
                tk.Label(self.fields_frame, text=f"{field}:").grid(row=row, column=0)
                
                if field == "aphiaID":
                    tk.Label(self.fields_frame, text="Select or Enter aphiaID:").grid(row=row, column=0)
                    
                    self.aphiaID_var = tk.StringVar(self)
                    self.aphiaID_var.set("")  # Set default value
                    
                    self.aphiaID_menu = tk.OptionMenu(self.fields_frame, self.aphiaID_var, *self.aphiaID_options)
                    self.aphiaID_menu.grid(row=row, column=2)
                    
                    self.custom_aphiaID_entry = tk.Entry(self.fields_frame)
                    self.custom_aphiaID_entry.grid(row=row, column=1)
                    self.custom_aphiaID_entry.insert(0, "")
                    
                    self.entries[field] = (self.aphiaID_var, self.custom_aphiaID_entry)
                else:
                    entry = tk.Entry(self.fields_frame)
                    entry.grid(row=row, column=1)
                    self.entries[field] = entry
                    
                    if default_value == "fixed":
                        checkbox_var = tk.BooleanVar()
                        checkbox = tk.Checkbutton(self.fields_frame, variable=checkbox_var)
                        checkbox.grid(row=row, column=2)
                        checkbox_var.set(field in self.fixed_values)  # Set checkbox state
                        self.checkboxes[field] = checkbox_var
                    
                row += 1

        else:
            print("No images found to display")




    def update_aphiaID_options(self, aphiaID_list):
        unique_aphiaIDs = sorted(set(aphiaID_list))  # Optional: sort to maintain a consistent order
        
        menu = self.aphiaID_menu["menu"]
        menu.delete(0, "end")
        
        menu.add_command(label="", command=tk._setit(self.aphiaID_var, ""))
        
        for aphiaID in unique_aphiaIDs:
            menu.add_command(label=aphiaID, command=tk._setit(self.aphiaID_var, aphiaID))
        
        self.aphiaID_var.set("")  # Ensure the default is empty


    def save_fields_and_next_image(self):
        if self.images:
            image_path = self.images[self.current_image_index]


            self.display_current_image()

            selected_aphiaID = self.aphiaID_var.get()
            custom_aphiaID = self.custom_aphiaID_entry.get().strip()
            aphiaID = custom_aphiaID if custom_aphiaID else selected_aphiaID

            image_data = {}
            for field in self.image_fields:
                if field == "aphiaID":
                    image_data[field] = aphiaID
                elif field in self.entries:
                    if isinstance(self.entries[field], tuple):
                        image_data[field] = self.entries[field][0].get()
                    else:
                        image_data[field] = self.entries[field].get()

            image_data["file_name"] = os.path.basename(image_path)
            image_data["folder_name"] = self.folder_name_entry.get()

            # Save fixed values if their checkboxes are checked
            for field, checkbox_var in self.checkboxes.items():
                self.fixed_values[field] = self.entries[field].get()
            self.data["images"].append(image_data)

            print(image_data)
            self.labeled_images_count += 1

            if self.labeled_images_count % 5 == 0:
                self.save_data()

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

    def process_all_images(self):
        response = messagebox.askyesno("Confirm", "This will process all images in the directory and save to CSV and JSON format based only on folder name. This will process a few thousand images in a minute. Note if you have lots of images, the program will be unresponsive while these are written. Continue?")
        if response:
            while self.current_image_index < len(self.images):
                self.save_fields_and_next_image()

            save_to_files(self.data, self.labels_directory, self.output_name)
            messagebox.showinfo("Completed", "All images have been processed.")

    def load_model(self, model_path):
        model = load_model(model_path, self.LABELS, self.device)

    def toggle_class(self, label):
        if self.checkboxes[label].get():
            self.selected_classes.add(label)
        else:
            self.selected_classes.discard(label)

    def save_data(self, event=None):
        if not self.output_name:
            messagebox.showwarning("No Output Name", "You are not saving your labels. Please provide a valid save directory.")
            return

        success = save_to_files(self.data, self.labels_directory, self.output_name)
        
        if not success:
            messagebox.showerror("Save Failed", "Failed to save the file. Please check the save path and ensure the file is not already open.")

        save_to_files(self.data, self.labels_directory, self.output_name)

if __name__ == "__main__":
    app = COCOAnnotator()
    app.mainloop()
