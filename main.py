import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from PIL import Image, ImageTk
from tkinterdnd2 import DND_FILES, TkinterDnD

# The main application window
# We now initialize the main window using TkinterDnD to enable drag and drop
root = TkinterDnD.Tk()
root.title("AI Resume Reviewer")
root.geometry("800x600")
root.configure(bg="#F5F5F5")
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(0, weight=1)

# Global variable to hold the image reference and prevent garbage collection
global_img_ref = None

# Create a main frame to hold all content and use grid for a cleaner layout
main_frame = tk.Frame(root, bg="#FFFFFF", padx=20, pady=20)
main_frame.grid(row=0, column=0, sticky='nsew')
main_frame.grid_columnconfigure(0, weight=1)
main_frame.grid_rowconfigure(0, weight=1)

# Style configuration using Roboto font
label_font = ('Roboto', 18, 'bold')
button_font = ('Roboto', 14)
button_bg = '#1abc9c'
button_fg = '#ffffff'
button_active_bg = '#2ecc71'


# Function to handle file import
def import_file():
    file_path = filedialog.askopenfilename(
        initialdir="/",
        title="Select a PDF File",
        filetypes=(("PDF files", "*.pdf"), ("all files", "*.*"))
    )
    if file_path:
        messagebox.showinfo("File Selected", f"You selected the file:\n{file_path}")
    else:
        messagebox.showinfo("No Selection", "No file was selected.")


# Function to handle drag-and-drop
def handle_drag_and_drop(event):
    # The event data from tkinterdnd2 contains the file path(s).
    # It might contain multiple file paths if multiple files are dropped.
    file_paths = root.tk.splitlist(event.data)

    if file_paths:
        # For this app, we'll just handle the first dropped file
        file_path = file_paths[0]
        # Check if the dropped file has a .pdf extension
        if file_path.lower().endswith('.pdf'):
            messagebox.showinfo("File Dropped", f"You dropped the file:\n{file_path}")
        else:
            messagebox.showerror("Invalid File", "Please drop a PDF file.")
    else:
        messagebox.showinfo("No Selection", "No file was selected.")


# Create a frame to hold the left and right sections
content_frame = tk.Frame(main_frame, bg="#FFFFFF")
content_frame.grid(row=0, column=0, sticky='nsew')
content_frame.grid_columnconfigure(0, weight=1)
content_frame.grid_columnconfigure(1, weight=0)
content_frame.grid_columnconfigure(2, weight=1)
content_frame.grid_rowconfigure(0, weight=1)

# Left pane for the image and drag-and-drop area
left_pane = tk.Frame(content_frame, bg="#FFFFFF")
left_pane.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)
left_pane.grid_rowconfigure(0, weight=1)
left_pane.grid_columnconfigure(0, weight=1)

# Load and display the PNG image
try:
    # global global_img_ref
    img = Image.open("DragAndDrop.png")
    img = img.resize((300, 300), Image.LANCZOS)
    global_img_ref = ImageTk.PhotoImage(img)
    image_label = tk.Label(left_pane, image=global_img_ref, bg="#FFFFFF")
    image_label.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
except FileNotFoundError:
    messagebox.showerror("Error", "DragAndDrop.png not found. Please ensure the file is in the same directory.")
    image_label = tk.Label(left_pane, text="Image Not Found", font=('Roboto', 12), fg="#2c3e50", bg="#FFFFFF")
    image_label.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

# Bind the drag-and-drop event to the image_label widget using tkinterdnd2
image_label.drop_target_register(DND_FILES, DND_FILES)
image_label.dnd_bind('<<Drop>>', handle_drag_and_drop)

# Vertical separator line
separator_canvas = tk.Canvas(content_frame, width=2, bg="#2c3e50", highlightthickness=0)
separator_canvas.create_line(1, 40, 1, 520, fill="#2c3e50", width=2)
separator_canvas.grid(row=0, column=1, sticky='ns')

# Right pane for "Or choose a file" and button
right_pane = tk.Frame(content_frame, bg="#FFFFFF")
right_pane.grid(row=0, column=2, sticky='nsew', padx=20, pady=20)
right_pane.grid_columnconfigure(0, weight=1)
right_pane.grid_rowconfigure(0, weight=1)
right_pane.grid_rowconfigure(1, weight=0)
right_pane.grid_rowconfigure(2, weight=1)

# "Or choose a file" text
text_label = tk.Label(right_pane, text="Or choose a file", font=label_font, fg="#2c3e50", bg="#FFFFFF")
text_label.grid(row=1, column=0)

# The file import button
import_button = tk.Button(right_pane, text="Browse your files", command=import_file,
                          font=button_font, bg=button_bg, fg=button_fg,
                          activebackground=button_active_bg, relief=tk.FLAT)
import_button.grid(row=2, column=0, pady=20)

# Start the Tkinter event loop
root.mainloop()
