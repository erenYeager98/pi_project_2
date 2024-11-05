import sys
import socket
import struct
import subprocess
import threading
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QStackedLayout
from PyQt5.QtGui import QPixmap, QImage, QFont
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
import numpy as np
import cv2
import time
import RPi.GPIO as GPIO 


GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


class HeartbeatThread(QThread):
    """Thread to send periodic heartbeat messages to the server."""
    def __init__(self, video_receiver):
        super().__init__()
        self.video_receiver = video_receiver
        self.running = True

    def run(self):
        while self.running:
            if self.video_receiver.is_connected:
                try:
                    self.video_receiver.client_socket.sendall(b'HEARTBEAT')
                    time.sleep(3)
                except (socket.timeout, ConnectionResetError, BrokenPipeError):
                    print(f"Heartbeat failed for {self.video_receiver.camera_label_text}")
                    self.video_receiver.is_connected = False
                    self.video_receiver.error_occurred.emit()
                    self.running = False
            else:
                time.sleep(1)

    def stop(self):
        self.running = False
        self.wait()


class VideoReceiver(QThread):
    frame_received = pyqtSignal(np.ndarray)
    error_occurred = pyqtSignal()

    def __init__(self, host, port, camera_label):
        super().__init__()
        self.host = host
        self.port = port
        self.camera_label_text = camera_label
        self.is_connected = False
        self.client_socket = None
        self.running = True
        self.heartbeat_thread = None

    def run(self):
        while self.running:
            try:
                if not self.is_connected:
                    self.connect_to_server()

                raw_length = self.client_socket.recv(4)
                if not raw_length:
                    raise ConnectionError("No frame length received")

                frame_length = struct.unpack('>I', raw_length)[0]
                frame_data = b''
                while len(frame_data) < frame_length:
                    frame_data += self.client_socket.recv(frame_length - len(frame_data))

                np_frame = np.frombuffer(frame_data, dtype=np.uint8)
                frame = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)
                if frame is not None:
                    self.frame_received.emit(frame)
            except Exception as e:
                print(f"Error receiving frame from {self.camera_label_text}: {e}")
                self.error_occurred.emit()
                self.is_connected = False

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            self.is_connected = True
            print(f"Connected to {self.camera_label_text}")

            self.heartbeat_thread = HeartbeatThread(self)
            self.heartbeat_thread.start()
        except Exception as e:
            print(f"Failed to connect to {self.camera_label_text} at {self.host}:{self.port}")
            self.error_occurred.emit()

    def stop(self):
        self.running = False
        if self.client_socket:
            self.client_socket.close()
        if self.heartbeat_thread:
            self.heartbeat_thread.stop()


class ReconnectionThread(QThread):
    def __init__(self, video_receiver):
        super().__init__()
        self.video_receiver = video_receiver
        self.attempt_reconnect = True

    def run(self):
        while self.attempt_reconnect:
            if not self.video_receiver.is_connected:
                print(f"Attempting to reconnect {self.video_receiver.camera_label_text}")
                self.video_receiver.connect_to_server()
            self.sleep(5)

    def stop(self):
        self.attempt_reconnect = False
        self.wait()


class GPIOShutdownThread(threading.Thread):
    def run(self):
        while True:
            if GPIO.input(17) == GPIO.HIGH:
                print("Shutdown button pressed. Shutting down the server...")
                subprocess.run(["sudo", "shutdown", "now"])




class VideoClient(QWidget):
    def __init__(self, host, port, camera_label):
        super().__init__()

        self.camera_label_text = camera_label
        self.current_frame = None
        self.shift_threshold_cm = 1.0  # Threshold to ignore shifts below 1 cm
        self.previous_dx_cm = 0.0
        self.previous_dy_cm = 0.0

        # Layout setup
        self.stack_layout = QStackedLayout()
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)

        self.error_label = QLabel(f"{camera_label} error")
        self.error_label.setFont(QFont('Arial', 24))
        self.error_label.setStyleSheet('color: red')
        self.error_label.setAlignment(Qt.AlignCenter)

        self.stack_layout.addWidget(self.video_label)
        self.stack_layout.addWidget(self.error_label)

        layout = QVBoxLayout()
        self.camera_label = QLabel(camera_label)
        self.camera_label.setFont(QFont('Arial', 16))
        self.camera_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.camera_label)
        layout.addLayout(self.stack_layout)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.video_receiver = VideoReceiver(host, port, camera_label)
        self.video_receiver.frame_received.connect(self.update_frame)
        self.video_receiver.error_occurred.connect(self.show_error)
        self.video_receiver.start()

        self.reconnection_thread = ReconnectionThread(self.video_receiver)
        self.reconnection_thread.start()

    def update_frame(self, frame):
        self.current_frame = frame

        height, width, channels = frame.shape
        bytes_per_line = channels * width
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)

        self.video_label.setPixmap(pixmap)
        self.stack_layout.setCurrentWidget(self.video_label)

    def show_error(self):
        self.stack_layout.setCurrentWidget(self.error_label)

    def closeEvent(self, event):
        self.video_receiver.stop()
        self.reconnection_thread.stop()
        event.accept()

    def compute_shift(self, other_frame):
        if self.current_frame is not None and other_frame is not None:
            gray1 = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(other_frame, cv2.COLOR_BGR2GRAY)

            orb = cv2.ORB_create()
            kp1, des1 = orb.detectAndCompute(gray1, None)
            kp2, des2 = orb.detectAndCompute(gray2, None)

            if des1 is None or des2 is None:
                return None, None

            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(des1, des2)

            if len(matches) > 0:
                matches = sorted(matches, key=lambda x: x.distance)
                src_pts = np.float32([kp1[m.queryIdx].pt for m in matches])
                dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches])

                displacement = np.mean(dst_pts - src_pts, axis=0)
                dx, dy = displacement

                pixel_to_cm_factor = 0.05
                dx_cm = dx * pixel_to_cm_factor
                dy_cm = dy * pixel_to_cm_factor

                # Apply threshold to reduce fluctuations within 1 cm range
                if abs(dx_cm - self.previous_dx_cm) >= self.shift_threshold_cm:
                    self.previous_dx_cm = dx_cm
                else:
                    dx_cm = self.previous_dx_cm

                if abs(dy_cm - self.previous_dy_cm) >= self.shift_threshold_cm:
                    self.previous_dy_cm = dy_cm
                else:
                    dy_cm = self.previous_dy_cm

                return dx_cm, dy_cm
            else:
                return None, None
        else:
            return None, None
    def is_connected(self):
        return self.video_receiver.is_connected 
            

class MainWindow(QMainWindow):
    def __init__(self, host1, port1, host2, port2):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.showMaximized()

        self.client1 = VideoClient(host1, port1, "Camera 1")
        self.client2 = VideoClient(host2, port2, "Camera 2")

        self.layout = QVBoxLayout()
        self.cameras_layout = QHBoxLayout()
        self.cameras_layout.addWidget(self.client1)
        self.cameras_layout.addWidget(self.client2)

        self.displacement_label = QLabel("Displacement: ΔX = N/A cm, ΔY = N/A cm")
        self.displacement_label.setFont(QFont('Arial', 16))
        self.displacement_label.setAlignment(Qt.AlignCenter)

        self.logo_label = QLabel(self)
        logo_pixmap = QPixmap("logo.jpg").scaled(150, 150, Qt.KeepAspectRatio)
        self.logo_label.setPixmap(logo_pixmap)
        self.logo_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.layout.addWidget(self.logo_label)

        self.layout.addLayout(self.cameras_layout)
        self.layout.addWidget(self.displacement_label)

        self.container = QWidget()
        self.container.setLayout(self.layout)
        self.setCentralWidget(self.container)

        self.shift_timer = QTimer(self)
        self.shift_timer.timeout.connect(self.compute_shifts)
        self.shift_timer.start(1000)

        self.shutdown_thread = GPIOShutdownThread()
        self.shutdown_thread.start()

    def compute_shifts(self):
        if self.client1.is_connected() and self.client2.is_connected() and \
           self.client1.current_frame is not None and self.client2.current_frame is not None:
            dx_cm, dy_cm = self.client1.compute_shift(self.client2.current_frame)
            if dx_cm is not None and dy_cm is not None:
                self.displacement_label.setText(f"Displacement: ΔX = {dx_cm:.2f} cm, ΔY = {dy_cm:.2f} cm")
            else:
                self.displacement_label.setText("Cannot display displacement due to insufficient data from one or both cameras.")
        else:
            self.displacement_label.setText("Cannot display displacement: one or both cameras are disconnected.")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    host1 = "192.168.127.48"
    port1 = 8000
    host2 = "192.168.127.3"
    port2 = 8000

    window = MainWindow(host1, port1, host2, port2)
    window.show()

    sys.exit(app.exec_())
