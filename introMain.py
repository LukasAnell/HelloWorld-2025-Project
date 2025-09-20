import tkinter as tk
import os
import sys


class ResumeReviewerApp:
    """
    A simple Tkinter application that displays a welcome message with a fade-in effect.
    """

    def __init__(self, root):
        """
        Initializes the application window and its widgets.
        """
        self.root = root
        self.root.title("Resume Reviewer")
        self.root.geometry("800x400")  # Made the window bigger
        self.root.configure(bg='#f0f0f0')  # A light gray background
        self.root.resizable(False, False)
        self.state = 0  # 0 for initial screen, 1 for info screen

        # Determine the correct application data folder based on the OS
        self.config_path = self.get_config_path()
        self.config_file_path = os.path.join(self.config_path, "AlreadyLoaded.txt")

        # Center the window on the screen
        self.center_window()

        # --- Widgets ---
        # Use a central frame for easy centering of all content
        self.main_frame = tk.Frame(root, bg=self.root.cget('bg'))
        self.main_frame.pack(expand=True)

        # Check if the user has been here before
        if not self.check_already_loaded():
            self.setup_initial_ui()
            self.start_initial_animations()
        else:
            self.setup_final_ui()

    def get_config_path(self):
        """Gets the appropriate cross-platform path for app data."""
        app_name = "ResumeReviewer"
        if sys.platform == 'win32':
            # Windows
            path = os.path.join(os.getenv('APPDATA'), app_name)
        elif sys.platform == 'darwin':
            # macOS
            path = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', app_name)
        else:
            # Linux and other Unix-like OSes
            path = os.path.join(os.path.expanduser('~'), '.config', app_name)

        # Ensure the directory exists
        os.makedirs(path, exist_ok=True)
        return path

    def check_already_loaded(self):
        """Checks for AlreadyLoaded.txt and its content."""
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, "r") as f:
                    content = f.read().strip()
                    if content == "true":
                        return True
            except IOError:
                # Handle cases where the file might be inaccessible
                return False
        return False

    def setup_initial_ui(self):
        """Creates all widgets for the initial animated sequence."""
        initial_fg = self.root.cget('bg')

        self.header_label = tk.Label(
            self.main_frame, text="Welcome to Resume Reviewer!", font=("Roboto", 26, "bold"),
            fg=initial_fg, bg=self.root.cget('bg')
        )
        self.header_label.pack(pady=(10, 20), padx=20)

        self.text_label = tk.Label(
            self.main_frame,
            text="Our AI model will apply the highest standards to your resume\nand help you improve it beyond a basic draft",
            font=("Roboto", 14), fg=initial_fg, bg=self.root.cget('bg'), justify=tk.CENTER
        )
        self.text_label.pack(pady=10, padx=20)

        self.info_label = tk.Label(
            self.main_frame,
            text="Did you know? Recruiters spend only 6–9 seconds scanning a resume before making a decision.\n\n"
                 "Even before the recruiter sees your resume, it may pass through an Applicant Tracking System (ATS). "
                 "That’s why we focus on helping your content stand out, "
                 "making sure your experiences and achievements are highlighted in a way that captures attention.",
            font=("Roboto", 14), fg=initial_fg, bg=self.root.cget('bg'), justify=tk.CENTER, wraplength=700
        )

        self.continue_button = tk.Button(
            self.main_frame, text="Continue >", font=("Roboto", 14, "bold"), fg=initial_fg, bg=self.root.cget('bg'),
            activebackground=self.root.cget('bg'), activeforeground='#000000', bd=0, highlightthickness=0,
            cursor="hand2", command=self.on_continue_click
        )
        self.continue_button.pack(pady=20)

    def start_initial_animations(self):
        """Schedules the fade-in animations for the initial UI."""
        self.fade_in(self.header_label, 240)
        self.root.after(1000, lambda: self.fade_in(self.text_label, 240))
        self.root.after(2000, lambda: self.fade_in(self.continue_button, 240))

    def setup_final_ui(self):
        """Clears the UI, effectively skipping the animations."""
        # This method is called when AlreadyLoaded.txt is "true"
        # It clears the frame for the next step of the application
        self.clear_all_widgets()
        # You could add new widgets here for the next stage of your app
        tk.Label(self.main_frame, text="Ready to review your resume.", font=("Roboto", 18),
                 bg=self.root.cget('bg')).pack(pady=20)

    def on_continue_click(self):
        """Handles the click event for the continue button, based on the current state."""
        self.continue_button.config(state=tk.DISABLED)

        if self.state == 0:
            def after_fade_out():
                self.text_label.pack_forget()
                # Pack the new info label *before* the continue button widget
                self.info_label.pack(pady=10, padx=20, before=self.continue_button)
                self.fade_in(self.info_label, 240)
                self.root.after(500, lambda: self.fade_in(self.continue_button, 240,
                                                          callback=lambda: self.continue_button.config(
                                                              state=tk.NORMAL)))
                self.state = 1

            self.fade_out(self.text_label, 0)
            self.fade_out(self.continue_button, 0, callback=after_fade_out)

        elif self.state == 1:
            def after_fade_out():
                self.clear_all_widgets()
                self.write_load_file()
                self.setup_final_ui()  # Go to the final state

            # Fade out everything
            self.fade_out(self.header_label, 0)
            self.fade_out(self.info_label, 0)
            self.fade_out(self.continue_button, 0, callback=after_fade_out)

    def write_load_file(self):
        """Creates or overwrites AlreadyLoaded.txt with 'true'."""
        try:
            # The directory is already created in __init__
            with open(self.config_file_path, "w") as f:
                f.write("true")
        except IOError as e:
            print(f"Error writing to file: {e}")

    def clear_all_widgets(self):
        """Destroys all widgets within the main_frame."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def center_window(self):
        """Centers the main window on the user's screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def fade_in(self, widget, current_shade, callback=None):
        """
        Gradually changes the widget's foreground color to black.
        """
        if current_shade >= 0:
            hex_color = f'#{current_shade:02x}{current_shade:02x}{current_shade:02x}'
            widget.config(fg=hex_color)
            self.root.after(15, lambda: self.fade_in(widget, current_shade - 5, callback))
        elif callback:
            callback()

    def fade_out(self, widget, current_shade, callback=None):
        """
        Gradually changes the widget's foreground color to match the background.
        """
        if current_shade <= 240:  # 240 is the shade of the background #f0f0f0
            hex_color = f'#{current_shade:02x}{current_shade:02x}{current_shade:02x}'
            widget.config(fg=hex_color)
            self.root.after(10, lambda: self.fade_out(widget, current_shade + 5, callback))
        elif callback:
            callback()


def main():
    """
    Creates the root window and starts the Tkinter event loop.
    """
    root = tk.Tk()
    app = ResumeReviewerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

