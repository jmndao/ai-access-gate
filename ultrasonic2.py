from pyfirmata import Arduino, util
import time
from datetime import datetime

board = Arduino('/dev/ttyACM1')

it = util.Iterator(board)
it.start()

t_pin = board.get_pin('d:3:o')
e_pin = board.get_pin('d:2:i')


while True:
	t_pin.write(0)

	time.sleep(1)

	t_pin.write(1)
	time.sleep(0.00001)
	t_pin.write(0)

	while e_pin.read() is None:
		pass

	start = datetime.now()

	while e_pin.read() is None:
		pass

	end = datetime.now()

	intval = (end - start).microseconds

	distance = intval/58

	print("Distance {} cm".format(distance))
