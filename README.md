# Eye + brain mouse v2.0

Eyes move the cursor (webcam). Mental commands from an Emotiv headset left and right click.

Started late 2024, developed through late 2025. v2.0 is the reworked version for 2026.

## Setup

1. Install: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
2. EMOTIV Launcher: log in and connect the headset.
3. EmotivBCI: train Neutral, Push and Pull in a profile, then quit EmotivBCI.
4. Create a Cortex app at <https://www.emotiv.com/my-account/cortex-apps/>.
5. Copy `config.example.json` to `config.json`. Fill in `client_id`, `client_secret`, `profile`.
6. macOS: allow Camera and Accessibility for your terminal, then restart it.

## Use

| Command | What it does |
| --- | --- |
| `.venv/bin/python main.py calibrate` | Eye calibration. Space to start, look at each dot, Space to accept or R to redo. |
| `.venv/bin/python main.py eeg` | Shows live mental commands and when a click would fire. Clicks nothing. |
| `.venv/bin/python main.py run` | Eyes move the cursor, commands click. Add `--no-eeg` for eyes only. |

Stop with Ctrl+C. Moving the real mouse pauses eye control for 2 seconds.

Recalibrate when your seat, lighting or screen changes. Best results: even light on
your face, 50 to 60 cm from the camera, head still.

## Settings (`config.json`)

| Setting | Meaning |
| --- | --- |
| `left_click_command`, `right_click_command` | Trained command for each click. Default `push`, `pull`. |
| `threshold` | Command strength needed, 0 to 1. Raise it to stop accidental clicks. |
| `hold_samples` | Samples in a row above threshold. 8 per second, so 3 is about 0.4 s. |
| `cooldown_seconds` | Minimum time between clicks. |
| `camera` | Camera number. Try `1` if `0` is the wrong camera. |
| `headset_id` | Empty uses the first headset found. |

## Files

| File | Purpose |
| --- | --- |
| `main.py` | Command line program. |
| `eye_tracker.py` | Eye tracking with [GazeFollower](https://github.com/GanchengZhu/GazeFollower), plus cursor smoothing. |
| `eeg.py` | Mental commands to clicks. |
| `emotiv/`, `certificates/` | EMOTIV's official [Cortex example](https://github.com/Emotiv/cortex-example) code and certificate, unchanged. |

## Limits

- Webcam eye tracking is accurate to about 2 cm on screen: fine for large buttons, not small links.
- Ear-EEG has few sensors, so telling two commands apart takes a lot of training.
- Single left and right clicks only.

## Licence

MIT for this repository's code (`LICENSE`). EMOTIV's files are under `emotiv/LICENSE`.
GazeFollower is CC BY-NC-SA, so the program as a whole is for non-commercial use only.
