import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
from tkinterdnd2 import DND_FILES, TkinterDnD

# Main application window
root = TkinterDnD.Tk()
root.title("AI Resume Reviewer")
root.geometry("950x650")
root.configure(bg="#f0f4f8")
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(0, weight=1)

global_img_ref = None  # Prevent garbage collection

# Fonts & Colors
header_font = ('Roboto', 22, 'bold')
desc_font = ('Roboto', 12)
label_font = ('Roboto', 16, 'bold')
sub_font = ('Roboto', 11)
button_font = ('Roboto', 13, 'bold')

primary_color = "#2c3e50"   # Dark Blue-Grey
accent_color = "#16a085"    # Teal
accent_hover = "#1abc9c"    # Light Teal
light_bg = "#ffffff"
divider_color = "#dcdde1"

# File Import Function
def import_file():
    file_path = filedialog.askopenfilename(
        title="Select a PDF File",
        filetypes=(("PDF files", "*.pdf"), ("All files", "*.*"))
    )
    if file_path:
        messagebox.showinfo("File Selected", f"You selected:\n{file_path}")

# Drag & Drop Function
def handle_drag_and_drop(event):
    file_paths = root.tk.splitlist(event.data)
    if file_paths:
        file_path = file_paths[0]
        if file_path.lower().endswith('.pdf'):
            messagebox.showinfo("File Dropped", f"You dropped:\n{file_path}")
        else:
            messagebox.showerror("Invalid File", "Please drop a PDF file.")

# ===== HEADER SECTION =====
header_frame = tk.Frame(root, bg="#f0f4f8")
header_frame.pack(side="top", fill="x", pady=15)

header_label = tk.Label(header_frame, text="Welcome to AI Resume Reviewer",
                        font=header_font, bg="#f0f4f8", fg=primary_color)
header_label.pack(pady=(5, 2))

desc_label = tk.Label(header_frame, text="Upload or drop your resume to: "
                                         "\n✓ Review formatting  ✓ Highlight strengths "
                                         "\n✓ Suggest improvements  ✓ Ensure ATS compatibility",
                      font=desc_font, bg="#f0f4f8", fg="#636e72", justify="center")
desc_label.pack()

# ===== MAIN CONTAINER =====
main_frame = tk.Frame(root, bg=light_bg, padx=25, pady=25)
main_frame.pack(fill="both", expand=True, padx=40, pady=(10, 20))
main_frame.grid_columnconfigure(0, weight=1)   # Left pane weight
main_frame.grid_columnconfigure(1, weight=0)   # Separator
main_frame.grid_columnconfigure(2, weight=1)   # Right pane weight
main_frame.grid_rowconfigure(0, weight=1)

# ===== LEFT PANE (Drag & Drop) =====
left_pane = tk.Frame(main_frame, bg=light_bg)
left_pane.grid(row=0, column=0, sticky="nsew", padx=20, pady=10)

# Wrapper frame to center content vertically
center_frame = tk.Frame(left_pane, bg=light_bg)
center_frame.pack(expand=True)  # Vertically center the content

try:
    img = Image.open("DragAndDrop.png")
    img = img.resize((744, 414), Image.LANCZOS)
    global_img_ref = ImageTk.PhotoImage(img)
    image_label = tk.Label(center_frame, image=global_img_ref, bg=light_bg)
    image_label.pack(pady=5)
except FileNotFoundError:
    image_label = tk.Label(center_frame, text="Drag & Drop Resume Here", font=label_font,
                           fg=primary_color, bg="#ecf0f1", width=55, height=15)
    image_label.pack(pady=5)

# Add the "Drag and Drop" label under the image
drag_and_drop_label = tk.Label(center_frame, text="Drag and Drop",
                               font=header_font, bg=light_bg, fg=primary_color)
drag_and_drop_label.pack(pady=(2, 0))

# Enable Drag & Drop
image_label.drop_target_register(DND_FILES)
image_label.dnd_bind("<<Drop>>", handle_drag_and_drop)

# ===== SEPARATOR =====
separator = tk.Canvas(main_frame, width=2, bg=divider_color, highlightthickness=0)
separator.grid(row=0, column=1, sticky="ns", pady=10)

# ===== RIGHT PANE (Choose File) =====
right_pane = tk.Frame(main_frame, bg=light_bg)
right_pane.grid(row=0, column=2, sticky="nsew", padx=20, pady=10)
right_pane.grid_rowconfigure(0, weight=1)
right_pane.grid_rowconfigure(1, weight=0)
right_pane.grid_rowconfigure(2, weight=0)
right_pane.grid_rowconfigure(3, weight=1)

# Label
text_label = tk.Label(right_pane, text="Or choose a file", font=label_font,
                      fg=primary_color, bg=light_bg)
text_label.grid(row=1, column=0, pady=(30, 10))

# Subtext
sub_label = tk.Label(right_pane, text="Supported: PDF only", font=sub_font,
                     fg="#7f8c8d", bg=light_bg)
sub_label.grid(row=2, column=0, pady=(0, 20))

# Browse Button
import_button = tk.Button(right_pane, text="Browse Files", command=import_file,
                          font=button_font, bg="#4285f4", fg="white",
                          activebackground=accent_hover, relief="flat",
                          padx=25, pady=12)
import_button.grid(row=3, column=0, pady=20)

root.mainloop()
