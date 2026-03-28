import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading

import numpy as np
from PIL import Image
from scipy.ndimage import uniform_filter, minimum_filter, maximum_filter

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")

# Defaults matching the original ImageMagick pipeline
DEFAULT_BLOCK_SIZE = 41
DEFAULT_OFFSET_PCT = 10
DEFAULT_QUALITY = 95


class Image2ScanApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("image2scan")
        self.geometry("500x480")
        self.resizable(False, False)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # --- Input folder ---
        ctk.CTkLabel(self, text="Input Folder:").pack(padx=20, pady=(20, 0), anchor="w")

        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(padx=20, fill="x")

        self.input_var = ctk.StringVar()
        ctk.CTkEntry(input_frame, textvariable=self.input_var) \
            .pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(input_frame, text="Browse", width=80, command=self.browse_input) \
            .pack(side="right")

        # --- Output folder ---
        ctk.CTkLabel(self, text="Output Folder:").pack(padx=20, pady=(10, 0), anchor="w")

        output_frame = ctk.CTkFrame(self, fg_color="transparent")
        output_frame.pack(padx=20, fill="x")

        self.output_var = ctk.StringVar()
        ctk.CTkEntry(output_frame, textvariable=self.output_var) \
            .pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(output_frame, text="Browse", width=80, command=self.browse_output) \
            .pack(side="right")

        # --- Settings ---
        settings_label = ctk.CTkLabel(self, text="Settings", font=ctk.CTkFont(size=14, weight="bold"))
        settings_label.pack(padx=20, pady=(15, 5), anchor="w")

        # Block Size
        self.block_size_var = ctk.IntVar(value=DEFAULT_BLOCK_SIZE)
        self.block_size_label = ctk.CTkLabel(self, text=f"Block Size: {DEFAULT_BLOCK_SIZE}")
        self.block_size_label.pack(padx=20, anchor="w")
        ctk.CTkSlider(self, from_=5, to=101, number_of_steps=48,
                      variable=self.block_size_var,
                      command=self.on_block_size_change) \
            .pack(padx=20, fill="x")

        # Offset %
        self.offset_var = ctk.IntVar(value=DEFAULT_OFFSET_PCT)
        self.offset_label = ctk.CTkLabel(self, text=f"Offset: {DEFAULT_OFFSET_PCT}%")
        self.offset_label.pack(padx=20, pady=(8, 0), anchor="w")
        ctk.CTkSlider(self, from_=0, to=30, number_of_steps=30,
                      variable=self.offset_var,
                      command=self.on_offset_change) \
            .pack(padx=20, fill="x")

        # JPEG Quality
        self.quality_var = ctk.IntVar(value=DEFAULT_QUALITY)
        self.quality_label = ctk.CTkLabel(self, text=f"JPEG Quality: {DEFAULT_QUALITY}")
        self.quality_label.pack(padx=20, pady=(8, 0), anchor="w")
        ctk.CTkSlider(self, from_=50, to=100, number_of_steps=50,
                      variable=self.quality_var,
                      command=self.on_quality_change) \
            .pack(padx=20, fill="x")

        # --- Progress bar ---
        self.progress = ctk.CTkProgressBar(self)
        self.progress.pack(padx=20, pady=(15, 0), fill="x")
        self.progress.set(0)

        self.status_label = ctk.CTkLabel(self, text="Ready")
        self.status_label.pack(padx=20, pady=(5, 0), anchor="w")

        # --- Scan button ---
        self.scan_btn = ctk.CTkButton(self, text="Scan", height=40,
                                      command=self.start_scan)
        self.scan_btn.pack(padx=20, pady=15, fill="x")

    # --- Slider callbacks ---

    def on_block_size_change(self, value):
        v = int(value)
        if v % 2 == 0:  # force odd
            v += 1
        self.block_size_var.set(v)
        self.block_size_label.configure(text=f"Block Size: {v}")

    def on_offset_change(self, value):
        v = int(value)
        self.offset_label.configure(text=f"Offset: {v}%")

    def on_quality_change(self, value):
        v = int(value)
        self.quality_label.configure(text=f"JPEG Quality: {v}")

    # --- Folder browsing ---

    def browse_input(self):
        folder = filedialog.askdirectory(title="Select folder with images")
        if folder:
            self.input_var.set(folder)
            if not self.output_var.get():
                self.output_var.set(os.path.join(folder, "Scans"))

    def browse_output(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_var.set(folder)

    def get_images(self, folder):
        return [f for f in os.listdir(folder)
                if f.lower().endswith(IMAGE_EXTENSIONS)]

    # --- Scan logic ---

    def start_scan(self):
        input_folder = self.input_var.get()
        output_folder = self.output_var.get()

        if not input_folder or not os.path.isdir(input_folder):
            messagebox.showerror("Error", "Please select a valid input folder.")
            return

        images = self.get_images(input_folder)
        if not images:
            messagebox.showwarning("No Images", "No JPG/PNG images found in the selected folder.")
            return

        # Read settings before spawning thread
        block_size = self.block_size_var.get()
        offset_pct = self.offset_var.get()
        quality = self.quality_var.get()

        self.scan_btn.configure(state="disabled")
        self.progress.set(0)
        threading.Thread(
            target=self.run_scan,
            args=(input_folder, output_folder, images, block_size, offset_pct, quality),
            daemon=True,
        ).start()

    @staticmethod
    def process_image(input_path, output_path, block_size=41, offset_pct=10, quality=95):
        """Convert an image to a scanned-document look using local adaptive thresholding.

        Uses a box-mean filter (uniform_filter) to match ImageMagick's -lat behavior,
        then applies morphological closing to fill small white holes inside dark regions.
        """
        img = Image.open(input_path).convert("L")
        arr = np.array(img, dtype=np.float64)

        # Box mean over block_size window — matches ImageMagick -lat
        local_mean = uniform_filter(arr, size=block_size)
        offset = (offset_pct / 100.0) * 255
        binary = ((arr > local_mean - offset) * 255).astype(np.uint8)

        # Morphological closing (dilate then erode) to fill small white holes in dark areas
        binary = maximum_filter(binary, size=3)
        binary = minimum_filter(binary, size=3)

        Image.fromarray(binary).save(output_path, "JPEG", quality=quality)

    def run_scan(self, input_folder, output_folder, images, block_size, offset_pct, quality):
        os.makedirs(output_folder, exist_ok=True)
        total = len(images)

        for i, filename in enumerate(images):
            self.update_status(f"Processing {filename}  ({i + 1}/{total})")
            input_path = os.path.join(input_folder, filename)
            name = os.path.splitext(filename)[0]
            output_path = os.path.join(output_folder, f"{name}_scan.jpg")

            try:
                self.process_image(input_path, output_path, block_size, offset_pct, quality)
            except Exception as e:
                self.update_status(f"Error processing {filename}")
                self.after(0, lambda fn=filename, err=e:
                           messagebox.showerror("Error", f"Failed on {fn}:\n{err}"))
                break

            self.update_progress((i + 1) / total)

        self.update_status(f"Done — {total} images processed")
        self.after(0, lambda: self.scan_btn.configure(state="normal"))

    def update_progress(self, value):
        self.after(0, lambda: self.progress.set(value))

    def update_status(self, text):
        self.after(0, lambda: self.status_label.configure(text=text))


if __name__ == "__main__":
    app = Image2ScanApp()
    app.mainloop()
