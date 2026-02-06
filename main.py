import hid
import subprocess

# Replace with your device's IDs from step 2
VENDOR_ID = 0x041E
PRODUCT_ID = 0x3287


def toggle_play_pause():
    # macOS AppleScript to play/pause
    subprocess.run(["osascript", "-e", 'tell application "Music" to playpause'])
    # Or for Spotify: tell application "Spotify" to playpause
    print("Play/Pause toggled!")


def forward():
    subprocess.run(["osascript", "-e", 'tell application "Music" to next track'])
    print("Forward")


def backward():
    subprocess.run(["osascript", "-e", 'tell application "Music" to previous track'])
    print("Backward")


try:
    device = hid.device()
    device.open(VENDOR_ID, PRODUCT_ID)
    device.set_nonblocking(True)

    print("Listening for knob clicks... Press Ctrl+C to exit")

    previous_state = None

    counter = 0
    while True:
        data = device.read(64)
        if data:
            if data[1] == 0:
                continue
            if data[1] == 1:
                counter += 1
            elif data[1] == 2:
                counter -= 1

            previous_state = data[1]

            if counter > 10:
                forward()
                counter = 0
            elif counter < -10:
                backward()
                counter = 0


except KeyboardInterrupt:
    print("\nStopped listening")
except Exception as e:
    print(f"Error: {e}")
finally:
    device.close()
