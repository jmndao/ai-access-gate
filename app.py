import os
import time
import asyncio
from threading import Lock

import numpy as np
import tkinter as tk
from tkinter import messagebox

import configparser as cfg

from PIL import Image, ImageTk

import cv2
from rsid_py import FaceAuthenticator, AuthenticateStatus, EnrollStatus, PreviewConfig, Preview

from db import FirebaseAdminDB


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

config = cfg.RawConfigParser()
# Load the config
config.read(os.path.join(BASE_DIR, "config.ini"))

CAM_PORT = "/dev/cam"
ARDUINO_PORT = "/dev/arduino"
# Pin definition
GATE_PIN = 7  # Gate Pin (servo)
E_PIN = 2  # Echo Pin (ultrasonic Sensor)
T_PIN = 3  # Trigger Pin (ultrasonic Sensor)


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
            self.master, text="Khelcom Face ID Access", font=("Arial", 34), padx=20, pady=20)
        self.header_label.pack(side=tk.TOP)

        # Default path to face-id image
        self.face_id = os.path.join(BASE_DIR, "images/face-id.png")

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
        self.quit_image = Image.open(os.path.join(BASE_DIR, "images/quit.png"))
        self.quit_image = self.quit_image.resize(
            (90, 90), Image.LANCZOS)  # Resize image to 30x30
        self.quit_image = ImageTk.PhotoImage(self.quit_image)
        self.quit_button = tk.Button(
            self.button_frame, image=self.quit_image, command=self.quit, bd=0)
        self.quit_button.pack(side=tk.RIGHT, padx=(0, 60))
        # Enroll Button
        self.enroll_image = Image.open(os.path.join(BASE_DIR, "images/enroll.png"))
        self.enroll_image = self.enroll_image.resize(
            (90, 90), Image.LANCZOS)  # Resize image to 30x30
        self.enroll_image = ImageTk.PhotoImage(self.enroll_image)
        self.enroll_button = tk.Button(
            self.button_frame, image=self.enroll_image, command=self.enroll, bd=0)
        self.enroll_button.pack(side=tk.LEFT, padx=(60, 0))

        # rsid_py authenticator instance
        self.f = FaceAuthenticator(CAM_PORT)
        self.detected_faces = []

        # Set up count label
        self.count_label = tk.Label(
            self.master, text=f"Enrolled users: {0}", font=("Arial", 16))
        self.count_label.pack(side=tk.TOP)

        # Image lock
        self.img_lock = Lock()

        # Status msg
        self.status_msg = ""
        self.img_filename = f'captures/user.jpeg'

        # Get full path to serviceAccount.json file
        cred_file = os.path.join(BASE_DIR, "creds.json")
        # Initialize firebase
        self.fb = FirebaseAdminDB(cred_file_path=cred_file)

        self.update_count_label()

        try:
            from pymata4 import pymata4 as py4
        except ImportError:
            print('Failed importing pyfirmata. Please install it (pip install pyfirmata)')
            exit(0)

        # Define the board via pymata protocol
        self.board = py4.Pymata4(ARDUINO_PORT)

        self.board.set_pin_mode_digital_output(GATE_PIN)

    def enroll(self):
        # Enroll function using FaceAuthenticator class
        self.f.enroll(on_hint=self.on_hint, on_progress=self.on_progress, on_result=self.on_enroll_result,
                      on_faces=self.on_faces, user_id=f"user_{int(time.time() / 1000)}")
        self.update_count_label()

    def on_enroll_result(self, result):
        if result == EnrollStatus.Success:
            messagebox.showinfo("Enrollment Successful",
                                "You've been enrolled successfully")
        else:
            messagebox.showerror("Enrollment Failed", "Enrollment has failed")

    def update_count_label(self):
        # Update the user count label
        self.count_label.config(
            text=f"Enrolled users: {len(self.f.query_user_ids())}")

    def authenticate(self):
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
            print("Distance: ", distance)
            if distance >= 10 and distance <= 40:
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
        self.update_count_label()

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
        return cv2.putText(image, self.status_msg, (text_x, text_y), font,
                           font_scale, color, thickness, cv2.LINE_AA)

    def show_face(self, face, image):
        # scale rets from 1080p
        f = face['face']

        scale_x = image.shape[1] / 1080.0
        scale_y = image.shape[0] / 1920.0
        x = int(f.x * scale_x)
        y = int(f.y * scale_y)
        w = int(f.w * scale_y)
        h = int(f.h * scale_y)

        start_point = (x, y)
        end_point = (x + w, y + h)
        color = self.color_from_msg()
        thickness = 2
        cv2.rectangle(image, start_point, end_point, color, thickness)

    def capture_image(self, image):
        self.img_lock.acquire()
        buffer = memoryview(image.get_buffer())
        arr = np.asarray(buffer, dtype=np.uint8)
        arr2d = arr.reshape((image.height, image.width, -1))
        img_rgb = cv2.cvtColor(arr2d, cv2.COLOR_BGR2RGB)

        for f in self.detected_faces:
            self.show_face(f, img_rgb)

        # Extract corresponding color
        color = self.color_from_msg()

        img_rgb = self.show_status(image=img_rgb, color=color)
        img_scaled = cv2.resize(img_rgb, self.img_size)

        # create captures folder if it doesn't exist
        if not os.path.exists('captures'):
            os.makedirs('captures')

        # Open image
        self.image = Image.open(self.img_filename)
        self.image = ImageTk.PhotoImage(self.image)
        self.image_label.configure(image=self.image)

        self.face_id = self.img_filename

        # save image
        cv2.imwrite(self.img_filename, img_scaled)

        self.img_lock.release()

    def on_hint(self, hint):
        pass

    def on_progress(self, progress):
        pass

    def on_faces(self, faces, timestamp):
        self.detected_faces = [{'face': f} for f in faces]

    def on_result(self, result, user_id=None):
        # Enroll user and save their face in the database with a random user id
        if result == AuthenticateStatus.Success:
            self.status_msg = "Authentication successful"

            asyncio.run(self.fb.upload_image(
                self.img_filename, f'{self.face_id}.jpg'))

            asyncio.run(self.fb.save_data(status="Success",
                                          current_time=time.strftime("%Y-%m-%d %H:%M:%S")))

            # Open the door
            self.gate_trigger()
        elif result == AuthenticateStatus.Failure or result == AuthenticateStatus.Forbidden:
            self.status_msg = "Authentication failed"

            asyncio.run(self.fb.save_data(status="Forbidden",
                                          current_time=time.strftime("%Y-%m-%d %H:%M:%S")))
        else:
            self.status_msg = "No face detected"

    def gate_trigger(self):
        self.board.digital_write(GATE_PIN, 0)
        time.sleep(1)
        self.board.digital_write(GATE_PIN, 1)
        return
