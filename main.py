import tkinter as tk
from tkinter import messagebox

# The main application window
root = tk.Tk()
root.title("Main Window")
root.geometry("400x300")
root.configure(bg="#2c3e50")

# Create a modern-looking frame for content with some padding and rounded corners
main_frame = tk.Frame(root, bg="#34495e", padx=20, pady=20)
main_frame.pack(expand=True, padx=20, pady=20, fill='both')

# Style configuration for a clean, modern look
label_font = ('Inter', 14, 'bold')
button_font = ('Inter', 12)
button_bg = '#1abc9c'
button_fg = '#ffffff'
button_active_bg = '#16a085'


# Create a new Toplevel window (this is how you make a new window)
def open_new_window():
    # Use a try-except block to handle potential issues with opening multiple windows
    try:
        # Create a new Toplevel window instance
        new_window = tk.Toplevel(root)
        new_window.title("New Window")
        new_window.geometry("300x200")
        new_window.configure(bg="#34495e")

        # Use a label to provide a title for the new window
        label_text = "This is a new window!"
        label = tk.Label(new_window, text=label_text, font=label_font, fg="#ecf0f1", bg="#34495e")
        label.pack(pady=20)

        # A button to close the new window
        close_button = tk.Button(new_window, text="Close Window", command=new_window.destroy,
                                 font=button_font, bg=button_bg, fg=button_fg,
                                 activebackground=button_active_bg, relief=tk.FLAT)
        close_button.pack(pady=10)

    except Exception as e:
        messagebox.showerror("Error", f"Could not open new window: {e}")


# Create a button on the main window to open the new window
open_button = tk.Button(main_frame, text="Open New Window", command=open_new_window,
                        font=button_font, bg=button_bg, fg=button_fg,
                        activebackground=button_active_bg, relief=tk.FLAT)
open_button.pack(pady=20)

# Start the Tkinter event loop
# This keeps the window open and responsive to user actions
root.mainloop()
