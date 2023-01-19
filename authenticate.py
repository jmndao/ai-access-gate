"""
License: Apache 2.0. See LICENSE file in root directory.
Copyright(c) 2020-2021 Intel Corporation. All Rights Reserved.
"""

import rsid_py
import pyfirmata
import time

PORT='/dev/ttyACM0'
ARDUINO_PORT='/dev/ttyACM1'
board = None

def on_result(result, user_id):
	print('on_result', result)    
	if result == rsid_py.AuthenticateStatus.Success:
		board.digital[7].write(0)
		board.digital[7].write(1) 
		print('Authenticated user:', user_id)
	elif result == rsid_py.AuthenticateStatus.Forbidden:
		board.digital[7].write(1)
		print('Please Authenticate !')
	else:
		board.digital[7].write(1)
		print('Your face is tilted, please face the camera')


def on_faces(faces, timestamp):    
	print(f'detected {len(faces)} face(s)')
	for f in faces:
		print(f'\tface {f.x},{f.y} {f.w}x{f.h}')    

if __name__ == '__main__':
	board = pyfirmata.Arduino(ARDUINO_PORT)
	board.digital[13].write(1)
	board.digital[7].write(1) # close the gate at start
	print("Arduino Port linked successfully...")
	with rsid_py.FaceAuthenticator(PORT) as f:
		f.authenticate(on_faces=on_faces, on_result=on_result)
    
