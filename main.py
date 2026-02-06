import hid
import time
from pynput.keyboard import Key, Controller, Listener

keyboard = Controller()
VENDOR_ID = 0x041E
PRODUCT_ID = 0x3287

# Configuration
ROTATION_THRESHOLD = 10  # Number of ticks to trigger action
RESET_TIMEOUT = 0.5  # Seconds of inactivity before resetting counter

# Track modifier key state
shift_pressed = False


def on_key_press(key):
    global shift_pressed
    if key == Key.shift_l:
        shift_pressed = True


def on_key_release(key):
    global shift_pressed
    if key == Key.shift_l:
        shift_pressed = False


def toggle_play_pause():
    keyboard.press(Key.media_play_pause)
    keyboard.release(Key.media_play_pause)
    print("Play/Pause toggled!")


def next_track():
    keyboard.press(Key.media_next)
    keyboard.release(Key.media_next)
    print("Next track")


def previous_track():
    keyboard.press(Key.media_previous)
    keyboard.release(Key.media_previous)
    print("Previous track")


def main():
    global shift_pressed

    device = hid.device()
    device.open(VENDOR_ID, PRODUCT_ID)
    device.set_nonblocking(True)

    print("Listening for knob rotation... Press Ctrl+C to exit")
    print(f"Quick rotate ({ROTATION_THRESHOLD} ticks) → Play/Pause")
    print("Left Shift + clockwise → Next track")
    print("Left Shift + counterclockwise → Previous track")
    print("Normal rotation → Volume (unchanged)")

    counter = 0
    last_activity = time.time()

    try:
        while True:
            data = device.read(64)

            if counter != 0 and (time.time() - last_activity) > RESET_TIMEOUT:
                counter = 0

            if data:
                if data[1] == 0:
                    continue

                direction = (
                    1 if data[1] == 1 else -1
                )

                if shift_pressed:
                    if direction == 1:
                        next_track()
                    else:
                        previous_track()

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
