# This file has to be placed under /home/pi on the main pi.
import sys
import cv2
import socket
import numpy as np
from PyQt5.QtWidgets import QApplication, QLabel, QHBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
from picamera2 import Picamera2

class CameraStream:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.ip, self.port))
        self.stream = self.socket.makefile('rb')

    def read_frame(self):
        length = self._read_length()
        frame_data = self.stream.read(length)
        frame = np.frombuffer(frame_data, dtype=np.uint8)
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
        return frame

    def _read_length(self):
        length = self.stream.read(4)
        length = int.from_bytes(length, byteorder='big')
        return length

class CameraDisplay(QWidget):
    def __init__(self, camera1, camera2):
        super().__init__()
        self.camera1 = camera1
        self.camera2 = camera2

        self.label1 = QLabel(self)
        self.label2 = QLabel(self)

        layout = QHBoxLayout()
        layout.addWidget(self.label1)
        layout.addWidget(self.label2)
        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frames)
        self.timer.start(100)  # Update every 100ms

    def update_frames(self):
        frame1 = self.camera1.read_frame()
        frame2 = self.camera2.read_frame()

        self._update_label(self.label1, frame1)
        self._update_label(self.label2, frame2)

    def _update_label(self, label, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        label.setPixmap(pixmap)

def main():
    app = QApplication(sys.argv)

    # Replace '192.168.0.101' and '192.168.0.102' with the IP addresses of your camera Pis
    camera1 = CameraStream('192.168.0.10', 8000)
    camera2 = CameraStream('192.168.0.13', 8000)

    display = CameraDisplay(camera1, camera2)
    display.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
