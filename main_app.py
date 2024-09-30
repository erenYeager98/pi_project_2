import sys
import socket
import struct
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QStackedLayout
from PyQt5.QtGui import QPixmap, QImage, QFont
from PyQt5.QtCore import Qt, QTimer
import numpy as np
import cv2


class VideoClient(QWidget):
    def __init__(self, host, port, camera_label):
        super().__init__()

        self.host = host
        self.port = port
        self.camera_label_text = camera_label

        # Set up a stacked layout to switch between the video stream and error message
        self.stack_layout = QStackedLayout()

        # Label for displaying the video frames
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)

        # Label for showing an error message if the camera is not available
        self.error_label = QLabel(f"{camera_label} error")
        self.error_label.setFont(QFont('Arial', 24))
        self.error_label.setStyleSheet('color: red')
        self.error_label.setAlignment(Qt.AlignCenter)

        # Stack video label and error label
        self.stack_layout.addWidget(self.video_label)
        self.stack_layout.addWidget(self.error_label)

        layout = QVBoxLayout()
        # Add camera label
        self.camera_label = QLabel(camera_label)
        self.camera_label.setFont(QFont('Arial', 16))
        self.camera_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.camera_label)

        # Add stacked layout to the widget
        layout.addLayout(self.stack_layout)
        self.setLayout(layout)

        # Initialize socket and connection state
        self.client_socket = None
        self.is_connected = False

        # Timer for trying to reconnect and receiving frames
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.receive_frame)
        self.timer.start(1000)  # Start trying to connect every 1 second

    def receive_frame(self):
        try:
            if not self.is_connected:
                self.connect_to_server()

            # First receive the length of the frame
            raw_length = self.client_socket.recv(4)
            if not raw_length:
                raise ConnectionError("No frame length received")

            frame_length = struct.unpack('>I', raw_length)[0]

            # Then receive the actual frame
            frame_data = b''
            while len(frame_data) < frame_length:
                frame_data += self.client_socket.recv(frame_length - len(frame_data))

            # Convert the frame to a numpy array
            np_frame = np.frombuffer(frame_data, dtype=np.uint8)

            # Decode the frame using OpenCV
            frame = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)

            # Convert the frame to QImage and display it in the PyQt5 window
            height, width, channels = frame.shape
            bytes_per_line = channels * width
            q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)

            # Update the label with the new frame
            self.video_label.setPixmap(pixmap)
            self.stack_layout.setCurrentWidget(self.video_label)  # Show the video

        except Exception as e:
            print(f"Error receiving frame from {self.camera_label_text}: {e}")
            # self.stack_layout.setCurrentWidget(self.error_label)  # Show the error label
            self.is_connected = False

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            self.is_connected = True
            print(f"Connected to {self.camera_label_text}")
        except Exception as e:
            print(f"Failed to connect to {self.camera_label_text} at {self.host}:{self.port}")
            self.stack_layout.setCurrentWidget(self.error_label)  # Show the error label


class MainWindow(QMainWindow):
    def __init__(self, host1, port1, host2, port2):
        super().__init__()

        self.setWindowTitle("Dual Video Stream")
        self.setGeometry(100, 100, 1280, 720)  # Adjust the window size

        # Create two VideoClient widgets for two different servers
        self.client1 = VideoClient(host1, port1, "Camera 1")  # First server stream
        self.client2 = VideoClient(host2, port2, "Camera 2")  # Second server stream

        # Set up a horizontal layout to display both streams side by side
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.client1)  # Add the first video stream
        self.layout.addWidget(self.client2)  # Add the second video stream

        # Central container for the window
        self.container = QWidget()
        self.container.setLayout(self.layout)
        self.setCentralWidget(self.container)

        # Timer to handle switching layout when one of the streams fails
        self.switch_timer = QTimer(self)
        self.switch_timer.timeout.connect(self.handle_layout_switch)
        self.switch_timer.start(1000)  # Check every second

    def handle_layout_switch(self):
        # If both clients are connected, show side-by-side layout
        if self.client1.is_connected and self.client2.is_connected:
            self.show_side_by_side()
        # If only Camera 1 is connected, show Camera 1 full screen
        elif self.client1.is_connected and not self.client2.is_connected:
            self.show_single_camera(self.client1)
        # If only Camera 2 is connected, show Camera 2 full screen
        elif not self.client1.is_connected and self.client2.is_connected:
            self.show_single_camera(self.client2)
        # If both are not connected, keep showing error messaes
        else:
            self.show_side_by_side()  # Default to side-by-side with error messages

    def show_side_by_side(self):
        if self.layout.count() == 1:
            self.layout.addWidget(self.client1)
            self.layout.addWidget(self.client2)

    def show_single_camera(self, client):
        # Remove other widgets if needed
        while self.layout.count() > 0:
            widget = self.layout.takeAt(0).widget()
            if widget:
                widget.setParent(None)

        # Add the single camera
        self.layout.addWidget(client)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Replace with the actual IP addresses and ports of the two servers
    host1 = "192.168.29.23"  # First server's IP address
    port1 = 8000                  # First server's port

    host2 = "192.168.29.122"  # Second server's IP address
    port2 = 8000                  # Second server's port

    # Create the main window with two video streams
    window = MainWindow(host1, port1, host2, port2)

    # Show the window
    window.show()

    # Run the PyQt5 event loop
    sys.exit(app.exec_())
