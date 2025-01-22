import supervisor
import time
import sys

print("\n" * 2)
print("=" * 40)
print("MatrixPortal M4 Startup")
print("=" * 40)

# Enable serial output for debugging
try:
    supervisor.runtime.serial_connected = True
except:
    pass

def start_wifi_server():
    """Start the WiFi server from wifi.py"""
    try:
        print("Importing wifi server module...")
        import wifi
        print("WiFi server module imported successfully")
    except Exception as e:
        print("Error importing wifi server:", str(e))
        print("Retrying in 5 seconds...")
        time.sleep(5)
        supervisor.reload()

# Start the server
print("Starting WiFi server...")
start_wifi_server() 