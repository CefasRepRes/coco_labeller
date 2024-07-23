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

LABELS = [
    "copepod",
    "detritus",
    "noncopepod",
]

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

def classify(image_path, device, model):
    image = tiff.imread(image_path)
    t = functional.to_tensor(image)
    t = functional.resize(t, (256, 256))
    t = t.unsqueeze(dim=0)
    t = t.to(device)
    with torch.set_grad_enabled(False):
        outputs = model(t)
        scores = torch.softmax(outputs, dim=1)  # Calculate softmax scores
        _, preds = torch.max(outputs, 1)
    return LABELS[preds[0]], scores[0]  # Return label and scores

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
