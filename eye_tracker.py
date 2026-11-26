import os

import cv2
import numpy as np
import pygame
from gazefollower import GazeFollower
from gazefollower.camera import WebCamCamera

CALIBRATION_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calibration.npy")
JUMP_PIXELS = 120
FIXATION_FRAMES = 15


class EyeTracker:
    def __init__(self, camera=0):
        probe = cv2.VideoCapture(camera)
        opened = probe.isOpened()
        probe.release()
        if not opened:
            raise RuntimeError(f"Cannot open camera {camera}. Allow camera access for your terminal in "
                               'System Settings > Privacy & Security > Camera, or change "camera" in config.json.')
        self.gf = GazeFollower(camera=WebCamCamera(webcam_id=camera), use_multiprocessing=False)
        self.last_time = None
        self.window = []
        self.away = []

    def calibrate(self):
        self.gf.calibrate()
        pygame.quit()
        if not self.gf.calibration.has_calibrated:
            raise RuntimeError("Calibration failed. Check lighting and camera, then try again.")
        np.save(CALIBRATION_PATH, self.gf.calibration.weights)
        print("Calibration saved.")

    def start(self):
        if not os.path.exists(CALIBRATION_PATH):
            raise RuntimeError("No calibration yet. Run:  python main.py calibrate")
        self.gf.calibration.weights = np.load(CALIBRATION_PATH)
        self.gf.calibration.has_calibrated = True
        self.gf.start_sampling()

    def read(self):
        info = self.gf.get_gaze_info()
        if info is None or not info.status or info.timestamp == self.last_time:
            return None
        self.last_time = info.timestamp
        return self.smooth(np.array(info.filtered_gaze_coordinates, dtype=float))

    def smooth(self, target):
        if self.window and np.linalg.norm(target - np.mean(self.window, axis=0)) > JUMP_PIXELS:
            self.away.append(target)
            if len(self.away) >= 2:
                self.window, self.away = self.away, []
        else:
            self.away = []
            self.window = (self.window + [target])[-FIXATION_FRAMES:]
        x, y = np.clip(np.mean(self.window, axis=0), 0, self.gf.screen_size - 1)
        return float(x), float(y)

    def close(self):
        self.gf.release()
