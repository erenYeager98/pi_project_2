1. Prepare the Raspberry Pi Devices
 ● MainPi(with HDMI display) and 2 Pi Cameras.
 Step 1: Install Raspbian OS (Raspberry Pi OS)
 ● Download and install Raspberry Pi OS on each Raspberry Pi using tools like Raspberry
 Pi Imager.
 ● After booting, ensure all devices are connected to the same network (e.g., using a
 hotspot on the main Pi or a router).
 Step 2: Enable Camera Interface on Each Pi
 Open a terminal on each Pi:
 bash
 Copy code
 sudo raspi-config
 ●
 ● GotoInterface Options-> Camera-> Enable.
 Reboot the Pi to apply changes:
 bash
 Copy code
 sudo reboot
 ●
 Step 3: Install Required Packages (on all Pis)
 Update the system:
 bash
 Copy code
 sudo apt update && sudo apt upgrade-y
 ●
 Install Python 3 and essential libraries:
 bash
 Copy code
 sudo apt install python3 python3-pyqt5 python3-picamera2-y
 sudo apt install python3-opencv
●
 Step 4: Install and Configure Picamera2 Library (on Pi Cameras)
 ● Oneachof the Pi cameras, install the Picamera2 library:
 ● sudo apt install python3-picamera2
 Step 5: Setup the network (Hotspot on the main pi)
 Script: script_to_spawn_hotspot.py
 Command sudo python script_to_spawn_hotspot.py
 Then connect the two pi to the spawned network using raspi-config
 Step 6: Run the app.py script on the camera1 pi
 sudo python3 camera1.py
 Step 7: Run the app.py script on the camera2 pi
 sudo python3 camera2.py
 Step 8: Run the app.py script on the main pi
 sudo python3 app.py
 Step 9: Testing the app
 The application will ope