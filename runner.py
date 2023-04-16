import os
import threading
import tkinter as tk
from tkinter import messagebox
from app import FaceID


# Pre-run the bash script to set up the port links
try:
    os.system("sudo ln -s /dev/serial/by-id/usb-Arduino__www.arduino.cc__0043_751303038353512032E0-if00 /dev/arduino")
    os.system(
        "sudo ln -s /dev/serial/by-id/usb-Intel_Intel_F450_00.00.01-if02 /dev/cam")
except Exception as e:
    error_message = f"An error occurred: {str(e)}"
    messagebox.showerror(title="Error", message=error_message)


# Create the Tkinter app
root = tk.Tk()
app = FaceID(root)

# Start ultrasonic detection thread
ultrasonic_thread = threading.Thread(target=app.start_ultrasonic_detection)
ultrasonic_thread.start()

# Start the Tkinter main loop
root.mainloop()
