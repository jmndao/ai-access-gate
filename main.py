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

status_msg = ''
# array of (faces, success, user_name)
detected_faces = []


screen_size = (640, 480)
img_lock = Lock()


def on_result(result, user_id=None):
    global status_msg
    global detected_faces

    success = result == rsid_py.AuthenticateStatus.Success
    status_msg = f'Success "{user_id}"' if success else str(result)

    if success:
        print("Gate is opening...")
        # gate_trigger()

    # find next face without a status
    for f in detected_faces:
        if not 'success' in f:
            f['success'] = success
            f['user_id'] = user_id
            break


def on_progress(p):
    global status_msg
    status_msg = f'on_progress {p}'


def on_hint(h):
    global status_msg
    status_msg = f'{h}'


def on_faces(faces, timestamp):
    global status_msg
    global detected_faces
    status_msg = f'detected {len(faces)} face(s)'
    detected_faces = [{'face': f} for f in faces]


def remove_all_users():
    global status_msg
    with rsid_py.FaceAuthenticator(PORT) as f:
        status_msg = "Remove.."
        f.remove_all_users()
        status_msg = 'Remove Success'


# Preview

def color_from_msg(msg):
    if 'Success' in msg:
        return (0x3c, 0xff, 0x3c)
    if 'Forbidden' in msg or 'Fail' in status_msg or 'NoFace' in status_msg:
        return (0x3c, 0x3c, 255)
    return (0xcc, 0xcc, 0xcc)


def show_face(face, image):
    # scale rets from 1080p
    f = face['face']

    scale_x = image.shape[1] / 980.0
    scale_y = image.shape[0] / 1920.0
    x = int(f.x * scale_x)
    y = int(f.y * scale_y)
    w = int(f.w * scale_y)
    h = int(f.h * scale_y)

    start_point = (x, y)
    end_point = (x + w, y + h)
    success = face.get('success')
    if success is None:
        color = (0x33, 0xcc, 0xcc)  # yellow
    else:
        color = (0x11, 0xcc, 0x11) if success else (0x11, 0x11, 0xcc)
    thickness = 2
    cv2.rectangle(image, start_point, end_point, color, thickness)


def show_status(msg, image, color):
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.4
    thickness = 3
    padding = 20

    (msg_w, msg_h), _ = cv2.getTextSize(
        msg, font, fontScale=font_scale, thickness=thickness)
    image_h, image_w = image.shape[0], image.shape[1]
    rect_x = 0
    rect_y = image_h - msg_h - padding * 2

    start_point = (rect_x, rect_y)
    end_point = (image_w, image_h)

    bg_color = (0x33, 0x33, 0x33)
    image = cv2.rectangle(image, start_point, end_point, bg_color, -thickness)
    # align to center
    text_x = int((image_w - msg_w) / 2)
    text_y = rect_y + msg_h + padding
    msg = msg.replace('Status.', ' ')
    return cv2.putText(image, msg, (text_x, text_y), font, font_scale, color, thickness, cv2.LINE_AA)


def on_image(image):
    img_lock.acquire()
    buffer = memoryview(image.get_buffer())
    arr = np.asarray(buffer, dtype=np.uint8)
    arr2d = arr.reshape((image.height, image.width, -1))
    img_rgb = cv2.cvtColor(arr2d, cv2.COLOR_BGR2RGB)
    img_scaled = cv2.resize(img_rgb, screen_size)

    # show faces
    for f in detected_faces:
        show_face(f, img_scaled)

    img_scaled = cv2.flip(img_scaled, 1)

    color = color_from_msg(status_msg)

    img_scaled = show_status(status_msg, image=img_scaled, color=color)

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


@app.route('/users')
def query_users():
    with rsid_py.FaceAuthenticator(PORT) as f:
        return jsonify(f.query_user_ids().count())


@app.route('/video_feed')
def video_feed():
    return Response(VideoStream().gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/authenticate', methods=["GET"])
def authenticate():
    global status_msg
    with rsid_py.FaceAuthenticator(PORT) as f:
        status_msg = "Authenticating.."
        f.authenticate(on_hint=on_hint, on_result=on_result, on_faces=on_faces)
    return jsonify(status_msg)


@app.route('/enroll', methods=["POST", "GET"])
def enroll():
    if request.method == 'POST':
        user = request.form['user']
        with rsid_py.FaceAuthenticator(PORT) as f:
            f.enroll(user_id=user, on_hint=on_hint,
                     on_progress=on_progress, on_faces=on_faces, on_result=on_result)
    return jsonify(status_msg)


@app.route('/exit')
def exit_app():
    global status_msg
    status_msg = 'Bye.. :)'
    time.sleep(0.4)
    os._exit(0)


if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', debug=False, threaded=True, processes=1)
    finally:
        VideoStream().p.stop()
