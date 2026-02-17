import base64
import subprocess
import tempfile
import time
import hid
from pynput.keyboard import Key, Controller, Listener

keyboard = Controller()

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


def get_device(device_name="Creative Pebble"):
    keywords = device_name.split(" ")

    for device in hid.enumerate():
        product = device["product_string"]
        if any(keyword.lower() in product.lower() for keyword in keywords):
            print(f"Found device: {product}")
            print("-" * 50)
            print(f"Vendor ID: 0x{device['vendor_id']:04x}")
            print(f"Product ID: 0x{device['product_id']:04x}")
            print(f"Product: {device['product_string']}")
            print(f"Manufacturer: {device['manufacturer_string']}")
            print("-" * 50)
            return {
                "vendor_id": int(f"0x{device['vendor_id']:04x}", 16),
                "product_id": int(f"0x{device['product_id']:04x}", 16),
            }

    return None


def get_volume():
    cmd = "output volume of (get volume settings)"
    result = subprocess.run(["osascript", "-e", cmd], capture_output=True, text=True)
    return result.stdout


def set_volume(volume):
    cmd = f"set volume output volume {volume}"
    result = subprocess.run(["osascript", "-e", cmd], capture_output=True, text=True)
    return result.stdout


def listen_for_knob(device):
    try:
        while True:
            data = device.read(64)

            if data:
                if data[1] == 0:
                    continue

                direction = data[1]

                if shift_pressed:
                    volume = get_volume()
                    if direction == 1:
                        next_track()
                    else:
                        previous_track()
                    set_volume(volume)
                elif ctrl_pressed:
                    if direction == 1:
                        volume = get_volume()
                        toggle_play_pause()
                        set_volume(volume)
                    else:
                        mute()
                else:
                    if direction == 1:
                        volume_up()
                    else:
                        volume_down()

    finally:
        device.close()


def check_device_and_listen():
    device = None
    try:
        while not device:
            device = get_device()
            if not device:
                raise Exception("Device not found")

        VENDOR_ID = device["vendor_id"]
        PRODUCT_ID = device["product_id"]

        device = hid.device()
        device.open(VENDOR_ID, PRODUCT_ID)
        device.set_nonblocking(True)

        print("Listening for knob rotation... Press Ctrl+C to exit")
        print("Left Shift + clockwise → Next track")
        print("Left Shift + counterclockwise → Previous track")
        print("Ctrl + clockwise → Play/Pause")
        print("Ctrl + counterclockwise → Mute")
        print("Normal rotation → Volume (unchanged)")

        listen_for_knob(device)
    except Exception as e:
        print(e)
        time.sleep(1)
        check_device_and_listen()
    except KeyboardInterrupt:
        print("\nStopped listening")


def main():
    global shift_pressed, ctrl_pressed

    check_device_and_listen()


if __name__ == "__main__":
    listener = Listener(on_press=on_key_press, on_release=on_key_release)
    listener.start()

    try:
        main()
    finally:
        listener.stop()
