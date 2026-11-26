import json
import os
import queue
import sys
import time

from eeg import ClickDetector, EegError, MentalCommands

HERE = os.path.dirname(os.path.abspath(__file__))
USAGE = "Usage: python main.py calibrate | eeg | run [--no-eeg]     (see README.md)"
TAKEOVER_PIXELS = 6
TAKEOVER_PAUSE_SECONDS = 2


def load_config():
    with open(os.path.join(HERE, "config.json")) as f:
        return json.load(f)


def start_eeg(config, on_click, show=False):
    detector = ClickDetector(config["left_click_command"], config["right_click_command"],
                             config["threshold"], config["hold_samples"], config["cooldown_seconds"])

    def on_command(action, power):
        click = detector.update(action, power)
        if show:
            print(f'{action:<10} {power:4.2f} {"=" * int(power * 30)}' + (f"   <-- {click.upper()} CLICK" if click else ""))
        if click:
            on_click(click)

    print("Connecting to Emotiv Cortex...")
    eeg = MentalCommands(config["client_id"], config["client_secret"], config["profile"],
                         config.get("headset_id", ""), on_command)
    eeg.start()
    print(f'EEG ready. Profile "{config["profile"]}" loaded.')
    return eeg


def cmd_calibrate(config):
    from eye_tracker import EyeTracker
    tracker = EyeTracker(config["camera"])
    try:
        tracker.calibrate()
    finally:
        tracker.close()


def cmd_eeg(config):
    eeg = start_eeg(config, lambda click: None, show=True)
    try:
        while not eeg.error:
            time.sleep(0.2)
        print("EEG stopped:", eeg.error)
    finally:
        eeg.close()


def cmd_run(config, use_eeg):
    from pynput.mouse import Button, Controller
    from eye_tracker import EyeTracker

    if sys.platform == "darwin":
        from ApplicationServices import AXIsProcessTrusted
        if not AXIsProcessTrusted():
            sys.exit("This terminal app is not allowed to control the mouse.\nAllow it in System Settings > "
                     "Privacy & Security > Accessibility, then quit and reopen the terminal and try again.")

    clicks = queue.Queue()
    tracker = EyeTracker(config["camera"])
    eeg = None
    try:
        tracker.start()
        if use_eeg:
            eeg = start_eeg(config, clicks.put)
        mouse = Controller()
        last_set = None
        paused_until = 0
        print("Running. Ctrl+C to stop. Move your real mouse to pause eye control for 2 seconds.")
        while not (eeg and eeg.error):
            time.sleep(0.005)
            gaze = tracker.read()
            now = time.monotonic()

            x, y = mouse.position
            if last_set and abs(x - last_set[0]) + abs(y - last_set[1]) > TAKEOVER_PIXELS:
                paused_until = now + TAKEOVER_PAUSE_SECONDS
            last_set = (x, y)

            if gaze is not None and now >= paused_until:
                last_set = gaze
                mouse.position = gaze

            while not clicks.empty():
                click = clicks.get()
                mouse.click(Button.left if click == "left" else Button.right)
                print(f"{click} click")
        print("EEG stopped:", eeg.error)
    finally:
        tracker.close()
        if eeg:
            eeg.close()


def main():
    args = sys.argv[1:]
    if not args or args[0] not in ("calibrate", "eeg", "run"):
        sys.exit(USAGE)
    config = load_config()
    try:
        if args[0] == "calibrate":
            cmd_calibrate(config)
        elif args[0] == "eeg":
            cmd_eeg(config)
        else:
            cmd_run(config, use_eeg="--no-eeg" not in args)
    except EegError as e:
        sys.exit(f"EEG problem: {e}")
    except RuntimeError as e:
        sys.exit(str(e))
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
