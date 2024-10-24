import os
import tempfile
import requests
import subprocess
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk  # Import for image handling

class BlobApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Blob File Loader")
        self.root.geometry("800x600")
        self.temp_dir = os.path.join(tempfile.gettempdir(), "BlobAppTemp")
        self.clone_dir = os.path.join(self.temp_dir, "cyz2json")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.clear_temp_folder()
        
        self.compile_button = tk.Button(root, text="Download and compile cyz2json tool (required)", command=self.compile_cyz2json)
        self.compile_button.pack(pady=10)
        
        self.path_label = tk.Label(root, text="Path to cyz2json Installation:")
        self.path_label.pack(pady=5)
        
        self.path_entry = tk.Entry(root, width=100)
        self.path_entry.insert(0, self.clone_dir + "\\bin\\Cyz2Json.dll")
        self.path_entry.pack(pady=5)
        
        self.url_label = tk.Label(root, text="Blob File URL:")
        self.url_label.pack(pady=5)
        
        self.url_entry = tk.Entry(root, width=100)
        self.url_entry.insert(0, "https://citprodflowcytosa.blob.core.windows.net/public/ThamesSTN6MA4_9%202023-10-16%2011h24.cyz")
        self.url_entry.pack(pady=5)
        
        self.download_button = tk.Button(root, text="Download", command=self.download_file)
        self.download_button.pack(pady=10)
        
        self.load_label = tk.Label(root, text="Load File Path:")
        self.load_label.pack(pady=5)
        
        self.load_entry = tk.Entry(root, width=100)
        self.load_entry.pack(pady=5)
        
        self.load_button = tk.Button(root, text="Convert to json", command=self.load_file)
        self.load_button.pack(pady=10)
        
        # New button to process the file
        self.process_button = tk.Button(root, text="Extract images and associated data", command=self.process_file)
        self.process_button.pack(pady=10)

        self.downloaded_file = None
        self.json_file = os.path.join(self.temp_dir, "tempfile.json")        
        self.csv_file = os.path.join(self.temp_dir, "tempfile.csv")
        
        # New image label for displaying the images
        self.image_label = None

    def clear_temp_folder(self):
        for filename in os.listdir(self.temp_dir):
            file_path = os.path.join(self.temp_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting file: {e}")

    def compile_cyz2json(self):
        BlobApp.clone_dir = os.path.join(self.temp_dir, "cyz2json")
        if os.path.exists(BlobApp.clone_dir):
            messagebox.showinfo("Info", "cyz2json already exists in " + BlobApp.clone_dir)
            return
        try:
            subprocess.run(["git", "clone", "https://github.com/OBAMANEXT/cyz2json.git", BlobApp.clone_dir], check=True)
            subprocess.run(["dotnet", "build", "-o", "bin"], cwd=BlobApp.clone_dir, check=True)
            messagebox.showinfo("Success", "cyz2json downloaded and compiled successfully!")
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, os.path.join(BlobApp.clone_dir, "bin", "Cyz2Json.dll"))
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Compilation Error", f"Failed to compile cyz2json: {e}. Have you installed the requirement DotNet version 8.0? See https://github.com/OBAMANEXT/cyz2json")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def download_file(self):
        url = self.url_entry.get()
        try:
            response = requests.get(url, allow_redirects=True)
            response.raise_for_status()
            filename = os.path.basename(url)
            self.downloaded_file = os.path.join(self.temp_dir, filename)
            with open(self.downloaded_file, 'wb') as file:
                file.write(response.content)
            self.load_entry.delete(0, tk.END)
            self.load_entry.insert(0, self.downloaded_file)
            messagebox.showinfo("Download Success", f"File downloaded successfully to: {self.downloaded_file}")
        except requests.RequestException as e:
            messagebox.showerror("Download Error", f"Failed to download file: {e}")

    def load_file(self):
        if not self.downloaded_file:
            messagebox.showerror("Load Error", "Please download a file first!")
            return
        cyz2json_path = self.path_entry.get()
        try:
            subprocess.run(["dotnet", cyz2json_path, self.downloaded_file, "--output", self.json_file], check=True)
            messagebox.showinfo("Success", f"File processed successfully. Output: {self.json_file}")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Processing Error", f"Failed to process file: {e}")

    def process_file(self):
        try:
            subprocess.run(["python", "./listmode.py", self.json_file, '--output', self.csv_file, self.temp_dir, self.temp_dir], check=True)
            messagebox.showinfo("Success", f"File processed successfully. Output: {self.csv_file}")
            self.show_images()  # Call the method to display images
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Processing Error", f"Failed to process file: {e}")

    def show_images(self):
        tif_files = [f for f in os.listdir(self.temp_dir) if f.endswith('.tif')]
        if not tif_files:
            messagebox.showinfo("No Images", "No .tif files found in the directory!")
            return
        
        self.display_image(os.path.join(self.temp_dir, tif_files[0]))  # Display the first image

    def display_image(self, image_path):
        img = Image.open(image_path)
        img = img.resize((400, 400), Image.LANCZOS)  # Use Image.LANCZOS instead of Image.ANTIALIAS
        img_tk = ImageTk.PhotoImage(img)
        
        if self.image_label is None:
            self.image_label = tk.Label(self.root, image=img_tk)
            self.image_label.image = img_tk
            self.image_label.pack(pady=10)
        else:
            self.image_label.config(image=img_tk)
            self.image_label.image = img_tk



if __name__ == "__main__":
    root = tk.Tk()
    app = BlobApp(root)
    root.mainloop()
