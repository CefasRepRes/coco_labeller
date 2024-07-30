import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import os
import json
from PIL import Image, ImageTk
import torch
from utils import resnet18, get_device, classify, extract_gps, save_to_files, load_images_from_directory, load_model, bind_keys, setup_ui
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

        self.output_name = ""
        self.current_image_index = 0
        self.photo = None
        self.model = None
        self.labeled_images_count = 0

        self.common_fields = {
            "survey ID": "",
            "survey region": "",
            "instrument": "PI10",
            "class options considered": ""
        }

        # Define default aphiaID options
        self.aphiaID_options = ["123456", "789101", "112131", "415161", "718192"]

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
            "annotations": "",
            "categories": ""
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
        self.checkbox_window = tk.Toplevel(self)
        self.checkbox_window.title("Select Classes and Scores")

        # Create checkboxes for labels
        for label in self.LABELS.values():
            var = tk.BooleanVar(value=True)  # Set the default value to True
            checkbox = tk.Checkbutton(self.checkbox_window, text=label, variable=var, command=lambda l=label: self.toggle_class(l))
            checkbox.pack(anchor="w")
            self.checkboxes[label] = var
            self.selected_classes.add(label)  # Add all labels to selected_classes by default
        
        # Create score filters
        tk.Label(self.checkbox_window, text="Prediction scores above:").pack(anchor="w")
        self.min_score_entry = tk.Entry(self.checkbox_window)
        self.min_score_entry.pack(anchor="w")
        self.min_score_entry.insert(0, "0.0")

        tk.Label(self.checkbox_window, text="Prediction scores below:").pack(anchor="w")
        self.max_score_entry = tk.Entry(self.checkbox_window)
        self.max_score_entry.pack(anchor="w")
        self.max_score_entry.insert(0, "1.0")

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

            latitude, longitude, image_datetime = extract_gps(image_path)

            for widget in self.fields_frame.winfo_children():
                widget.destroy()

            folder_name = os.path.basename(os.path.dirname(image_path))
            tk.Label(self.fields_frame, text="Folder Name:").grid(row=0, column=0)
            self.folder_name_entry = tk.Entry(self.fields_frame)
            self.folder_name_entry.grid(row=0, column=1)
            self.folder_name_entry.insert(0, folder_name)

            self.entries = {}
            for i, (field, default_value) in enumerate(self.image_fields.items()):
                tk.Label(self.fields_frame, text=f"{field}:").grid(row=i+1, column=0)
                
                if field == "aphiaID":
                    tk.Label(self.fields_frame, text="Select or Enter aphiaID:").grid(row=i+1, column=0)
                    
                    # OptionMenu for predefined aphiaID options
                    self.aphiaID_var = tk.StringVar(self)
                    self.aphiaID_var.set("")  # Set default value
                    self.aphiaID_menu = tk.OptionMenu(self.fields_frame, self.aphiaID_var, *self.aphiaID_options)
                    self.aphiaID_menu.grid(row=i+1, column=1)
                    
                    # Text entry for user-defined aphiaID
                    self.custom_aphiaID_entry = tk.Entry(self.fields_frame)
                    self.custom_aphiaID_entry.grid(row=i+1, column=2)
                    self.custom_aphiaID_entry.insert(0, "")
                    
                    self.entries[field] = (self.aphiaID_var, self.custom_aphiaID_entry)
                else:
                    entry = tk.Entry(self.fields_frame)
                    entry.grid(row=i+1, column=1)
                    if field == "latitude":
                        entry.insert(0, latitude if latitude != 'error' else "")
                    elif field == "longitude":
                        entry.insert(0, longitude if longitude != 'error' else "")
                    elif field == "datetime":
                        entry.insert(0, image_datetime if image_datetime != 'error' else "")
                    else:
                        entry.insert(0, default_value)
                    self.entries[field] = entry

            if self.model:
                label, scores = classify(image_path, self.device, self.model, self.LABELS)
                tk.Label(self.fields_frame, text="Predicted Label:").grid(row=len(self.image_fields) + 1, column=0)
                self.predicted_label_entry = tk.Entry(self.fields_frame)
                self.predicted_label_entry.grid(row=len(self.image_fields) + 1, column=1)
                self.predicted_label_entry.insert(0, label)
                self.entries["predicted_label"] = self.predicted_label_entry

                min_score = float(self.min_score_entry.get())
                max_score = float(self.max_score_entry.get())
                
                self.update_idletasks()
                time.sleep(0.01)

                if not (min_score <= scores.max().item() <= max_score) or label not in self.selected_classes:
                    self.save_fields_and_next_image()
                    return

                # Update AphiaID dropdown based on predicted label
                if label in self.aphia_data:
                    self.update_aphiaID_options(self.aphia_data[label])
                else:
                    self.update_aphiaID_options([])  # Clear options if no data

            else:
                messagebox.showwarning("Model Not Loaded", "Please load a model before proceeding.")
        else:
            print("No images found to display")

    def update_aphiaID_options(self, aphiaID_list):
        menu = self.aphiaID_menu["menu"]
        menu.delete(0, "end")
        for aphiaID in aphiaID_list:
            menu.add_command(label=aphiaID, command=tk._setit(self.aphiaID_var, aphiaID))
        self.aphiaID_var.set(aphiaID_list[0] if aphiaID_list else "")
        
        

    def save_fields_and_next_image(self):
        if self.images:
            image_path = self.images[self.current_image_index]
            if not self.model:
                messagebox.showwarning("Model Not Loaded", "Please load a model before proceeding.")
                return

            label, scores = classify(image_path, self.device, self.model, self.LABELS)
            min_score = float(self.min_score_entry.get())
            max_score = float(self.max_score_entry.get())

            if label not in self.selected_classes or not (min_score <= scores.max().item() <= max_score):
                self.current_image_index += 1
                if self.current_image_index < len(self.images):
                    self.display_current_image()
                return

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

            predicted_label_entry = self.entries.get("predicted_label")
            image_data["predicted_label"] = predicted_label_entry.get() if predicted_label_entry else ""

            image_data["file_name"] = os.path.basename(image_path)
            image_data["folder_name"] = self.folder_name_entry.get()

            self.data["images"].append(image_data)

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
                self.common_fields = config.get("common_fields", self.common_fields)
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

    def upload_labels_json(self):
        json_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if json_path:
            try:
                with open(json_path, 'r') as json_file:
                    data = json.load(json_file)
                    labels_dict = data.get('labels', {})
                    if not labels_dict:
                        messagebox.showwarning("No Labels Found", "No labels found in the JSON file.")
                    else:
                        self.LABELS = {int(num): name for num, name in labels_dict.items()}
                        messagebox.showinfo("Labels Loaded", f"Labels loaded successfully from {json_path}")
                        if self.model:
                            self.load_model_dialog()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load labels: {e}")

    def load_model(self, model_path):
        model = load_model(model_path, self.LABELS, self.device)

    def load_model_dialog(self):
        model_path = filedialog.askopenfilename(filetypes=[("PyTorch Model files", "*.pth")])
        if model_path:
            self.model = self.load_model(model_path)
            if self.model:
                messagebox.showinfo("Model Loaded", f"Model loaded successfully from {model_path}")
                if not self.LABELS:
                    messagebox.showwarning("No Labels", "No labels available. Please upload labels JSON first.")
                    return
                self.checkbox_window = tk.Toplevel(self)
                self.checkbox_window.title("Select Classes and Scores")

                for label in self.LABELS.values():
                    var = tk.BooleanVar(value=True)  # Set the default value to True
                    checkbox = tk.Checkbutton(self.checkbox_window, text=label, variable=var, command=lambda l=label: self.toggle_class(l))
                    checkbox.pack(anchor="w")
                    self.checkboxes[label] = var
                    self.selected_classes.add(label)  # Add all labels to selected_classes by default

                # Create score filters in checkbox_window
                tk.Label(self.checkbox_window, text="Min Prediction Score:").pack(anchor="w")
                self.min_score_entry = tk.Entry(self.checkbox_window)
                self.min_score_entry.pack(anchor="w")
                self.min_score_entry.insert(0, "0.0")

                tk.Label(self.checkbox_window, text="Max Prediction Score:").pack(anchor="w")
                self.max_score_entry = tk.Entry(self.checkbox_window)
                self.max_score_entry.pack(anchor="w")
                self.max_score_entry.insert(0, "1.0")

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
