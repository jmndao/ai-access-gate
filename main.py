#Modified by smartbuilds.io
#Date: 27.09.20
#Desc: This web application serves a motion JPEG stream
# main.py
# import the necessary packages
from flask import Flask, render_template, Response, request, send_from_directory

import time
import os

import cv2
import numpy as np
import rsid_py


# App Globals (do not edit)
app = Flask(__name__)
screen_size = (920, 600)

def on_image(image):
    buffer = memoryview(image.get_buffer())
    arr = np.asarray(buffer, dtype=np.uint8)
    arr2d = arr.reshape((image.height, image.width, -1))
    img_rgb = cv2.cvtColor(arr2d, cv2.COLOR_BGR2RGB)
    img_scaled = cv2.resize(img_rgb, screen_size)
    cv2.imwrite('capture.jpg', img_scaled)

class VideoStream:
    def __init__(self):
        self.preview_cfg = rsid_py.PreviewConfig()
        self.preview_cfg.camera_number = -1
        self.p = rsid_py.Preview(self.preview_cfg)
        self.p.start(on_image)

    def gen(self):
        while True:
            yield(b'--frame\r\n'
                  b'Content-Type: image/jpeg\r\n\r\n' +  open('capture.jpg','rb').read() + b'\r\n\r\n')

    def __del__(self):
        self.p.stop()


@app.route('/')
def index():
    return render_template('index.html') #you can customze index.html here

@app.route('/video_feed')
def video_feed():
    return Response(VideoStream().gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Take a photo when pressing camera button
@app.route('/picture')
def take_picture():
    # pi_camera.take_picture()
    return "None"

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', debug=False)
    finally:
        VideoStream().p.stop()
