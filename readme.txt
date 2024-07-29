# COCO Metadata Annotator

COCO Metadata Annotator is a simple tool to help you annotate image datasets with custom metadata.

## Features

- Define custom common fields and image-specific fields.
- Load images from a selected directory.
- Annotate each image with specified fields.
- Save the annotated data to a JSON file.

## Installation

1. **Clone the repository:**

    ```sh
    git clone https://github.com/yourusername/COCOAnnotator.git
    cd COCOAnnotator
    ```

2. **Install the required packages:**

    ```sh
    pip install pillow
    ```

## Requirements

- Python 3.x
- Tkinter
- Pillow

## Usage

1. **Run the application:**

    ```sh
    python coco_annotator.py
    ```

2. **Specify the common fields:**

    A dialog will prompt you to enter the common fields (comma-separated).

3. **Specify the image-specific fields:**

    Another dialog will prompt you to enter the image-specific fields (comma-separated).

4. **Select the JSON file location:**

    Click the "Select JSON File Location" button and choose where to save the JSON file.

5. **Select the master directory:**

    Click the "Select Master Directory" button and choose the directory containing the images to annotate.

6. **Annotate images:**

    The first image from the directory will be displayed. Fill in the fields and click "Next Image" to save the data and move to the next image.

7. **Complete annotation:**

    After annotating all images, a message will inform you that all images have been processed, and the application will exit.

8. Creating an executable, if required

    To rebuild, use the command pyinstaller labeller.py in anaconda prompt or similar (after pip installing pyinstaller, and making your changes to labeller.py)

## JSON Structure

The output JSON file will have the following structure:

```json
{
  "info": {
    "common_field1": "",
    "common_field2": "",
    ...
  },
  "images": [
    {
      "file_name": "image1.jpg",
      "folder_name": "folder1",
      "image_field1": "value1",
      "image_field2": "value2",
      ...
    },
    {
      "file_name": "image2.jpg",
      "folder_name": "folder2",
      "image_field1": "value1",
      "image_field2": "value2",
      ...
    },
    ...
  ]
}
```

## Contributing

This is an early version, contributions are welcome! Please fork this repository and submit a pull request with your improvements.

## License

This project is licensed under the MIT License.



