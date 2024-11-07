import requests
import subprocess
import os
import json
import pandas as pd
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import tkinter as tk
import csv

def clear_temp_folder(temp_dir):
    """Clear the temporary directory."""
    for filename in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")


def compile_cyz2json(clone_dir, path_entry):
    """Clone and compile the cyz2json tool."""
    if os.path.exists(clone_dir):
        messagebox.showinfo("Info", "cyz2json already exists in " + clone_dir)
        return

    try:
        subprocess.run(["git", "clone", "https://github.com/OBAMANEXT/cyz2json.git", clone_dir], check=True)
        subprocess.run(["dotnet", "build", "-o", "bin"], cwd=clone_dir, check=True)
        messagebox.showinfo("Success", "cyz2json downloaded and compiled successfully!")
        path_entry.delete(0, tk.END)
        path_entry.insert(0, os.path.join(clone_dir, "bin", "Cyz2Json.dll"))
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Compilation Error", f"Failed to compile cyz2json: {e}. Have you installed the requirement DotNet version 8.0? See https://github.com/OBAMANEXT/cyz2json")
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")


def download_file(url_entry, temp_dir, load_entry):
    """Download the file from the specified URL."""
    url = url_entry.get()
    try:
        response = requests.get(url, allow_redirects=True)
        response.raise_for_status()
        filename = os.path.basename(url)
        downloaded_file = os.path.join(temp_dir, filename)
        with open(downloaded_file, 'wb') as file:
            file.write(response.content)
        load_entry.delete(0, tk.END)
        load_entry.insert(0, downloaded_file)
        messagebox.showinfo("Download Success", f"File downloaded successfully to: {downloaded_file}")
    except requests.RequestException as e:
        messagebox.showerror("Download Error", f"Failed to download file: {e}")


def load_file(cyz2json_path, downloaded_file, json_file):
    """Convert .cyz file to .json using cyz2json tool."""
    try:
        subprocess.run(["dotnet", cyz2json_path, downloaded_file, "--output", json_file], check=True)
        messagebox.showinfo("Success", f"File processed successfully. Output: {json_file}")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Processing Error", f"Failed to process file: {e}")


def select_output_dir(app):
    """Open a dialog to select the output directory."""
    app.output_dir = filedialog.askdirectory()
    if app.output_dir:
        messagebox.showinfo("Output Directory Selected", f"Output files will be saved in: {app.output_dir}")



def load_json(file_path):
    with open(file_path, 'r') as f:
        json_data = json.load(f)
    return json_data

def select_particles(json_data, particle_ids):
    particles = [p for p in json_data['particles'] if p['particleId'] in particle_ids]
    return particles if particles else None

def get_pulses(particles):
    pulses = {p['particleId']: p.get('pulseShapes') for p in particles}
    return pulses



def display_image(self,root,current_image_index, output_dir, image_label, tif_files, metadata, confidence_entry, species_entry):
    """Display the image and update metadata entry fields."""
    image_file = tif_files[current_image_index]
    image_path = os.path.join(output_dir, image_file)
    
    img = Image.open(image_path)
    img = img.resize((400, 400), Image.LANCZOS)
    img_tk = ImageTk.PhotoImage(img)

    if self.image_label is None:
        self.image_label = tk.Label(self.root, image=img_tk)
        self.image_label.image = img_tk
        self.image_label.pack(pady=10)
    else:
        self.image_label.config(image=img_tk)
        self.image_label.image = img_tk

    # Load saved metadata if it exists
    metadata = self.metadata.get(image_file, {"confidence": "", "species": ""})
    self.confidence_entry.delete(0, tk.END)
    self.confidence_entry.insert(0, metadata["confidence"])
    self.species_entry.delete(0, tk.END)
    self.species_entry.insert(0, metadata["species"])



def update_navigation_buttons(prev_button, next_button, current_image_index, total_images):
    """Update the state of navigation buttons based on the current image index."""
    prev_button.config(state=tk.NORMAL if current_image_index > 0 else tk.DISABLED)
    next_button.config(state=tk.NORMAL if current_image_index < total_images - 1 else tk.DISABLED)


def save_metadata(current_image_index, tif_files, metadata, confidence_entry, species_entry, output_dir):
    """Save metadata to a CSV file."""
    image_file = tif_files[current_image_index]
    confidence = confidence_entry.get()
    species = species_entry.get()
    metadata[image_file] = {"confidence": confidence, "species": species}

    metadata_file_path = os.path.join(output_dir, "label_data.csv")
    with open(metadata_file_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Image File", "confidence", "Suspected Species"])
        for image, data in metadata.items():
            writer.writerow([image, data["confidence"], data["species"]])

