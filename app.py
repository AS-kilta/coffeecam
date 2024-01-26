import urllib.request
import cv2

from decouple import config

def getImage():
	TAPO_USERNAME = config("TAPO_USERNAME")
	TAPO_PASSWORD = config("TAPO_PASSWORD")

	HOST = "192.168.1.45" # The server's hostname or IP address
	PORT = 554 # The port used by the server

	url = f"rtsp://{TAPO_USERNAME}:{TAPO_PASSWORD}@{HOST}:{PORT}/stream1"
	savePath = "pic1.jpeg"

	try:
		stream = cv2.VideoCapture(url)
	except Exception as g:
		print("no stream")

	success, image = stream.read()

	cv2.imwrite(savePath, image)

if __name__ == "__main__":

