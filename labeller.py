import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import os
import json
from PIL import Image, ImageTk

class COCOAnnotator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("COCO Metadata Annotator")

        self.common_fields = []
        self.image_fields = []
        self.master_directory = ""
        self.json_file_path = ""
        self.images = []
        self.current_image_index = 0
        self.photo = None  # Add a reference to the image

        self.request_fields()  # Ask user for common and image-specific fields

        self.setup_ui()  # Set up the user interface

    def request_fields(self):
        print("Requesting common fields")
        self.common_fields = simpledialog.askstring("Common Fields", "Enter common fields (comma-separated):").split(',')
        print(f"Common fields: {self.common_fields}")

        print("Requesting image-specific fields")
        self.image_fields = simpledialog.askstring("Image Fields", "Enter image-specific fields (comma-separated):").split(',')
        print(f"Image fields: {self.image_fields}")

    def setup_ui(self):
        # Buttons for selecting JSON file location and master directory
        self.select_json_button = tk.Button(self, text="Select JSON File Location", command=self.select_json_location)
        self.select_json_button.pack(pady=5)

        self.select_dir_button = tk.Button(self, text="Select Master Directory", command=self.select_master_directory)
        self.select_dir_button.pack(pady=5)

        self.canvas = tk.Canvas(self, width=500, height=500)  # Canvas to display images
        self.canvas.pack()

        self.fields_frame = tk.Frame(self)  # Frame to hold input fields
        self.fields_frame.pack()

        self.next_button = tk.Button(self, text="Next Image", command=self.save_fields_and_next_image)
        self.next_button.pack(pady=5)

        # Data structure for storing metadata
        self.data = {
            "info": {field: "" for field in self.common_fields},
            "images": []
        }
        print("UI setup complete")

    def select_json_location(self):
        print("Selecting JSON file location")
        self.json_file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if self.json_file_path:
            messagebox.showinfo("Selected JSON File", self.json_file_path)
            print(f"Selected JSON file path: {self.json_file_path}")

    def select_master_directory(self):
        print("Selecting master directory")
        self.master_directory = filedialog.askdirectory()
        if self.master_directory:
            messagebox.showinfo("Selected Directory", self.master_directory)
            print(f"Selected master directory: {self.master_directory}")
            self.load_images()
            self.display_current_image()

    def load_images(self):
        print("Loading images")
        self.images = []
        for dp, dn, filenames in os.walk(self.master_directory):
            print(f"Checking directory: {dp}")
            for f in filenames:
                file_path = os.path.join(dp, f)
                print(f"Found file: {file_path}")
                print(f"Adding image: {file_path}")
                self.images.append(file_path)
        print(f"Found {len(self.images)} images")

    def display_current_image(self):
        if self.images:
            image_path = self.images[self.current_image_index]
            print(f"Displaying image {self.current_image_index + 1}/{len(self.images)}: {image_path}")
            image = Image.open(image_path)
            image.thumbnail((500, 500))  # Resize image to fit within 500x500
            self.photo = ImageTk.PhotoImage(image)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

            for widget in self.fields_frame.winfo_children():
                widget.destroy()

            # Display folder name and create entry fields for image-specific fields
            folder_name = os.path.basename(os.path.dirname(image_path))
            tk.Label(self.fields_frame, text="Folder Name:").grid(row=0, column=0)
            self.folder_name_entry = tk.Entry(self.fields_frame)
            self.folder_name_entry.grid(row=0, column=1)
            self.folder_name_entry.insert(0, folder_name)

            self.entries = {}
            for i, field in enumerate(self.image_fields):
                tk.Label(self.fields_frame, text=f"{field}:").grid(row=i+1, column=0)
                entry = tk.Entry(self.fields_frame)
                entry.grid(row=i+1, column=1)
                self.entries[field] = entry
        else:
            print("No images found to display")

    def save_fields_and_next_image(self):
        if self.images:
            image_path = self.images[self.current_image_index]
            print(f"Saving fields for image: {image_path}")
            # Collect data from input fields
            image_data = {
                "file_name": os.path.basename(image_path),
                "folder_name": self.folder_name_entry.get(),
                **{field: self.entries[field].get() for field in self.image_fields}
            }
            self.data["images"].append(image_data)

            # Save data to JSON file
            with open(self.json_file_path, 'w') as json_file:
                json.dump(self.data, json_file, indent=4)

            self.current_image_index += 1
            if self.current_image_index < len(self.images):
                self.display_current_image()
            else:
                messagebox.showinfo("Completed", "All images have been processed.")
                print("All images processed, exiting.")
                self.quit()

if __name__ == "__main__":
    app = COCOAnnotator()
    app.mainloop()
