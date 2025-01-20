import json
import time
import os
import sys

def find_circuitpy_drive():
    """Find the CircuitPython drive"""
    if sys.platform == "darwin":  # macOS
        base = "/Volumes"
        for drive in os.listdir(base):
            if drive.upper() == "CIRCUITPY":
                return os.path.join(base, drive)
    elif sys.platform == "win32":  # Windows
        for drive in range(ord('A'), ord('Z')+1):
            drive_letter = chr(drive) + ":\\"
            if os.path.exists(drive_letter):
                try:
                    volume_name = os.path.basename(drive_letter.rstrip('\\'))
                    if volume_name.upper() == "CIRCUITPY":
                        return drive_letter
                except:
                    continue
    return None

def simulate_countdown_trigger(name, duration):
    """
    Simulates a countdown trigger by writing to a test file
    on the CircuitPython drive
    """
    circuitpy_path = find_circuitpy_drive()
    if not circuitpy_path:
        print("Error: Could not find CIRCUITPY drive!")
        return False

    # Create test data
    test_data = {
        "name": str(name),  # Ensure it's a string
        "duration": int(duration),  # Ensure it's an integer
        "timestamp": time.time()
    }
    
    print("\nPreparing to write test data:")
    print(json.dumps(test_data, indent=2))
    
    # Write to test file on CIRCUITPY drive
    try:
        file_path = os.path.join(circuitpy_path, "test_trigger.json")
        
        # First verify we can write to the drive
        try:
            with open(os.path.join(circuitpy_path, "test_write"), "w") as f:
                f.write("test")
            os.remove(os.path.join(circuitpy_path, "test_write"))
            print("Write test successful")
        except Exception as e:
            print(f"Warning: Drive might be read-only: {str(e)}")
        
        # Write the actual test file
        print(f"Writing to: {file_path}")
        with open(file_path, "w") as f:
            json_str = json.dumps(test_data)
            print(f"Writing JSON: {json_str}")
            f.write(json_str)
            f.flush()
            os.sync() if hasattr(os, 'sync') else None  # Force write to disk
            
        # Verify the file was written
        if os.path.exists(file_path):
            print("File was written successfully")
            # Read back the file to verify content
            with open(file_path, "r") as f:
                content = f.read()
                print(f"Verification - file contains: {content}")
            return True
        else:
            print("Error: File was not written")
            return False
            
    except Exception as e:
        print(f"Error writing test file: {str(e)}")
        return False

if __name__ == "__main__":
    print("CircuitPython Countdown Test Tool")
    print("--------------------------------")
    
    # Check for CIRCUITPY drive first
    circuitpy_path = find_circuitpy_drive()
    if not circuitpy_path:
        print("Error: CIRCUITPY drive not found!")
        print("Please make sure your MatrixPortal is connected and mounted.")
        sys.exit(1)
    else:
        print(f"Found CIRCUITPY drive at: {circuitpy_path}")
    
    while True:
        print("\nTest Countdown Menu:")
        print("1. Start a new countdown")
        print("2. Exit")
        
        choice = input("Choose an option: ")
        
        if choice == "1":
            name = input("Enter countdown name: ")
            try:
                duration = int(input("Enter duration in seconds: "))
                if duration <= 0:
                    print("Duration must be positive!")
                    continue
                    
                print("\nStarting countdown with:")
                print(f"Name: {name}")
                print(f"Duration: {duration} seconds")
                
                if simulate_countdown_trigger(name, duration):
                    print("\nCountdown triggered successfully!")
                    print("Watch the matrix display for the countdown.")
                else:
                    print("\nFailed to trigger countdown")
                    print("Check the serial console for more information.")
            except ValueError:
                print("Please enter a valid number for duration")
        elif choice == "2":
            break
        else:
            print("Invalid choice") 