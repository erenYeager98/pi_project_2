___

# Pi Camera 2 Multi-Device Setup Guide

## Overview
This guide outlines the steps for setting up a Raspberry Pi network with two Pi Cameras, enabling remote streaming and control through a main Raspberry Pi. Follow each step carefully to complete the setup.

## Requirements
- **Main Pi**: Raspberry Pi with an HDMI display
- **Camera Pis**: Two Raspberry Pis with attached cameras
- **OS**: Raspbian (Raspberry Pi OS) installed on all devices

---

## Steps

### 1. Prepare the Raspberry Pi Devices

#### Step 1: Install Raspbian OS
1. Download and install Raspberry Pi OS on each Raspberry Pi using the Raspberry Pi Imager or similar tool.
2. Boot up each Raspberry Pi, ensuring they all connect to the same network (via the main Pi hotspot or a router).

#### Step 2: Enable Camera Interface on Each Pi
1. Open a terminal on each Raspberry Pi.
2. Run the following command to open the Raspberry Pi configuration menu:
   ```bash
   sudo raspi-config
  
3. Go to **Interface Options** → **Camera** → **Enable**.
4. Reboot the Pi to apply changes:
   ```bash
   sudo reboot
   ```

#### Step 3: Install Required Packages (on All Pis)
1. Update the system:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
2. Install Python 3, PyQt5, and OpenCV:
   ```bash
   sudo apt install python3 python3-pyqt5 python3-opencv -y
   ```
3. Install the Picamera2 library:
   ```bash
   sudo apt install python3-picamera2 -y
   ```

---

### 2. Network Setup and Connection

#### Step 4: Set Up the Network Hotspot on the Main Pi
1. Use the `script_to_spawn_hotspot.py` script to initiate a hotspot on the main Pi:
   ```bash
   sudo python script_to_spawn_hotspot.py
   ```
2. Connect each Camera Pi to the hotspot network via `raspi-config` on each device.

---

### 3. Running the Camera Applications

#### Step 5: Run the Camera Scripts on Each Camera Pi
1. SSH into **Camera Pi 1** and run:
   ```bash
   sudo python3 camera1.py
   ```
2. SSH into **Camera Pi 2** and run:
   ```bash
   sudo python3 camera2.py
   ```

#### Step 6: Configure and Run the Main App
1. Modify `app.py` on the main Pi by replacing placeholders for Camera Pi IP addresses with the actual IPs for camera1 and camera2.
2. Run the main app on the main Pi:
   ```bash
   sudo python3 app.py
   ```

---

### 4. Testing the Application

Once the application is running on all devices, you can test the setup. The application should open and display video feeds from both Camera Pis on the main Pi’s display.

***NOTE*** : *Change the ip address of the serving pis as per the ip configuration of the individual pis, if you are on a testing environment, you have to manually change it.*

---
### 5. Building the Application
Install pyinstaller to build the application 
```bash 
sudo su
pip install pyinstaller
```
Generate a single binary executable using the following command 
```bash
pyinstaller --onefile main_app.py
```
