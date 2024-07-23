import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import os
from PIL import Image, ImageTk
import torch
from utils import resnet18, get_device, classify, extract_gps, save_to_files, LABELS

class COCOAnnotator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("COCO Metadata Annotator")

        self.image_directory = ""
        self.labels_directory = ""
        self.output_name = ""
        self.images = []
        self.current_image_index = 0
        self.photo = None

        self.common_fields = {
            "survey ID": "",
            "survey region": "",
            "instrument": "PI10",
            "class options considered": ""
        }

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
            "annotations": "",
            "categories": ""
        }

        self.entries = {}
        self.setup_ui()
        self.bind_keys()

        self.device = get_device()
        self.model = resnet18(num_classes=len(LABELS)).to(self.device)
        self.model.load_state_dict(torch.load('C:/Users/JR13/Documents/LOCAL_NOT_ONEDRIVE/rapid-plankton/edge-ai/models/model_18_21May.pth', map_location=self.device))

    def setup_ui(self):
        self.select_labels_dir_button = tk.Button(self, text="Select directory for labels (output)", command=self.select_labels_directory)
        self.select_labels_dir_button.pack(pady=5)

        self.select_dir_button = tk.Button(self, text="Select directory for images (input)", command=self.select_image_directory)
        self.select_dir_button.pack(pady=5)

        self.import_config_button = tk.Button(self, text="Import labelling standard", command=self.import_config)
        self.import_config_button.pack(pady=5)

        self.process_all_button = tk.Button(self, text="Process All", command=self.process_all_images)
        self.process_all_button.pack(pady=5)

        self.canvas = tk.Canvas(self, width=500, height=500)
        self.canvas.pack()

        self.fields_frame = tk.Frame(self)
        self.fields_frame.pack()

        self.next_button = tk.Button(self, text="Next Image", command=self.save_fields_and_next_image)
        self.next_button.pack(pady=5)

        self.data = {
            "info": self.common_fields,
            "images": [],
            "image_fields": self.image_fields
        }

    def bind_keys(self):
        for i in range(1, 10):
            self.bind(f"<Alt-Key-{i}>", self.focus_nth_entry)
        self.bind("<Control-n>", lambda event: self.save_fields_and_next_image())

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
        self.images = []
        valid_extensions = ('.png', '.PNG', '.jpg', '.JPG', '.jpeg', '.JPEG', '.bmp', '.BMP', '.gif', '.GIF', '.tiff', '.TIFF', '.tif', '.TIF', '.ico', '.ICO', '.webp', '.WEBP', '.svg', '.SVG', '.heic', '.HEIC', '.heif', '.HEIF', '.jfif', '.JFIF', '.pjpeg', '.PJPEG', '.pjp', '.PJP', '.avif', '.AVIF')
        for dp, dn, filenames in os.walk(self.image_directory):
            for f in filenames:
                file_path = os.path.join(dp, f)
                if f.lower().endswith(valid_extensions):
                    self.images.append(file_path)

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

            # Classify the image and add the predicted label
            label, scores = classify(image_path, self.device, self.model)
            tk.Label(self.fields_frame, text="Predicted Label:").grid(row=len(self.image_fields) + 1, column=0)
            self.predicted_label_entry = tk.Entry(self.fields_frame)
            self.predicted_label_entry.grid(row=len(self.image_fields) + 1, column=1)
            self.predicted_label_entry.insert(0, label)
            self.entries["predicted_label"] = self.predicted_label_entry

        else:
            print("No images found to display")

    def save_fields_and_next_image(self):
        if self.images:
            image_path = self.images[self.current_image_index]
            image_data = {
                "file_name": os.path.basename(image_path),
                "folder_name": self.folder_name_entry.get(),
                **{field: self.entries[field].get() for field in self.image_fields},
                "predicted_label": self.entries["predicted_label"].get()
            }
            self.data["images"].append(image_data)

            self.current_image_index += 1
            if self.current_image_index < len(self.images):
                self.display_current_image()
            else:
                messagebox.showinfo("Completed", "All images have been processed.")
                save_to_files(self.data, self.labels_directory, self.output_name)
                self.quit()

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
        response = messagebox.askyesno("Confirm", "This will process all images in the directory and save to csv and json format based only on folder name. This will process a few thousand images in a minute. Note if you have lots of images, the program will be unresponsive while these are written. Continue?")
        if response:
            while self.current_image_index < len(self.images):
                self.save_fields_and_next_image()

            save_to_files(self.data, self.labels_directory, self.output_name)
            messagebox.showinfo("Completed", "All images have been processed.")

if __name__ == "__main__":
    app = COCOAnnotator()
    app.mainloop()
