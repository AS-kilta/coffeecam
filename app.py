import urllib.request
import cv2

from decouple import config

def getImage() -> bool:
	TAPO_USERNAME = config("TAPO_USERNAME")
	TAPO_PASSWORD = config("TAPO_PASSWORD")

	HOST = "192.168.1.45" # The server's hostname or IP address
	PORT = 554 # The port used by the server

	url = f"rtsp://{TAPO_USERNAME}:{TAPO_PASSWORD}@{HOST}:{PORT}/stream1"
	savePath = "/mnt/ramdisk/newest.jpeg"

	# Create stream object.

	try:
		stream = cv2.VideoCapture(url)
	except Exception as g:
		print("no stream")

	# Set timeout at 10s, and try to read from stream.

	stream.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10_000)
	success, image = stream.read()

	# Save to file if succesfull

	if success:
		success = cv2.imwrite(savePath, image)
	return success
