import time
import threading

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from rsid_py import FaceAuthenticator


PORT = '/dev/ttyACM0'


class FaceID:
    def __init__(self, master):
        # Set up main window
        self.master = master
        self.master.title("Face ID Access")
        self.master.geometry("{0}x{1}+0+0".format(
            self.master.winfo_screenwidth(), self.master.winfo_screenheight()))

        # Set up header title and count label
        self.header_label = tk.Label(
            self.master, text="DAUST Face ID Access", font=("Arial", 34), padx=20, pady=20)
        self.header_label.pack(side=tk.TOP)

        # Set up count label
        self.count = 0
        self.count_label = tk.Label(
            self.master, text=f"Enrolled users: {self.count}", font=("Arial", 16))
        self.count_label.pack(side=tk.TOP)

        # Set up image and message
        self.image = Image.open("./images/face-id.png")
        self.image = self.image.resize(
            (500, 500), Image.LANCZOS)  # Resize image to 300x300
        self.image = ImageTk.PhotoImage(self.image)
        self.image_label = tk.Label(self.master, image=self.image)
        self.image_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.message_label = tk.Label(
            self.master, text="Message", font=("Arial", 16))
        self.message_label.place(relx=0.5, rely=0.75, anchor=tk.CENTER)

        # Set up buttons
        self.button_frame = tk.Frame(self.master)
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)
        # Quit Button
        self.quit_image = Image.open("./images/quit.png")
        self.quit_image = self.quit_image.resize(
            (90, 90), Image.LANCZOS)  # Resize image to 30x30
        self.quit_image = ImageTk.PhotoImage(self.quit_image)
        self.quit_button = tk.Button(
            self.button_frame, image=self.quit_image, command=self.quit, bd=0)
        self.quit_button.pack(side=tk.RIGHT, padx=(0, 60))
        # Enroll Button
        self.enroll_image = Image.open("./images/enroll.png")
        self.enroll_image = self.enroll_image.resize(
            (90, 90), Image.LANCZOS)  # Resize image to 30x30
        self.enroll_image = ImageTk.PhotoImage(self.enroll_image)
        self.enroll_button = tk.Button(
            self.button_frame, image=self.enroll_image, command=self.enroll, bd=0)
        self.enroll_button.pack(side=tk.LEFT, padx=(60, 0))

        self.f = FaceAuthenticator(PORT)

    def enroll(self):
        # Enroll function using FaceAuthenticator class
        popup = tk.Toplevel(self.master)
        popup.title("Enroll User")
        popup.geometry("300x150")

        # Set up user id label and entry field
        user_id_label = tk.Label(popup, text="Enter User ID:")
        user_id_label.pack()
        user_id_var = tk.StringVar()
        user_id_entry = tk.Entry(popup, textvariable=user_id_var)
        user_id_entry.pack()

        # Set up enroll button
        enroll_button = tk.Button(popup, text="Enroll", command=lambda: self.do_enroll(popup, user_id_var.get()))
        enroll_button.pack()

    def do_enroll(self, popup, user_id):
        # Enroll user using FaceAuthenticator class
        # face_authenticator = FaceAuthenticator()
        try:
            self.f.enroll(user_id=user_id)
            popup.destroy()
            self.update_count_label()
        except Exception as e:
            # Display error message if enrollment fails
            error_label = tk.Label(popup, text=str(e))
            error_label.pack()


    def update_count_label(self):
        # Update the user count label
        count = len(FaceAuthenticator(PORT).query_user_ids())
        # Update count
        self.count = count
        self.count_label.config(text=f"Enrolled users: {count}")

    def start_ultrasonic_detection(self):
        while True:
            time.sleep(0.5)
            distance = board.analog_read(T_PIN)
            if distance < 50:
                self.f.preview(False)
                # status_msg = 'Detecting person...'
                self.f.authenticate(
                    on_result=self.on_result, on_progress=self.on_progress, on_hint=self.on_hint, on_faces=self.on_faces)

    def quit(self):
        # Add functionality for Quit button
        self.master.destroy()

    def on_hint(self, hint):
        print(hint)

    def on_progress(self, progress):
        print(progress)

    def on_faces(self, faces, timestamp):
        print(faces)

    def on_result(self, result):
        print(result)


if __name__ == "__main__":
    root = tk.Tk()
    app = FaceID(root)

    # Start ultrasonic detection thread
    ultrasonic_thread = threading.Thread(target=app.start_ultrasonic_detection)
    ultrasonic_thread.start()

    root.mainloop()