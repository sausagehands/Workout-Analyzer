# AI Workout Form Analyzer

A macOS desktop app that watches you work out through your webcam, counts your reps, and rates your form in real time. It also catches cheated reps.

Supported exercises: squats, push-ups, and bicep curls.

Built as my capstone project for Ada Developers Academy.

## What it does

- **Real-time pose detection:** tracks 33 body landmarks per frame with MediaPipe Pose and computes joint angles (knee for squats, elbow for push-ups and curls). It reads whichever side of your body the camera sees best, so you don't have to face a particular way.
- **Rep counting:** each exercise has its own state machine that moves between positions using angle thresholds, with a cooldown so one rep can't be counted twice.
- **Form ratings:** every completed rep is rated Excellent, Good, or Poor from its peak joint angle, with live feedback while you're mid-rep.
- **Anti-cheat validation:** separate validators watch other landmarks (like back alignment) to confirm the movement was a real rep. If a rep doesn't pass, it isn't counted.
- **Auto-calibration:** after your first few valid reps, the app sets thresholds from your own range of motion. It skips calibration if those reps are too inconsistent, so a bad start doesn't skew your thresholds.
- **Workout history:** a dashboard with a calendar view and lifetime stats, backed by a local SQLite database.
- **First-run setup wizard** for creating your profile.

## How it's built

- The computer vision pipeline is fully separate from the GUI: `WorkoutEngine` processes frames and returns results, and the CustomTkinter interface only displays them.
- Each exercise detector inherits from a shared base detector, so adding an exercise means writing one new class.
- The database uses a repository pattern (users, sessions, sets, reps, stats) behind a single facade.
- Packaged as a standalone macOS `.app` with PyInstaller.

The core CV pipeline, state machines, and architecture are my own hands-on work. I used AI assistance for the PyInstaller packaging, some of the GUI, and the angle math.

## Requirements

- Python 3.11 (developed and tested with 3.11.14)
- A webcam
- macOS (the packaged app is macOS-only; running from source may work elsewhere but hasn't been tested)

| Package | Version | Purpose |
|---|---|---|
| mediapipe | 0.10.7 | Human pose detection |
| opencv-python | 4.8.1.78 | Camera access and image processing |
| opencv-contrib-python | 4.13.0.92 | Additional OpenCV modules |
| customtkinter | 5.2.2 | GUI framework |
| numpy | 2.4.2 | Numerical computation |
| matplotlib | 3.10.8 | Charts |
| Pillow | 12.1.0 | Image handling |

## Setup

```bash
git clone https://github.com/sausagehands/Workout-Analyzer.git
cd Workout-Analyzer
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

On first launch, the setup wizard walks you through creating a profile. Workout data is stored locally in `~/.workout_analyzer/`.

To reset the setup wizard while testing, run `python tools/reset_setup.py`.

## Building the macOS app

```bash
source venv/bin/activate
pyinstaller --clean -y main.spec
```

The app is written to `dist/`.

## Running tests

```bash
pytest tests/
```

Unit tests cover the angle math, each exercise detector, form analysis and validation, and the database layer. An integration test covers a full workout lifecycle.

## Project structure

```
Workout-Analyzer/
├── main.py              # Entry point
├── config/              # App constants and per-user configuration
├── core/                # Workout engine (CV pipeline orchestration, calibration)
├── core_cv/
│   ├── detection/       # Per-exercise rep-counting state machines
│   ├── analysis/        # Angle math, form analysis, landmark utilities
│   └── validation/      # Anti-cheat validators and rep history
├── cv/                  # MediaPipe pose detection wrapper
├── database/            # SQLite schema and repositories
├── gui/                 # CustomTkinter UI (dashboard, setup wizard, panels, dialogs)
├── models/              # Workout session and state models
├── tools/               # Developer utilities
└── tests/               # Unit and integration tests
```

## What's next

The original plan was to train my own pose detection model from scratch. I switched to MediaPipe to finish on time, and training a custom model is still on my list.
