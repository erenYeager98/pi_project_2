# This file has to be run under /home/camera1 on the camera1 pi.
import socket
import cv2
from picamera2 import Picamera2

def send_stream():
    server_socket = socket.socket()
    server_socket.bind(('0.0.0.0', 8000))
    server_socket.listen(0)

    connection = server_socket.accept()[0].makefile('wb')
    picam2 = Picamera2()
    picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
    picam2.start()

    try:
        while True:
            frame = picam2.capture_array()
            _, buffer = cv2.imencode('.jpg', frame)
            connection.write(len(buffer).to_bytes(4, byteorder='big'))
            connection.write(buffer.tobytes())
    finally:
        connection.close()
        server_socket.close()

if __name__ == '__main__':
    send_stream()
