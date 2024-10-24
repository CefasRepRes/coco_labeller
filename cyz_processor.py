import os
import tempfile
import requests
import subprocess
import tkinter as tk
from tkinter import messagebox


class BlobApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Blob File Loader")
        self.root.geometry("800x400")  # Set the width to 800 pixels and height to 400 pixels

        # Temporary directory and subfolder
        self.temp_dir = os.path.join(tempfile.gettempdir(), "BlobAppTemp")
        os.makedirs(self.temp_dir, exist_ok=True)  # Create the temp subfolder if it doesn't exist

        # Clear the temp folder on startup
        self.clear_temp_folder()

        # Predefined URL input
        self.url_label = tk.Label(root, text="Blob File URL:")
        self.url_label.pack(pady=5)

        self.url_entry = tk.Entry(root, width=100)  # Increased width
        self.url_entry.insert(0, "https://citprodflowcytosa.blob.core.windows.net/public/ThamesSTN6MA4_9%202023-10-16%2011h24.cyz")
        self.url_entry.pack(pady=5)

        # Download button
        self.download_button = tk.Button(root, text="Download", command=self.download_file)
        self.download_button.pack(pady=10)

        # Load file input
        self.load_label = tk.Label(root, text="Load File Path:")
        self.load_label.pack(pady=5)

        self.load_entry = tk.Entry(root, width=100)  # Increased width
        self.load_entry.pack(pady=5)

        # Path to cyz2json input
        self.path_label = tk.Label(root, text="Path to cyz2json Installation:")
        self.path_label.pack(pady=5)

        self.path_entry = tk.Entry(root, width=100)  # Increased width
        self.path_entry.insert(0, "./cyz2json/bin/Cyz2Json.dll")  # Default to a relative path
        self.path_entry.pack(pady=5)

        # Load button
        self.load_button = tk.Button(root, text="Load", command=self.load_file)
        self.load_button.pack(pady=10)

        self.downloaded_file = None  # Keep track of the downloaded file path

    def clear_temp_folder(self):
        """Clear the temporary directory."""
        for filename in os.listdir(self.temp_dir):
            file_path = os.path.join(self.temp_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting file: {e}")

    def download_file(self):
        """Download the blob file."""
        url = self.url_entry.get()

        try:
            response = requests.get(url, allow_redirects=True)
            response.raise_for_status()  # Raise an error for bad responses
            self.downloaded_file = os.path.join(self.temp_dir, "downloaded_file.cyz")
            with open(self.downloaded_file, 'wb') as file:
                file.write(response.content)

            # Autopopulate the load entry with the downloaded file path
            self.load_entry.delete(0, tk.END)  # Clear the existing content
            self.load_entry.insert(0, self.downloaded_file)

            messagebox.showinfo("Download Success", f"File downloaded successfully to: {self.downloaded_file}")
        except requests.RequestException as e:
            messagebox.showerror("Download Error", f"Failed to download file: {e}")

    def load_file(self):
        """Process the downloaded blob file."""
        if not self.downloaded_file:
            messagebox.showerror("Load Error", "Please download a file first!")
            return

        cyz2json_path = self.path_entry.get()  # Get the path from the input

        try:
            # Run the subprocess command
            output_file = os.path.join(self.temp_dir, "tempfile.json")
            subprocess.run(
                ["dotnet", cyz2json_path, self.downloaded_file, "--output", output_file],
                check=True
            )
            messagebox.showinfo("Success", f"File processed successfully. Output: {output_file}")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Processing Error", f"Failed to process file: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = BlobApp(root)
    root.mainloop()
