# main.spec
# -*- mode: python -*-

import os
from pathlib import Path
import mediapipe as mp
from PyInstaller.utils.hooks import collect_data_files

# -----------------------
# Paths
# -----------------------
# SPECPATH is provided by PyInstaller — it's the directory containing this spec file
project_root = Path(SPECPATH).resolve()

main_script = str(project_root / "main.py")

# -----------------------
# Collect assets
# -----------------------
datas = []

# 1) GUI icons — preserve the relative folder structure so
#    resource_path("gui/assets/icons/...") works inside the bundle.
icon_folders = [
    "gui/assets/icons/dashboard",
    "gui/assets/icons/history",
    "gui/assets/icons/next",
    "gui/assets/icons/previous",
    "gui/assets/icons/reset",
    "gui/assets/icons/settings",
    "gui/assets/icons/start",
    "gui/assets/icons/stop",
]

for folder in icon_folders:
    folder_path = project_root / folder
    if folder_path.exists():
        for f in folder_path.glob("*"):
            if f.is_file():
                datas.append((str(f), folder))

# 2) MediaPipe model files — pose detection + pose landmark at minimum.
#    Include all modules so other exercises can be added later.
mp_root = Path(mp.__file__).parent
mp_modules = mp_root / "modules"
if mp_modules.exists():
    for model_file in mp_modules.rglob("*"):
        if model_file.is_file() and model_file.suffix in (".tflite", ".binarypb", ".pbtxt", ".txt"):
            dest = str(model_file.parent.relative_to(mp_root))
            datas.append((str(model_file), f"mediapipe/{dest}"))

# -----------------------
# PyInstaller build
# -----------------------
block_cipher = None

a = Analysis(
    [main_script],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "cv2",
        "mediapipe",
        "mediapipe.python.solutions.pose",
        "mediapipe.python.solutions.drawing_utils",
        "mediapipe.python.solutions.drawing_styles",
        "PIL",
        "PIL._imaging",
        "PIL._imagingtk",
        "numpy",
        "customtkinter",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="WorkoutAnalyzer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX often breaks on Apple Silicon
    console=True,  # Set to False for GUI-only (no terminal window)
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="WorkoutAnalyzer",
)

# macOS .app bundle
icon_path = project_root / "icon.icns"
app = BUNDLE(
    coll,
    name="WorkoutAnalyzer.app",
    icon=str(icon_path) if icon_path.exists() else None,
    bundle_identifier="com.workoutanalyzer.app",
    info_plist={
        'NSCameraUsageDescription': 'This app needs camera access to analyze your workout form.',
        'NSHighResolutionCapable': True,
        'LSBackgroundOnly': False,  # Override PyInstaller default — required for camera permission
    },
)
