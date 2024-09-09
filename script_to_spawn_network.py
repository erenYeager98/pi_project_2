#Change WIfi SSID password as per your wish, dont' forget to configure the client pi to connect to the same!
import subprocess

def run_command(command):
    """Run a shell command."""
    subprocess.run(command, shell=True, check=True)

def append_to_file(file_path, content):
    """Append content to a file."""
    with open(file_path, 'a') as file:
        file.write(content)

def replace_file(file_path, content):
    """Replace file content."""
    with open(file_path, 'w') as file:
        file.write(content)

def main():
    try:
        # Step 16: Install dnsmasq and hostapd
        run_command('sudo apt install hostapd dnsmasq -y')
        
        # Step 17: Stop the services temporarily
        run_command('sudo systemctl stop hostapd')
        run_command('sudo systemctl stop dnsmasq')
        
        # Step 18: Configure Static IP for wlan0
        dhcpcd_conf = """
interface wlan0
static ip_address=192.168.0.1/24
nohook wpa_supplicant
"""
        append_to_file('/etc/dhcpcd.conf', dhcpcd_conf)
        
        # Step 19: Take backup of the default configuration
        run_command('sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig')
        
        # Step 20: Create new configuration file
        dnsmasq_conf = """
interface=wlan0
dhcp-range=192.168.0.2,192.168.0.20,255.255.255.0,24h
"""
        replace_file('/etc/dnsmasq.conf', dnsmasq_conf)
        
        # Step 21: Configure network settings
        hostapd_conf = """
interface=wlan0
driver=nl80211
ssid=Your_SSID_Name
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=Your_Passphrase
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
"""
        replace_file('/etc/hostapd/hostapd.conf', hostapd_conf)
        
        # Step 22: Point to the hostapd file
        daemon_conf = """
DAEMON_CONF="/etc/hostapd/hostapd.conf"
"""
        append_to_file('/etc/default/hostapd', daemon_conf)
        
        # Step 23: Execute statements to finalize the settings
        run_command('sudo systemctl unmask hostapd')
        run_command('sudo systemctl enable hostapd')
        run_command('sudo systemctl start hostapd')
        run_command('sudo systemctl enable dnsmasq')
        run_command('sudo systemctl start dnsmasq')

        print("Hotspot setup completed successfully.")
    
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
