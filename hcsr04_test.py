import time
from pymata4 import pymata4 as py4

E_PIN = 2
T_PIN = 3
DISTANCE_CM = 2


def cb(data):
	print("Distance: {} cm".format(data[DISTANCE_CM]))

def sonar(board, t_pin, e_pin, cb):
	board.set_pin_mode_sonar(t_pin, e_pin, cb)

	while True:
		try:
			time.sleep(.01)
			print("Data read: {}".format(board.sonar_read(T_PIN)))
		except KeyboardInterrupt:
			board.shutdown()
			sys.exit(0)

board = py4.Pymata4('/dev/ttyACM1')

try:
	sonar(board, T_PIN, E_PIN, cb)
	board.shutdown()
except(KeyInterrupt, RuntimeError):
	board.shutdown()
	sys.exit(0)
