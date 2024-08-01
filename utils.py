import json
import csv
import os
import torch
import torchvision
from torchvision.transforms import functional
from PIL import Image
import tifffile as tiff
import exifread
from io import BytesIO
import tkinter as tk

def resnet18(num_classes):
    model = torchvision.models.resnet18()
    model.fc = torch.nn.Linear(model.fc.in_features, num_classes)
    model.eval()
    return model

def get_device():
    device = torch.device("cpu")
    if torch.cuda.is_available():
        device = torch.device("cuda")
    return device

def classify(image_path, device, model, labels):
    image = tiff.imread(image_path)
    t = functional.to_tensor(image)
    t = functional.resize(t, (256, 256))
    t = t.unsqueeze(dim=0)
    t = t.to(device)
    with torch.set_grad_enabled(False):
        outputs = model(t)
        scores = torch.softmax(outputs, dim=1)
        _, preds = torch.max(outputs, 1)
    class_number = preds[0].item()
    class_name = labels.get(class_number, "Unknown")
    return class_name, scores[0]

def extract_gps(filename_or_bytes):
    try:
        try:
            tags = exifread.process_file(BytesIO(filename_or_bytes))
        except:
            with open(filename_or_bytes, "rb") as file:
                image_bytes = file.read()
            stream = BytesIO(image_bytes)
            tags = exifread.process_file(stream)

        latitude = tags.get("GPS GPSLatitude").values
        longitude = tags.get("GPS GPSLongitude").values
        latitude_ref = tags.get("GPS GPSLatitudeRef").values[0]
        longitude_ref = tags.get("GPS GPSLongitudeRef").values[0]
        image_datetime = tags.get("Image DateTime").values

        latitude = float(latitude[0]) + float(latitude[1]) / 60 + float(latitude[2]) / 3600
        if latitude_ref == "S":
            latitude *= -1

        longitude = float(longitude[0]) + float(longitude[1]) / 60 + float(longitude[2]) / 3600
        if longitude_ref == "W":
            longitude *= -1
    except:
        latitude = 'error'
        longitude = 'error'
        image_datetime = 'error'
    return latitude, longitude, image_datetime

def save_to_files(data, labels_directory, output_name):
    try:
        json_path = os.path.join(labels_directory, f"{output_name}.json")
        with open(json_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)

        csv_path = os.path.join(labels_directory, f"{output_name}.csv")
        with open(csv_path, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            headers = ["file_name", "folder_name"] + list(data['image_fields'].keys()) + ["predicted_label"]
            writer.writerow(headers)
            for image in data["images"]:
                row = [image.get(header, "") for header in headers]
                writer.writerow(row)
        return True
    except Exception as e:
        print(f"Failed to save files: {e}")
        return False

def bind_keys(app):
    for i in range(1, 10):
        app.bind(f"<Alt-Key-{i}>", app.focus_nth_entry)
    app.bind("<Control-n>", lambda event: app.save_fields_and_next_image())
    app.bind("<Control-s>", app.save_data)  # Bind Ctrl + S to save function


def load_model(model_path, labels, device):
    try:
        model = resnet18(num_classes=len(labels)).to(device)
        model.load_state_dict(torch.load(model_path, map_location=device))
        return model
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load model: {e}")
        return None

def setup_ui(app):
    app.upload_labels_button = tk.Button(app, text="1: Provide model labels (.json file)", command=app.upload_labels_json)
    app.upload_labels_button.grid(row=0, column=0, columnspan=2, pady=5, sticky="ew")

    app.load_model_button = tk.Button(app, text="2: Provide model (.pth file)", command=app.load_model_dialog)
    app.load_model_button.grid(row=1, column=0, columnspan=2, pady=5, sticky="ew")

    app.select_labels_dir_button = tk.Button(app, text="3: Provide directory for labels (my/saved/outputs/dir)", command=app.select_labels_directory)
    app.select_labels_dir_button.grid(row=2, column=0, columnspan=2, pady=5, sticky="ew")

    app.select_dir_button = tk.Button(app, text="4: Provide directory for images (my/input/images/library)", command=app.select_image_directory)
    app.select_dir_button.grid(row=3, column=0, columnspan=2, pady=5, sticky="ew")

    app.import_config_button = tk.Button(app, text="Optional: Import custom labelling standard", command=app.import_config)
    app.import_config_button.grid(row=4, column=0, columnspan=2, pady=5, sticky="ew")

    app.process_all_button = tk.Button(app, text="Optional: Process All", command=app.process_all_images)
    app.process_all_button.grid(row=5, column=0, columnspan=2, pady=5, sticky="ew")

    app.main_frame = tk.Frame(app)
    app.main_frame.grid(row=6, column=0, columnspan=2, sticky="nsew")

    app.canvas = tk.Canvas(app.main_frame, width=500, height=500)
    app.canvas.grid(row=0, column=0, padx=5, pady=5)

    app.fields_frame = tk.Frame(app.main_frame)
    app.fields_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ns")

    app.next_button = tk.Button(app, text="Next Image", command=app.save_fields_and_next_image)
    app.next_button.grid(row=7, column=0, columnspan=2, pady=5, sticky="ew")

    app.data = {
        "images": [],
        "image_fields": app.image_fields
    }



def load_images_from_directory(image_directory):
    valid_extensions = (
        '.png', '.PNG', '.jpg', '.JPG', '.jpeg', '.JPEG', '.bmp', '.BMP', '.gif', '.GIF',
        '.tiff', '.TIFF', '.tif', '.TIF', '.ico', '.ICO', '.webp', '.WEBP', '.svg', '.SVG',
        '.heic', '.HEIC', '.heif', '.HEIF', '.jfif', '.JFIF', '.pjpeg', '.PJPEG', '.pjp', '.PJP', '.avif', '.AVIF'
    )
    
    images = []
    for dp, dn, filenames in os.walk(image_directory):
        for f in filenames:
            file_path = os.path.join(dp, f)
            if f.lower().endswith(valid_extensions):
                images.append(file_path)
    
    return images


