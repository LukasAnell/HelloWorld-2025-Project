import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
from tkinterdnd2 import DND_FILES, TkinterDnD
import fitz  # PyMuPDF

# ===== GLOBAL SETTINGS =====
global_img_ref = None
MAX_WIDTH, MAX_HEIGHT = 500, 300
header_font = ('Roboto', 22, 'bold')
desc_font = ('Roboto', 12)
label_font = ('Roboto', 16, 'bold')
sub_font = ('Roboto', 11)
button_font = ('Roboto', 13, 'bold')

# Softer Aqua Theme Colors
primary_color = "#66D2FF"      # lighter aqua blue
light_bg = "#DFF6FF"           # very light background
alt_bg = "#E8FBFF"             # lighter aqua for panels
divider_color = "#F2FDFF"      # softest blue divider
hover_color = "#66D2FF"        # hover with primary
button_color = "#66D2FF"       # main button color
text_secondary = "#6699AA"     # gentle darker text

# ===== FIRST WINDOW =====
def open_first_window():
    root = TkinterDnD.Tk()
    root.title("AI Resume Reviewer")
    root.geometry("950x650")
    root.minsize(850, 600)
    root.configure(bg=light_bg)

    # ---- Import Functions ----
    def import_file():
        file_path = filedialog.askopenfilename(
            title="Select a PDF File",
            filetypes=(("PDF files", "*.pdf"), ("All files", "*.*"))
        )
        if file_path:
            open_pdf_viewer(file_path, root)

    def handle_drag_and_drop(event):
        file_paths = root.tk.splitlist(event.data)
        if file_paths:
            file_path = file_paths[0]
            if file_path.lower().endswith('.pdf'):
                open_pdf_viewer(file_path, root)
            else:
                messagebox.showerror("Invalid File", "Please drop a PDF file.")

    # ---- Header ----
    header_frame = tk.Frame(root, bg=light_bg)
    header_frame.pack(side="top", fill="x", pady=10)
    tk.Label(header_frame, text="Welcome to AI Resume Reviewer",
             font=header_font, bg=light_bg, fg=primary_color).pack(pady=(5, 2))
    tk.Label(header_frame, text="Upload or drop your resume to: "
                                "\n✓ Review formatting  ✓ Highlight strengths "
                                "\n✓ Suggest improvements  ✓ Ensure ATS compatibility",
             font=desc_font, bg=light_bg, fg=text_secondary, justify="center").pack()

    # ---- Main Container ----
    main_frame = tk.Frame(root, bg=alt_bg)
    main_frame.pack(fill="both", expand=True, padx=20, pady=10)
    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_columnconfigure(1, weight=0)
    main_frame.grid_columnconfigure(2, weight=1)
    main_frame.grid_rowconfigure(0, weight=1)

    # ---- Left Pane ----
    left_pane = tk.Frame(main_frame, bg=alt_bg)
    left_pane.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    left_pane.grid_rowconfigure(0, weight=1)
    left_pane.grid_columnconfigure(0, weight=1)

    center_frame = tk.Frame(left_pane, bg=alt_bg)
    center_frame.grid(sticky="nsew")
    center_frame.grid_rowconfigure(0, weight=1)
    center_frame.grid_rowconfigure(3, weight=1)
    center_frame.grid_columnconfigure(0, weight=1)

    global global_img_ref
    try:
        img = Image.open("image-removebg-preview.png")
        img.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.LANCZOS)
        global_img_ref = ImageTk.PhotoImage(img)
        image_label = tk.Label(center_frame, image=global_img_ref, bg=alt_bg)
    except FileNotFoundError:
        image_label = tk.Label(center_frame, text="Drag & Drop Resume Here", font=label_font,
                               fg=primary_color, bg=alt_bg, width=50, height=12)
    image_label.grid(row=1, column=0, pady=(0, 5))
    tk.Label(center_frame, text="Drag and Drop", font=header_font,
             bg=alt_bg, fg=primary_color).grid(row=2, column=0, pady=(0, 0))
    image_label.drop_target_register(DND_FILES)
    image_label.dnd_bind("<<Drop>>", handle_drag_and_drop)

    # ---- Separator ----
    separator = tk.Canvas(main_frame, width=2, bg=divider_color, highlightthickness=0)
    separator.grid(row=0, column=1, sticky="ns", pady=10)

    # ---- Right Pane ----
    right_pane = tk.Frame(main_frame, bg=alt_bg)
    right_pane.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)
    right_pane.grid_rowconfigure(0, weight=1)
    right_pane.grid_rowconfigure(4, weight=1)
    right_pane.grid_columnconfigure(0, weight=1)
    tk.Label(right_pane, text="Or choose a file", font=label_font,
             fg=primary_color, bg=alt_bg).grid(row=1, column=0, pady=(0, 10))
    tk.Label(right_pane, text="Supported: PDF only", font=sub_font,
             fg=text_secondary, bg=alt_bg).grid(row=2, column=0, pady=(0, 20))
    import_btn = tk.Button(
        right_pane, text="Browse Files", command=import_file, font=button_font,
        bg=button_color, fg="white", activebackground=hover_color, activeforeground="white",
        relief="flat", padx=25, pady=12
    )
    import_btn.grid(row=3, column=0, pady=20)

    root.mainloop()


# ===== PDF VIEWER =====
def open_pdf_viewer(file_path, parent_root):
    parent_root.destroy()
    viewer = tk.Tk()
    viewer.title("PDF Viewer")
    viewer.geometry("1000x700")
    viewer.minsize(1000, 600)
    viewer.configure(bg=light_bg)

    # ---- Canvas + Scrollbar ----
    canvas_frame = tk.Frame(viewer)
    canvas_frame.pack(fill="both", expand=True)
    canvas = tk.Canvas(canvas_frame, bg=light_bg, highlightthickness=0)
    scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    scrollable_frame = tk.Frame(canvas, bg=alt_bg)
    frame_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="n")

    # ---- Render PDF ----
    doc = fitz.open(file_path)
    viewer.pdf_images = []

    for i, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img_tk = ImageTk.PhotoImage(img)
        viewer.pdf_images.append(img_tk)

        page_frame = tk.Frame(scrollable_frame, bg=alt_bg)
        page_frame.pack(pady=10, fill="both")
        tk.Label(page_frame, image=img_tk, bg=alt_bg).pack(pady=5)

        # Add separator between pages
        if i < len(doc):
            separator = tk.Frame(scrollable_frame, height=5, bg=divider_color)
            separator.pack(fill="x", pady=5)

    # ---- Scroll & Center ----
    def update_scroll_region(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))
    scrollable_frame.bind("<Configure>", update_scroll_region)

    def recenter_frame(event):
        canvas.itemconfig(frame_window, width=event.width)
    canvas.bind("<Configure>", recenter_frame)

    def on_mousewheel(event):
        current = canvas.yview()
        if (event.delta < 0 and current[1] < 1.0) or (event.delta > 0 and current[0] > 0.0):
            canvas.yview_scroll(-1 * int(event.delta / 120), "units")
    canvas.bind_all("<MouseWheel>", on_mousewheel)

    # ---- Bottom Buttons ----
    btn_frame = tk.Frame(viewer, bg=light_bg)
    btn_frame.pack(fill="x", pady=10)

    def analyze_file():
        messagebox.showinfo("Analysis", f"Analyzing {file_path}...")
        viewer.destroy()
        open_first_window()

    def go_back():
        viewer.destroy()
        open_first_window()

    tk.Button(btn_frame, text="Analyze This File", bg=button_color, fg="white",
              activebackground=hover_color, activeforeground="white",
              font=("Roboto", 12, "bold"), relief="flat", padx=15, pady=10,
              command=analyze_file).pack(side="left", padx=20)
    tk.Button(btn_frame, text="Back", bg=divider_color, fg=primary_color,
              font=("Roboto", 12, "bold"), relief="flat", padx=15, pady=10,
              command=go_back).pack(side="right", padx=20)

    viewer.mainloop()


# ---- Start App ----
open_first_window()
