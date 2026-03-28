# image2scan

`image2scan` is a graphical desktop application that converts ordinary photos of documents into clean, "scanned-looking" images. It achieves this by applying a local adaptive thresholding (LAT) algorithm similar to ImageMagick's `-lat` command, followed by morphological operations to clean up the result.

## Features

*   **Batch Processing:** Process multiple images from an input folder at once.
*   **"Scanned Document" Effect:** Uses Local Adaptive Thresholding to clean up uneven lighting and background noise, isolating text and line art.
*   **Adjustable Settings:**
    *   **Block Size:** The size of the local neighborhood used to calculate the threshold. Larger values preserve larger dark areas.
    *   **Offset %:** Adjusts the threshold level. Higher values make the output lighter, removing more noise but potentially thinning out text.
    *   **JPEG Quality:** Controls the compression quality of the output files.
*   **Modern GUI:** Built with `customtkinter` for a sleek, dark-themed user interface.

## Prerequisites

Ensure you have Python installed. The required libraries are listed in `requirements.txt`.

## Installation

1.  Clone or download this repository.
2.  Install the required dependencies using pip:

```bash
pip install -r requirements.txt
```

## Usage

1.  Run the application:

```bash
python image2scan.py
```

2.  **Select Input Folder:** Click "Browse" next to "Input Folder" and select the directory containing the images you want to process (supported formats: JPG, JPEG, PNG).
3.  **Select Output Folder:** By default, it will suggest a `Scans` subfolder in your input directory. You can change this by clicking the corresponding "Browse" button.
4.  **Adjust Settings (Optional):**
    *   Modify **Block Size**, **Offset**, and **JPEG Quality** using the sliders to fine-tune the output.
5.  **Scan:** Click the "Scan" button to start the batch processing. Progress will be displayed in the bar at the bottom.

## How it Works

The core image processing pipeline relies on `numpy`, `scipy`, and `Pillow` (PIL):

1.  **Grayscale Conversion:** The image is first converted to grayscale.
2.  **Local Adaptive Thresholding (LAT):** A box-mean filter (`scipy.ndimage.uniform_filter`) calculates the local average brightness around each pixel. The pixel is kept black only if it's darker than its local average minus the specified offset. This effectively removes shadows and uneven lighting.
3.  **Morphological Closing:** A combination of maximum and minimum filters (`scipy.ndimage.maximum_filter` and `minimum_filter`) is applied to fill in tiny white holes within dark regions (like text strokes), resulting in a more solid and legible output.

## Building an Executable

You can build a standalone executable using PyInstaller (included in `requirements.txt`):

```bash
pyinstaller image2scan.spec
```
The executable will be located in the `dist` directory.