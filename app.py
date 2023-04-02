import os
import time
import threading
from threading import Lock

import numpy as np
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

import configparser as cfg

from PIL import Image, ImageTk

import cv2
from rsid_py import FaceAuthenticator, AuthenticateStatus, PreviewConfig, Preview


config = cfg.ConfigParser()
# Load the config
config.read("config.ini")

CAM_PORT = config.get("PORTS", "CAM_PORT")
ARDUINO_PORT = config.get("PORTS", "ARDUINO_PORT")
# Pin definition
BOARD_PIN = 7
E_PIN = 8  # Echo Pin (ultrasonic Sensor)
T_PIN = 9  # Trigger Pin (ultrasonic Sensor)


class FaceID:
    def __init__(self, master):
        # Set up main window
        self.master = master
        self.master.title("Face ID Access")
        self.master.geometry("{0}x{1}+0+0".format(
            self.master.winfo_screenwidth(), self.master.winfo_screenheight()))

        # Center Image size
        self.img_size = (400, 400)

        # Set up header title and count label
        self.header_label = tk.Label(
            self.master, text="DAUST Face ID Access", font=("Arial", 34), padx=20, pady=20)
        self.header_label.pack(side=tk.TOP)

        # Set up count label
        self.count = 0
        self.count_label = tk.Label(
            self.master, text=f"Enrolled users: {self.count}", font=("Arial", 16))
        self.count_label.pack(side=tk.TOP)

        # Default path to face-id image
        self.face_id = "./images/face-id.png"

        # Set up image and message
        self.image = Image.open(f"{self.face_id}")
        self.image = self.image.resize(
            self.img_size, Image.LANCZOS)  # Resize image to 300x300
        self.image = ImageTk.PhotoImage(self.image)

        self.image_label = tk.Label(self.master, image=self.image)
        self.image_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

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
        # Remove all users Button
        self.remove_all_image = Image.open("./images/remove_all.png")
        self.remove_all_image = self.remove_all_image.resize(
            (90, 90), Image.LANCZOS)  # Resize image to 30x30
        self.remove_all_image = ImageTk.PhotoImage(self.remove_all_image)
        self.remove_all_button = tk.Button(
            self.button_frame, image=self.remove_all_image, command=self.remove_all_users, bd=0)
        self.remove_all_button.pack(side=tk.LEFT, padx=(10, 0))

        # rsid_py authenticator instance
        self.f = FaceAuthenticator(CAM_PORT)

        # Image lock
        self.img_lock = Lock()

        # Status msg
        self.status_msg = ""

        try:
            from pymata4 import pymata4 as py4
        except ImportError:
            print('Failed importing pyfirmata. Please install it (pip install pyfirmata)')
            exit(0)

        # Define the board via pymata protocol
        self.board = py4.Pymata4(ARDUINO_PORT)

        self.board.set_pin_mode_digital_output(BOARD_PIN)
        # self.board.set_pin_mode_digital_output(13) # Output for led

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
        enroll_button = tk.Button(
            popup, text="Enroll", command=lambda: self.do_enroll(popup, user_id_var.get()))
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
        count = len(self.f.query_user_ids())
        # Update count
        self.count = count
        self.count_label.config(text=f"Enrolled users: {count}")

    def authenticate(self):
        # self.f.preview(False)
        # status_msg = 'Detecting person...'
        self.f.authenticate(on_result=self.on_result, on_faces=self.on_faces)

        # add this code to capture and save the image
        preview_cfg = PreviewConfig()
        preview_cfg.camera_number = 0
        p = Preview(preview_cfg)
        p.start(self.capture_image)
        time.sleep(0.5)
        p.stop()

    def start_ultrasonic_detection(self):
        self.board.set_pin_mode_sonar(T_PIN, E_PIN)
        while True:
            time.sleep(0.05)

            distance = int(self.board.sonar_read(T_PIN)[0])
            if distance >= 10 and distance <= 50:
                self.authenticate()

    def quit(self):
        # Release resources and stop threads
        self.board.shutdown()
        # Add functionality for Quit button
        self.master.destroy()
        os._exit(1)

    def confirm_remove_all_users(self):
        # create a message box to confirm the action
        response = messagebox.askyesno(
            "Confirm", "Are you sure you want to remove all users?")

        if response == 1:
            # if the user confirms, perform the action
            self.remove_all_users()

    def remove_all_users(self):
        # perform the action of removing all users here
        self.f.remove_all_users()

    def color_from_msg(self):
        if 'successful' in self.status_msg:
            return (0x3c, 0xff, 0x3c)
        if 'failed' in self.status_msg or 'Fail' in self.status_msg or 'NoFace' in self.status_msg:
            return (0x3c, 0x3c, 255)
        return (0xcc, 0xcc, 0xcc)

    def show_status(self, image, color):
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.5
        thickness = 3
        padding = 20

        (msg_w, msg_h), _ = cv2.getTextSize(
            self.status_msg, font, fontScale=font_scale, thickness=thickness)
        image_h, image_w = image.shape[0], image.shape[1]
        rect_x = 0
        rect_y = image_h - msg_h - padding * 2

        start_point = (rect_x, rect_y)
        end_point = (image_w, image_h)

        bg_color = (0x33, 0x33, 0x33)
        image = cv2.rectangle(image, start_point,
                              end_point, bg_color, -thickness)
        # align to center
        text_x = int((image_w - msg_w) / 2)
        text_y = rect_y + msg_h + padding
        msg = self.status_msg.replace('Status.', ' ')
        return cv2.putText(image, self.status_msg, (text_x, text_y), font, font_scale, color, thickness, cv2.LINE_AA)

    def capture_image(self, image):
        self.img_lock.acquire()
        buffer = memoryview(image.get_buffer())
        arr = np.asarray(buffer, dtype=np.uint8)
        arr2d = arr.reshape((image.height, image.width, -1))
        img_rgb = cv2.cvtColor(arr2d, cv2.COLOR_BGR2RGB)

        # Extract corresponding color
        color = self.color_from_msg()

        img_rgb = self.show_status(image=img_rgb, color=color)

        img_scaled = cv2.resize(img_rgb, self.img_size)

        # create captures folder if it doesn't exist
        if not os.path.exists('captures'):
            os.makedirs('captures')

        # generate unique image filename
        img_filename = f'captures/user.jpeg'

        # Open image
        self.image = Image.open(img_filename)
        self.image = ImageTk.PhotoImage(self.image)
        self.image_label.configure(image=self.image)

        self.face_id = img_filename

        # save image
        cv2.imwrite(img_filename, img_scaled)

        img_scaled = cv2.flip(img_scaled, 1)

        self.img_lock.release()

    def on_hint(self, hint):
        print(hint)

    def on_progress(self, progress):
        print(progress)

    def on_faces(self, faces, timestamp):
        print(faces)

    def on_result(self, result, user_id):
        print(result)
        if result == AuthenticateStatus.Success:
            self.status_msg = "Authentication successful"
            self.gate_trigger()
        elif result == AuthenticateStatus.Failure or result == AuthenticateStatus.Forbidden:
            self.status_msg = "Authentication failed"
        else:
            self.status_msg = "Please correct your posture"

    def gate_trigger(self):
        # self.board.digital_write(BOARD_PIN, 0)
        # time.sleep(1)
        # self.board.digital_write(BOARD_PIN, 1)
        # return
        print("Opening...")

    # Improvements
    # def authenticate(self):
    #     # Authenticate user using FaceAuthenticator class
    #     def authenticate_thread():
    #         self.f.authenticate(status_callback=self.authenticate_status_callback)

    #     threading.Thread(target=authenticate_thread).start()

    # def authenticate_status_callback(self, status):
    #     if status == AuthenticateStatus.SUCCESS:
    #         # Access granted
    #         self.open_door()
    #     elif status == AuthenticateStatus.ERROR:
    #         # Authentication error
    #         self.show_message("Authentication failed.")
    #     elif status == AuthenticateStatus.USER_UNKNOWN:
    #         # Unknown user
    #         self.show_message("User not recognized.")


if __name__ == "__main__":
    root = tk.Tk()
    app = FaceID(root)

    # Start ultrasonic detection thread
    ultrasonic_thread = threading.Thread(target=app.start_ultrasonic_detection)
    ultrasonic_thread.start()

    root.mainloop()
