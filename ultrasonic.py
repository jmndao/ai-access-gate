import time
from pyfirmata import Arduino, util
import adafruit_hcsr04 as ah

board = util.get_the_board(identifier="ttyACM1")
time.sleep(0.5)

echo = board.get_pin('d:2:i')
trig = board.get_pin('d:3:o')

sonar = ah.HCSR04(trig, echo)

count = 0

while True:
	if count >= 10:
		break
	try:
		print((sonar.distance,))
	except RuntimeError:
		print("Retrying!")
	time.sleep(2)
	count = count + 1
