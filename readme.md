# COCO Metadata Annotator

In development.
This python app was branched from the tool intended for the Plankton Imager. 
I have not yet tried to compile it.

It is for the new flow cytometer only, old files will break the tool as it looks for fields in the listmode that will not be present.

Currently it is a weird tool that does (or should do) a few things:
- Installs cyz2json dependency
- Installs r dependencies
- Python dependencies "should" be handled on compilation but they almost certainly will not as the tool uses system command "python listmode.py" and it is not clear which python version that will call on. Needs addressing.
- Contains two versions of the listmode extraction. One extracts listmode parameters for all of the particles. The other extracts listmode parameters and pulse shapes only for the particles which have images (this is so images can be labelled).
- Applies the r random forest model to the flow cytometer data for ALL particles.
- Makes a 3D plot of this random forest model inference.
- Allows you to label images and saves the labels alongside the images and the pulse shapes + listmode params


