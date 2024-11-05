import socket
import io
from threading import Condition
import threading
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
import RPi.GPIO as GPIO 
import subprocess


GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

def start_streaming_server():
    # Set up the camera
    picam2 = Picamera2()
    picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
    output = StreamingOutput()
    picam2.start_recording(JpegEncoder(), FileOutput(output))
    shutdown_thread = GPIOShutdownThread()
    shutdown_thread.start()


    while True:
        try:
            # Set up a TCP server
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            server_socket.bind(('0.0.0.0', 8000))  # Listen on port 8000
            server_socket.listen(1)
            print("Waiting for a connection...")

            client_socket, addr = server_socket.accept()
            print("Connection from:", addr)

            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    # Send frame length first
                    client_socket.sendall(len(frame).to_bytes(4, byteorder='big'))
                    # Send the actual frame
                    client_socket.sendall(frame)

            except ConnectionResetError:
                print("Connection reset by peer, waiting for new connection...")

            finally:
                # Ensure sockets are closed properly after a client disconnect
                client_socket.close()
                server_socket.close()

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            print("Restarting the server...")

class GPIOShutdownThread(threading.Thread):
    def run(self):
        while True:
            if GPIO.input(17) == GPIO.HIGH:
                print("Shutdown button pressed. Shutting down the server...")
                subprocess.run(["sudo", "shutdown", "now"])


if __name__ == "__main__":
    start_streaming_server()