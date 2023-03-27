# Modified by smartbuilds.io
# Date: 27.09.20
# Desc: This web application serves a motion JPEG stream
# main.py
# import the necessary packages
from flask import Flask, render_template, Response, request, jsonify

from threading import Lock
import time
import os
import base64

import cv2
import numpy as np
import rsid_py


# try:
#     from pymata4 import pymata4 as py4
# except ImportError:
#     print('Failed importing pyfirmata. Please install it (pip install pyfirmata)')
#     exit(0)

# App Globals (do not edit)
app = Flask(__name__)
app.config['SECRET_KEY'] = 'df0331cefc6c2b9a5d0208a726a5d1c0fd37324feba25506'
PORT = '/dev/ttyACM0'
ARDUINO_PORT = '/dev/ttyACM1'


face_authenticator = None
board = None

status_msg = ''
# array of (faces, success, user_name)
detected_faces = []

users_cache = None
cache_time = None


screen_size = (640, 480)
img_lock = Lock()

# Pin definition
BOARD_PIN = 7
E_PIN = 8
T_PIN = 9


# def gate_trigger():

#     global board

#     board.digital_write(BOARD_PIN, 0)
#     time.sleep(1)
#     board.digital_write(BOARD_PIN, 1)
#     return


def init_face_authenticator():
    global face_authenticator
    face_authenticator = rsid_py.FaceAuthenticator(PORT)

    def __del__(self):
        face_authenticator.stop_preview()


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
    if 'Forbidden' in msg or 'Fail' in msg or 'NoFace' in msg:
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

    # capture still image
    img_file = 'image.jpg'
    cv2.imwrite(img_file, img_scaled)

    # send file to frontend
    with open(img_file, 'rb') as f:
        image_bytes = f.read()
    image_b64 = base64.b64encode(image_bytes).decode('ascii')
    response = {'image': image_b64}

    # show faces
    for f in detected_faces:
        show_face(f, img_scaled)

    img_scaled = cv2.flip(img_scaled, 1)

    color = color_from_msg(status_msg)
    img_scaled = show_status(status_msg, img_scaled, color)

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
    global face_authenticator
    global users_cache
    global cache_time
    if users_cache is None or cache_time + 10*60 < time.time():
        users_cache = face_authenticator.query_user_ids()
        cache_time = time.time()
    return jsonify(len(users_cache))


@app.route('/video_feed')
def video_feed():
    return Response(VideoStream().gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/authenticate', methods=["GET"])
def authenticate():
    global face_authenticator

    status_msg = "Authenticating.."
    face_authenticator.authenticate(
        on_hint=on_hint, on_result=on_result, on_faces=on_faces)
    return jsonify(status_msg)


@app.route('/enroll', methods=["POST", "GET"])
def enroll():
    global face_authenticator

    if request.method == 'POST':
        user = request.form['user']
        face_authenticator.enroll(user_id=user, on_hint=on_hint,
                                  on_progress=on_progress, on_faces=on_faces, on_result=on_result)
    return jsonify(status_msg)


@app.route('/exit')
def exit_app():
    global status_msg
    status_msg = 'Bye.. :)'
    time.sleep(0.4)
    os._exit(0)


if __name__ == '__main__':
    # board = py4.Pymata4(ARDUINO_PORT)

    board.set_pin_mode_digital_output(BOARD_PIN)
    board.set_pin_mode_digital_output(13)

    board.digital_write(13, 1)  # turn on test led.
    board.digital_write(BOARD_PIN, 1)  # close gate at start
    try:
        init_face_authenticator()
        app.run(host='0.0.0.0', debug=False, threaded=True, processes=1)
    finally:
        VideoStream().p.stop()


@app.route('/authenticate', methods=['POST'])
def authenticate():
    global face_authenticator
    global status_msg
    global detected_faces

    if not face_authenticator:
        init_face_authenticator()

    # check if there is any presence nearby
    dist = int(board.sonar_read(t_pin)[0])
    if dist >= 10 and dist <= 50:
        # trigger the face detection
        face_authenticator.start_preview(
            on_faces, on_result, on_progress, on_hint)
    else:
        status_msg = "Please get close to the sensor"
        return jsonify({'status': status_msg})

    # wait for the detection to finish
    while len(detected_faces) == 0 or 'success' not in detected_faces[0]:
        time.sleep(0.01)

    # return the detection result
    result = detected_faces[0]
    user_id = result.get('user_id')
    success = result.get('success')
    status_msg = f'Success "{user_id}"' if success else 'Access Denied'
    return jsonify({'status': status_msg})
