# Modified by smartbuilds.io
# Date: 27.09.20
# Desc: This web application serves a motion JPEG stream
# main.py
# import the necessary packages
from flask import Flask, render_template, Response, request, jsonify

from threading import Lock
import time
import os

import cv2
import numpy as np
import rsid_py


# App Globals (do not edit)
app = Flask(__name__)
app.config['SECRET_KEY'] = 'df0331cefc6c2b9a5d0208a726a5d1c0fd37324feba25506'
PORT = '/dev/ttyACM0'


screen_size = (640, 480)
img_lock = Lock()


def on_result(result):
    print('on_result', result)


def on_progress(p):
    pass


def on_hint(h):
    pass


def on_faces(faces, timestamp):
    pass


def on_image(image):
    img_lock.acquire()
    buffer = memoryview(image.get_buffer())
    arr = np.asarray(buffer, dtype=np.uint8)
    arr2d = arr.reshape((image.height, image.width, -1))
    img_rgb = cv2.cvtColor(arr2d, cv2.COLOR_BGR2RGB)
    img_scaled = cv2.resize(img_rgb, screen_size)
    cv2.imwrite('capture.jpg', img_scaled, [cv2.IMWRITE_JPEG_QUALITY, 80])
    img_lock.release()


class VideoStream:
    def __init__(self):
        self.preview_cfg = rsid_py.PreviewConfig()
        self.preview_cfg.camera_number = -1
        self.p = rsid_py.Preview(self.preview_cfg)
        self.p.start(on_image)

    def gen(self):
        while True:
            time.sleep(1)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + open('capture.jpg', 'rb').read() + b'\r\n\r\n')

    def __del__(self):
        self.p.stop()


@app.route('/')
def index():
    return render_template('index.html')  # you can customze index.html here


@app.route('/video_feed')
def video_feed():
    return Response(VideoStream().gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Take a photo when pressing camera button


@app.route('/picture')
def take_picture():
    # pi_camera.take_picture()
    return "None"


@app.route('/enroll', methods=["POST", "GET"])
def enroll():
    if request.method == 'POST':
        user = request.form['user']
        with rsid_py.FaceAuthenticator(PORT) as f:
            f.enroll(user_id=user, on_hint=on_hint,
                     on_progress=on_progress, on_faces=on_faces, on_result=on_result)
    else:
        msg = 'No-data'
    return jsonify(msg)


if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', debug=False, threaded=True, processes=1)
    finally:
        VideoStream().p.stop()
