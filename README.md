# AI Workout Form Analyzer

A desktop application that uses computer vision to analyze workout form in real time. It tracks body landmarks through your webcam using Google's MediaPipe pose detection, counts reps, and provides feedback on exercise form quality.

Supported exercises: Squats, Push-ups, and Bicep Curls.

## Features

- Real-time pose detection and form analysis via webcam
- Rep counting with form quality ratings (Excellent / Good / Poor)
- Per-user calibration for personalized form thresholds
- Workout history with calendar view and statistics
- First-time setup wizard for profile creation and exercise calibration
- Persistent local database for workout tracking

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| mediapipe | 0.10.7 | Human pose detection |
| opencv-python | 4.8.1.78 | Camera access and image processing |
| opencv-contrib-python | 4.13.0.92 | Additional OpenCV modules |
| customtkinter | 5.2.2 | GUI framework |
| numpy | 2.4.2 | Numerical computation |
| matplotlib | 3.10.8 | Data visualization and charts |
| Pillow | 12.1.0 | Image handling |

Python 3.11 is required. Developed and tested with Python 3.11.14.

A webcam is required for exercise tracking.

## Setup

1. Clone the repository and navigate into the project directory:

```bash
git clone <repository-url>
cd Workout_Analyzer
```

2. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the application:

```bash
python main.py
```

On first launch, a setup wizard will walk you through creating a user profile and calibrating exercise thresholds. Workout data is stored locally at `~/.workout_analyzer/`.

## Pre-built Application

A standalone macOS `.app` bundle is available in `dist/`. This was built with PyInstaller and does not require a Python installation or virtual environment to run. To rebuild it:

```bash
source venv/bin/activate
pyinstaller --clean -y main.spec
```

## Running Tests

```bash
pytest tests/
```

## Project Structure

```
Workout_Analyzer/
├── main.py              # Application entry point
├── config/              # App constants and user configuration
├── core/                # Workout engine and business logic
├── core_cv/             # Exercise detectors, form analysis, validation
├── cv/                  # MediaPipe pose detection wrapper
├── database/            # SQLite database and repository layer
├── gui/                 # CustomTkinter UI (panels, dialogs, widgets)
├── models/              # Data models (workout state, sessions)
└── tests/               # Unit and integration tests
```
