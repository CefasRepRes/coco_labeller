import os
import requests
import subprocess
import csv
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import pandas as pd

# Folder & File Management
def clear_temp_folder(temp_dir):
    for filename in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")

def select_output_dir(app):
    app.output_dir = filedialog.askdirectory()
    if app.output_dir:
        messagebox.showinfo("Output Directory Selected", f"Output files will be saved in: {app.output_dir}")

# Download & Processing Functions
def compile_cyz2json(clone_dir, path_entry):
    if os.path.exists(clone_dir):
        messagebox.showinfo("Info", "cyz2json already exists in " + clone_dir)
        return
    try:
        subprocess.run(["git", "clone", "https://github.com/OBAMANEXT/cyz2json.git", clone_dir], check=True)
        subprocess.run(["dotnet", "build", "-o", "bin"], cwd=clone_dir, check=True)
        messagebox.showinfo("Success", "cyz2json downloaded and compiled successfully!")
        path_entry.delete(0, "end")
        path_entry.insert(0, os.path.join(clone_dir, "bin", "Cyz2Json.dll"))
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Compilation Error", f"Failed to compile cyz2json: {e}. Have you installed the requirement DotNet version 8.0?")
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")

def download_file(url_entry, temp_dir, load_entry):
    url = url_entry.get()
    try:
        response = requests.get(url, allow_redirects=True)
        response.raise_for_status()
        filename = os.path.basename(url)
        downloaded_file = os.path.join(temp_dir, filename)
        with open(downloaded_file, 'wb') as file:
            file.write(response.content)
        load_entry.delete(0, "end")
        load_entry.insert(0, downloaded_file)
        messagebox.showinfo("Download Success", f"File downloaded successfully to: {downloaded_file}")
    except requests.RequestException as e:
        messagebox.showerror("Download Error", f"Failed to download file: {e}")

# Metadata Functions
def save_metadata(current_index, tif_files, metadata, biological_entry, species_entry, output_dir):
    image_file = tif_files[current_index]
    metadata[image_file] = {"biological": biological_entry.get(), "species": species_entry.get()}
    with open(os.path.join(output_dir, "metadata.csv"), mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Image File", "Biological", "Suspected Species"])
        for image, data in metadata.items():
            writer.writerow([image, data["biological"], data["species"]])

def display_image(index, output_dir, image_label, tif_files, metadata, biological_entry, species_entry):
    image_file = tif_files[index]
    image_path = os.path.join(output_dir, image_file)
    img = Image.open(image_path).resize((400, 400), Image.LANCZOS)
    img_tk = ImageTk.PhotoImage(img)
    image_label.config(image=img_tk)
    image_label.image = img_tk
    biological_entry.delete(0, "end")
    biological_entry.insert(0, metadata.get(image_file, {}).get("biological", ""))
    species_entry.delete(0, "end")
    species_entry.insert(0, metadata.get(image_file, {}).get("species", ""))

def update_navigation_buttons(prev_button, next_button, current_index, total_images):
    prev_button.config(state="normal" if current_index > 0 else "disabled")
    next_button.config(state="normal" if current_index < total_images - 1 else "disabled")


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

