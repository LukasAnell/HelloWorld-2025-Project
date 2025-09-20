import tkinter as tk
from tkinter import messagebox, filedialog
import os
import sys
from PIL import Image, ImageTk
from tkinterdnd2 import DND_FILES, TkinterDnD
import fitz  # PyMuPDF

# ===== GLOBAL SETTINGS (from main.py) =====
# These settings will be used for the main application window after the intro.
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

# ===== MAIN APPLICATION UI FUNCTIONS (from main.py) =====

def open_first_window():
    """
    Creates and displays the main resume reviewer window.
    This is the primary interface for file uploading.
    """
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

    # ---- Left Pane (Drag & Drop) ----
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
        # NOTE: Ensure 'image-removebg-preview.png' is in the same directory
        img = Image.open("image-removebg-preview.png")
        img.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.Resampling.LANCZOS)
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

    # ---- Right Pane (Browse Button) ----
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

def open_pdf_viewer(file_path, parent_root):
    """
    Opens a new window to display the selected PDF file.
    """
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


# ===== INTRODUCTORY UI CLASS (from introMain.py) =====

class ResumeReviewerApp:
    """
    Handles the initial welcome screen with a fade-in effect.
    This screen is only shown on the first launch.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Welcome")
        self.root.geometry("800x400")
        self.root.configure(bg='#f0f0f0')
        self.root.resizable(False, False)
        self.state = 0  # 0 for initial screen, 1 for info screen

        self.config_path = self.get_config_path()
        self.config_file_path = os.path.join(self.config_path, "AlreadyLoaded.txt")
        self.center_window()

        self.main_frame = tk.Frame(root, bg=self.root.cget('bg'))
        self.main_frame.pack(expand=True)

        if not self.check_already_loaded():
            self.setup_initial_ui()
            self.start_initial_animations()
        else:
            self.setup_final_ui()

    def get_config_path(self):
        app_name = "ResumeReviewer"
        if sys.platform == 'win32':
            path = os.path.join(os.getenv('APPDATA'), app_name)
        elif sys.platform == 'darwin':
            path = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', app_name)
        else:
            path = os.path.join(os.path.expanduser('~'), '.config', app_name)
        os.makedirs(path, exist_ok=True)
        return path

    def check_already_loaded(self):
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, "r") as f:
                    return f.read().strip() == "true"
            except IOError:
                return False
        return False

    def setup_initial_ui(self):
        initial_fg = self.root.cget('bg')
        self.header_label = tk.Label(self.main_frame, text="Welcome to Resume Reviewer!", font=("Roboto", 26, "bold"), fg=initial_fg, bg=self.root.cget('bg'))
        self.header_label.pack(pady=(10, 20), padx=20)
        self.text_label = tk.Label(self.main_frame, text="Our AI model will apply the highest standards to your resume\nand help you improve it beyond a basic draft", font=("Roboto", 14), fg=initial_fg, bg=self.root.cget('bg'), justify=tk.CENTER)
        self.text_label.pack(pady=10, padx=20)
        self.info_label = tk.Label(self.main_frame, text="Did you know? Recruiters spend only 6–9 seconds scanning a resume before making a decision.\n\nEven before the recruiter sees your resume, it may pass through an Applicant Tracking System (ATS). That’s why we focus on helping your content stand out, making sure your experiences and achievements are highlighted in a way that captures attention.", font=("Roboto", 14), fg=initial_fg, bg=self.root.cget('bg'), justify=tk.CENTER, wraplength=700)
        self.continue_button = tk.Button(self.main_frame, text="Continue >", font=("Roboto", 14, "bold"), fg=initial_fg, bg=self.root.cget('bg'), activebackground=self.root.cget('bg'), activeforeground='#000000', bd=0, highlightthickness=0, cursor="hand2", command=self.on_continue_click)
        self.continue_button.pack(pady=20)

    def start_initial_animations(self):
        self.fade_in(self.header_label, 240)
        self.root.after(1000, lambda: self.fade_in(self.text_label, 240))
        self.root.after(2000, lambda: self.fade_in(self.continue_button, 240))

    def setup_final_ui(self):
        """
        Destroys the intro window and launches the main application UI.
        This function serves as the transition point.
        """
        self.root.destroy()
        open_first_window()

    def on_continue_click(self):
        self.continue_button.config(state=tk.DISABLED)
        if self.state == 0:
            def after_fade_out():
                self.text_label.pack_forget()
                self.info_label.pack(pady=10, padx=20, before=self.continue_button)
                self.fade_in(self.info_label, 240)
                self.root.after(500, lambda: self.fade_in(self.continue_button, 240, callback=lambda: self.continue_button.config(state=tk.NORMAL)))
                self.state = 1
            self.fade_out(self.text_label, 0)
            self.fade_out(self.continue_button, 0, callback=after_fade_out)
        elif self.state == 1:
            def after_fade_out():
                self.write_load_file()
                self.setup_final_ui()
            self.fade_out(self.header_label, 0)
            self.fade_out(self.info_label, 0)
            self.fade_out(self.continue_button, 0, callback=after_fade_out)

    def write_load_file(self):
        try:
            with open(self.config_file_path, "w") as f:
                f.write("true")
        except IOError as e:
            print(f"Error writing to config file: {e}")

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def fade_in(self, widget, current_shade, callback=None):
        if current_shade >= 0:
            hex_color = f'#{current_shade:02x}{current_shade:02x}{current_shade:02x}'
            widget.config(fg=hex_color)
            self.root.after(15, lambda: self.fade_in(widget, current_shade - 5, callback))
        elif callback:
            callback()

    def fade_out(self, widget, current_shade, callback=None):
        if current_shade <= 240:
            hex_color = f'#{current_shade:02x}{current_shade:02x}{current_shade:02x}'
            widget.config(fg=hex_color)
            self.root.after(10, lambda: self.fade_out(widget, current_shade + 5, callback))
        elif callback:
            callback()

# ===== APPLICATION ENTRY POINT =====

def main():
    """
    Creates the root window for the intro and starts the app.
    """
    root = tk.Tk()
    app = ResumeReviewerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()