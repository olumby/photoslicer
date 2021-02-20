import os
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from PIL import Image, ImageTk
from autoslicer import Autoslicer, AutoslicerParams
from slicingcanvas import SlicingCanvas, PhotoSlice


class MyFrame(tk.Frame):

    def enable(self, state='normal'):

        def set_status(widget):
            if widget.winfo_children:
                for child in widget.winfo_children():
                    child_type = child.winfo_class()
                    if child_type not in ('Frame', 'Labelframe'):
                        child['state'] = state
                    set_status(child)

        set_status(self)

    def disable(self):
        self.enable('disabled')


class PhotoSlicer(MyFrame):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

        self.winfo_toplevel().title("PhotoSlicer")
        self.source_images = []
        self.source_index = None

        tk.Grid.rowconfigure(self, 0, weight=1)
        tk.Grid.columnconfigure(self, 1, weight=1)

        # Left side control panel
        self.frame_controls = MyFrame(self, borderwidth=5)
        self.frame_controls.grid(row=0, column=0, sticky="nsw")

        # Set defaults
        row = 0
        self.button_setdef = tk.Button(self.frame_controls, text="Set defaults", command=self.set_default_parameters)
        self.button_setdef.grid(row=row, column=0, sticky="we")

        # Generate controls from parameters
        row += 1
        self.params = AutoslicerParams()
        for pi in self.params.__dict__:
            p = getattr(self.params, pi)
            tk.Label(self.frame_controls, text=p.label).grid(row=row, column=0, sticky="w")
            row += 1
            p.control = tk.Spinbox(self.frame_controls, from_=p.min, to=p.max, increment=p.step, textvariable=p.tk_var)
            p.control.grid(row=row, column=0, sticky="we")
            row += 1

        row += 1
        self.button_update = tk.Button(self.frame_controls, text="Detect pictures", command=self.update_preview)
        self.button_update.grid(row=row, column=0, sticky="we")

        row += 1
        self.button_addbox = tk.Button(self.frame_controls, text="Add manual bounding box", command=self.add_box)
        self.button_addbox.grid(row=row, column=0, sticky="we")

        self.status_text = tk.StringVar(self)
        self.statuslabel = tk.Label(self, textvariable=self.status_text, anchor='w',
                                    width=1, relief=tk.SUNKEN).grid(row=1, column=0, columnspan=2, sticky='swe')

        self.status_text.set("Ready.")

        # Slicing canvas
        self.slicing_canvas = SlicingCanvas(self)
        self.slicing_canvas.grid(row=0, column=1, sticky='nswe')
        self.slicing_canvas.update()
        self.autoslicer = Autoslicer(self.params)

    def update_statusbar(self, text):
        self.status_text.set(text)
        self.update()

    def load_image(self, move_index=0):

        if len(self.source_images) == 0:
            self.open_directory()

        if self.source_index is None:
            self.source_index = 0
        else:
            self.source_index += move_index

            if self.source_index < 0:
                self.source_index = 0
                messagebox.showwarning(title="No previous", message="This is the first image")
                return

            if self.source_index >= len(self.source_images):
                self.source_index = len(self.source_images) - 1
                messagebox.showwarning(title="No next", message="This is the last image")
                return

        self.disable()
        self.autoslicer.load_image(self.source_images[self.source_index])
        if self.autoslicer.image_loaded():
            self.update_preview()
            self.update_statusbar("Loaded " + self.source_images[self.source_index])
        self.enable()

    def update_preview(self):
        if not self.autoslicer.image_loaded():
            return

        self.disable()
        bbxs, image = self.autoslicer.autodetect_slices(self.update_statusbar)
        self.slicing_canvas.set_image(Image.fromarray(image))
        self.slicing_canvas.update_bboxes(bbxs)
        self.slicing_canvas.update_view()
        self.status_text.set("Ready.")
        self.enable()

    def save_all(self):

        if self.source_images is None or self.source_index < 0:
            messagebox.showwarning(title="No image loaded", message="Load an image first")
            return

        self.disable()

        i = -1
        for slice in self.slicing_canvas.slices:
            if not slice.locked:
                continue

            i += 1
            outname = self.source_images[self.source_index].replace(".png", "_" + f'{i:03}' + ".png", 1)
            self.autoslicer.save_slice(slice.bbox, outname)
            self.update_statusbar("Saved " + outname)

        if i < 0:
            messagebox.showwarning(title="No locked slice to save!",
                                   message="To lock one slice, click on its central number")
        else:
            i += 1
            messagebox.showinfo(title="Slices saved", message=f"{i} slices have been saved")

        self.enable()

    def not_implemented(self):
        messagebox.showwarning(title="Not implemented", message="Sorry, not there yet")
        return

    def abort_processing(self):
        self.autoslicer.abort_operation()

    def add_box(self):
        new_slice = PhotoSlice([[10, 10], [200, 10], [200, 200], [10, 200]])
        new_slice.toggle_locked()
        self.slicing_canvas.add_bbox(new_slice)

    def open_directory(self, basedir=None):
        if basedir is None:
            basedir = filedialog.askdirectory()

        if basedir is not None:
            for file in os.listdir(basedir):
                if file.endswith(".png"):
                    self.source_images.append(os.path.join(basedir, file))

        if len(self.source_images) == 0:
            messagebox.showwarning(title="No images", message="No images available")
        else:
            self.load_image(0)

    def next_image(self):
        self.load_image(1)

    def prev_image(self):
        self.load_image(-1)

    def set_default_parameters(self):
        for pi in self.params.__dict__:
            p = getattr(self.params, pi)
            p.reset()
        self.update()
        return

    def test_disable(self):
        self.disable()

    def test_enable(self):
        self.enable()
