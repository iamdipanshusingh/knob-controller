import base64
import json
import subprocess
import tempfile
from time import sleep
import hid
import pync
from pynput.keyboard import Key, Controller, Listener

keyboard = Controller()
VENDOR_ID = 0x041E
PRODUCT_ID = 0x3287

RESET_TIMEOUT = 0.5  # Seconds of inactivity before resetting counter

# Track modifier key state
shift_pressed = False
ctrl_pressed = False


def on_key_press(key):
    global shift_pressed, ctrl_pressed
    if key == Key.shift_l:
        shift_pressed = True
    elif key == Key.ctrl_l:
        ctrl_pressed = True


def on_key_release(key):
    global shift_pressed, ctrl_pressed
    if key == Key.shift_l:
        shift_pressed = False
    elif key == Key.ctrl_l:
        ctrl_pressed = False


def toggle_play_pause():
    keyboard.press(Key.media_play_pause)
    keyboard.release(Key.media_play_pause)


def mute():
    keyboard.press(Key.media_volume_mute)
    keyboard.release(Key.media_volume_mute)


def next_track():
    keyboard.press(Key.media_next)
    keyboard.release(Key.media_next)


def previous_track():
    keyboard.press(Key.media_previous)
    keyboard.release(Key.media_previous)


def volume_up():
    keyboard.press(Key.media_volume_up)
    keyboard.release(Key.media_volume_up)


def volume_down():
    keyboard.press(Key.media_volume_down)
    keyboard.release(Key.media_volume_down)


# TODO: make use of this artwork
def decode_artwork(artwork_data):
    """Decode base64 artwork and return temp file path"""
    if not artwork_data:
        return None

    try:
        # Handle data URL format
        if artwork_data.startswith("data:"):
            artwork_data = artwork_data.split("base64,")[1]

        # Decode base64
        image_bytes = base64.b64decode(artwork_data)

        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png", dir="/tmp")
        temp_file.write(image_bytes)
        temp_file.close()

        return temp_file.name
    except Exception as e:
        print(f"Artwork decode error: {e}")
        return None


def main():
    global shift_pressed, ctrl_pressed

    device = hid.device()
    device.open(VENDOR_ID, PRODUCT_ID)
    device.set_nonblocking(True)

    print("Listening for knob rotation... Press Ctrl+C to exit")
    print("Left Shift + clockwise → Next track")
    print("Left Shift + counterclockwise → Previous track")
    print("Ctrl + clockwise → Play/Pause")
    print("Ctrl + counterclockwise → Mute")
    print("Normal rotation → Volume (unchanged)")

    try:
        while True:
            data = device.read(64)

            if data:
                if data[1] == 0:
                    continue

                direction = 1 if data[1] == 1 else -1

                if shift_pressed:
                    if direction == 1:
                        next_track()
                    else:
                        previous_track()
                elif ctrl_pressed:
                    if direction == 1:
                        toggle_play_pause()
                    else:
                        mute()
                else:
                    if direction == 1:
                        volume_up()
                    else:
                        volume_down()

    except KeyboardInterrupt:
        print("\nStopped listening")
    finally:
        device.close()


if __name__ == "__main__":
    # Start keyboard listener in background thread
    listener = Listener(on_press=on_key_press, on_release=on_key_release)
    listener.start()

    try:
        main()
    finally:
        listener.stop()
