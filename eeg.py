import threading
import time

from emotiv.cortex import Cortex

START_TIMEOUT_SECONDS = 120


class EegError(Exception):
    pass


class MentalCommands:
    def __init__(self, client_id, client_secret, profile, headset_id, on_command):
        if not client_id or not client_secret or "PASTE" in client_id + client_secret + profile:
            raise EegError("Put your Emotiv client_id, client_secret and profile in config.json (see README).")
        self.profile = profile
        self.on_command = on_command
        self.ready = threading.Event()
        self.error = None
        self.closing = False
        self.stage = "waiting for EMOTIV Launcher approval and a connected headset"
        self.cortex = Cortex(client_id, client_secret)
        self.cortex.set_wanted_profile(profile)
        if headset_id:
            self.cortex.set_wanted_headset(headset_id)
        self.cortex.bind(create_session_done=self.on_create_session_done,
                         query_profile_done=self.on_query_profile_done,
                         load_unload_profile_done=self.on_load_unload_profile_done,
                         new_com_data=self.on_new_com_data,
                         inform_error=self.on_inform_error)

    def start(self):
        threading.Thread(target=self.run, daemon=True).start()
        deadline = time.monotonic() + START_TIMEOUT_SECONDS
        while not self.ready.wait(0.2):
            if self.error:
                self.close()
                raise EegError(self.error)
            if time.monotonic() > deadline:
                self.close()
                raise EegError(f"Timed out while {self.stage}.")

    def run(self):
        try:
            self.cortex.open()
        except Exception as e:
            self.error = str(e)
        if not self.closing and not self.error:
            self.error = "The connection to Cortex closed. Is EMOTIV Launcher running?"

    def close(self):
        self.closing = True
        if hasattr(self.cortex, "ws"):
            self.cortex.close()

    def on_create_session_done(self, *args, **kwargs):
        self.stage = "looking up your training profile"
        self.cortex.query_profile()

    def on_query_profile_done(self, *args, **kwargs):
        profiles = kwargs.get("data")
        if self.profile in profiles:
            self.stage = f'loading profile "{self.profile}" (quit EmotivBCI if it is open)'
            self.cortex.get_current_profile()
        else:
            self.error = (f'Training profile "{self.profile}" not found. Your profiles: {profiles}. '
                          'Set "profile" in config.json to one you trained in EmotivBCI.')

    def on_load_unload_profile_done(self, *args, **kwargs):
        if kwargs.get("isLoaded"):
            self.stage = "waiting for mental command data"
            self.cortex.sub_request(["com"])
        else:
            self.cortex.setup_profile(self.profile, "load")

    def on_new_com_data(self, *args, **kwargs):
        data = kwargs.get("data")
        self.ready.set()
        self.on_command(data["action"], data["power"])

    def on_inform_error(self, *args, **kwargs):
        error = kwargs.get("error_data")
        self.error = f'{error.get("message")} (Cortex code {error.get("code")})'


class ClickDetector:
    def __init__(self, left_action, right_action, threshold=0.5, hold_samples=3, cooldown=1.0):
        self.buttons = {left_action: "left", right_action: "right"}
        self.threshold = threshold
        self.hold_samples = hold_samples
        self.cooldown = cooldown
        self.current = None
        self.count = 0
        self.fired = False
        self.last_click = float("-inf")

    def update(self, action, power, now=None):
        now = time.monotonic() if now is None else now
        button = self.buttons.get(action) if power >= self.threshold else None
        if button != self.current:
            self.current, self.count, self.fired = button, 0, False
        if button is None:
            return None
        self.count += 1
        if self.fired or self.count < self.hold_samples or now - self.last_click < self.cooldown:
            return None
        self.fired = True
        self.last_click = now
        return button
