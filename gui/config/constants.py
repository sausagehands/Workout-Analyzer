"""
GUI Configuration Constants for Workout Analyzer
Modern, cohesive color scheme optimized for fitness applications
UPDATED VERSION: Clean, professional fitness theme
"""
from pathlib import Path
from config.app_constants import resource_path
# ============================================================================
# LAYOUT CONFIGURATION
# ============================================================================

# Window dimensions
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800

# Grid weights (controls proportions)
LAYOUT_MAIN_WEIGHT = 12          # Main area width (75% when 3:1)
LAYOUT_SIDEBAR_WEIGHT = 1       # Sidebar width (25% when 3:1)
LAYOUT_VIDEO_WEIGHT = 1         # Video area height (expandable)
LAYOUT_HEADER_WEIGHT = 0        # Header row (fixed height)
LAYOUT_CONTROLS_WEIGHT = 0      # Controls row (fixed height)

# Grid layout constants (for forms/settings)
GRID_LABEL_WIDTH = 180          # Label column width
GRID_INPUT_WIDTH = 250          # Input field width
GRID_ROW_PADY = 8               # Vertical padding between rows
GRID_COL_PADX = 10              # Horizontal padding between columns

# ============================================================================
# DASHBOARD LAYOUT CONFIGURATION
# ============================================================================

# Dashboard grid weights
DASHBOARD_HEADER_WEIGHT = 0      # Header row (fixed height)
DASHBOARD_CONTENT_WEIGHT = 1     # Main content area (expandable)
DASHBOARD_SIDEBAR_WEIGHT = 0     # Sidebar column (fixed width)
DASHBOARD_MAIN_WEIGHT = 1        # Main column (expandable)

# Dashboard fixed dimensions
DASHBOARD_HEADER_HEIGHT = 80     # Header height
DASHBOARD_SIDEBAR_WIDTH = 280    # Right sidebar width
DASHBOARD_CALENDAR_HEIGHT = 350  # Calendar section height

# Dashboard calendar
CALENDAR_CELL_SIZE = 36          # Calendar day cell size
CALENDAR_HEADER_HEIGHT = 40      # Month/year header height
CALENDAR_DAY_FONT_SIZE = 12      # Day number font size
CALENDAR_NAV_BUTTON_SIZE = 30    # Navigation button size

# Dashboard stat cards
STAT_CARD_HEIGHT = 100           # Stat card height
STAT_CARD_MIN_WIDTH = 150        # Minimum card width
STAT_CARD_PADDING = 15           # Internal padding

# Dashboard colors (inherit from main theme)
COLOR_CALENDAR_WORKOUT = "#00FFE1"   # Green for workout days
COLOR_CALENDAR_TODAY = "#8B5CF6"      # Blue outline for today
COLOR_CALENDAR_HOVER = "#1E293B"      # Hover background
COLOR_STAT_CARD_BG = "#1E293B"
COLOR_STAT_CARD_BG2 = "#6422FF" # Stat card background

# Fixed heights
HEADER_HEIGHT = 60              # Slightly taller for better presence
CONTROLS_HEIGHT = 100

# Padding (spacing around elements)
OUTER_PADDING_X = 10            # Generous outer padding
OUTER_PADDING_Y = 10
SECTION_SPACING = 5            # More space between sections
INNER_PADDING = 10              # Padding inside frames

# Corner radius (roundness of frames)
CORNER_RADIUS_LARGE = 20        # Softer, more modern corners
CORNER_RADIUS_SMALL = 12        # Rounded buttons
CORNER_RADIUS = 15              # Default corner radius

# ============================================================================
# COLOR SCHEME - MODERN FITNESS THEME (UPDATED)
# ============================================================================

# Primary Colors - Clean & Professional Fitness Theme
COLOR_BACKGROUND = "#000000"    # Very light blue-gray background
COLOR_FRAME_HEADER = "transparent" 
# COLOR_FRAME_VID = "#FFFFFF"     # Pure white for video frame - clean contrast
COLOR_FRAME_INFO = "#444444"    # White sidebar for better readability
COLOR_FRAME_FEEDBACK = "#F1F5F9" # Very light blue-gray for feedback
COLOR_FRAME_EXERCISE = "#F1F5F9" # Light background for exercise selector
COLOR_FRAME_HISTORY = "#FFFFFF"  # White for history dialogs
COLOR_FRAME_SUMMARY = "#FFFFFF"  # White for summary dialogs
COLOR_FRAME = "#616161"         # Light gray for general frames
COLOR_ACCENT = "#C5FF50"        # Bright blue - primary accent (unchanged)
COLOR_DROPDOWN_LABEL = "#FFFFFF"
COLOR_TEXT_POP ="#FF0090"
COLOR_TEXT_POP2 ="#00FFE1"


COLOR_SECONDARY_BUTTON = "#ECB024"
COLOR_SECONDARY_BUTTON_HOVER = "#D97706"

# Add this line:
COLOR_SURFACE = "#616161"       # Surface color for panels and containers

# Semantic Colors - Clear visual feedback
COLOR_SUCCESS = "#10B981"       # Emerald green - success/start (unchanged)
COLOR_SUCCESS_DARK = "#059669"  # Darker green for borders
COLOR_ERROR = "#EF4444"         # Coral red - error/stop (unchanged)
COLOR_ERROR_DARK = "#DC2626"    # Darker red for borders
COLOR_WARNING = "#F59E0B"       # Amber yellow - warning/state (unchanged)
COLOR_WARNING_DARK = "#D97706"  # Darker amber for borders

# Text Colors - High contrast for readability
COLOR_TEXT_PRIMARY = "#000000"  # Dark blue-gray for primary text
COLOR_TEXT_HEADER = "#C5FF50"   # Almost black for headers - maximum contrast
COLOR_TEXT_SECONDARY = "#64748B" # Medium blue-gray for secondary text
COLOR_SEPARATOR = "#484848"    # Light gray for separators - subtle
COLOR_SEPARATOR_DARK = COLOR_DROPDOWN_LABEL # Slightly darker for some borders

COLOR_TEXT_ALERT = "#000000"

# Additional Colors for Variety
COLOR_HIGHLIGHT = "#8B5CF6"     # Purple - for highlights (unchanged)

COLOR_SYSTEM_BORDER="#6D28D9"
COLOR_SYSTEM_BORDER_HOVER="#8B5CF6"
 
COLOR_INFO = "#06B6D4"          # Cyan - informational elements (unchanged)

# Button hover effects (color variations)
COLOR_SUCCESS_HOVER = "#059669"  # Darker green on hover (unchanged)
COLOR_ERROR_HOVER = "#DC2626"    # Darker red on hover (unchanged)
COLOR_ACCENT_HOVER = COLOR_STAT_CARD_BG  # Darker blue on hover (unchanged)

# Button colors for specific actions
COLOR_BUTTON_START = COLOR_SUCCESS
COLOR_BUTTON_STOP = COLOR_ERROR
COLOR_BUTTON_RESET = "#94A3B8"   # Neutral gray for reset
COLOR_BUTTON_HISTORY = COLOR_HIGHLIGHT

# ============================================================================
# FONT CONFIGURATION
# ============================================================================

BUTTON_FONT = 'Inter'
BUTTON_FONT_SIZE = 14

# Font sizes - Modern typography scale
FONT_SIZE_TITLE = 34            # Main header - prominent
FONT_SIZE_XL=30
FONT_SIZE_LARGE = 26            # Large text
FONT_SIZE_MEDLARGE = 22
FONT_SIZE_MEDIUM = 18           # Section headers
FONT_SIZE_SMALL = 14            # Normal text
FONT_SIZE_TINY = 12             # Small text/details
FONT_SIZE_REP_DISPLAY = 80      # Rep counter - very prominent
FONT_SIZE_STATE_DISPLAY = 32    # State display - clear

# Font weights (if you want to use them)
FONT_WEIGHT_BOLD = "bold"
FONT_WEIGHT_NORMAL = "normal"

# ============================================================================
# BUTTON & CONTROL SIZES
# ============================================================================

# Button sizes
BUTTON_WIDTH = 160              # Comfortable width
BUTTON_HEIGHT = 52              # Slightly taller for better click area

# Image button sizes (for StateImageButton)
IMAGE_BUTTON_SIZE = 60          # Square buttons for image controls

# Dropdown sizes
DROPDOWN_WIDTH = 260            # Wide enough for text
DROPDOWN_HEIGHT = 44            # Comfortable height

# ============================================================================
# BORDER & SHADOW CONFIGURATION
# ============================================================================

# Border widths
BORDER_WIDTH_NORMAL = 2         # Normal border width
BORDER_WIDTH_THICK = 3          # Thicker border for emphasis

# Shadow colors (for elevated elements)
SHADOW_COLOR = "rgba(0, 0, 0, 0.1)"  # Subtle shadow

# ============================================================================
# ANIMATION & EFFECTS
# ============================================================================

# Animation durations (milliseconds)
ANIMATION_FAST = 150            # Fast animations
ANIMATION_NORMAL = 300          # Normal speed
ANIMATION_SLOW = 500            # Slow/emphatic animations

# Hover transitions
HOVER_TRANSITION = "0.2s ease-in-out"

# ============================================================================
# LAYOUT RATIOS & CALCULATIONS
# ============================================================================

# Derived ratios (calculated, don't modify directly)
MAIN_TO_SIDEBAR_RATIO = LAYOUT_MAIN_WEIGHT / LAYOUT_SIDEBAR_WEIGHT
VIDEO_AREA_RATIO = 16/9         # Standard video aspect ratio

# Calculate sidebar width percentage
SIDEBAR_WIDTH_PERCENTAGE = (LAYOUT_SIDEBAR_WEIGHT / (LAYOUT_MAIN_WEIGHT + LAYOUT_SIDEBAR_WEIGHT)) * 100

# ============================================================================
# QUALITY OF LIFE SETTINGS
# ============================================================================

# Tooltip delay (milliseconds)
TOOLTIP_DELAY = 800             # Delay before showing tooltips

# Auto-hide controls (milliseconds)
AUTO_HIDE_DELAY = 3000          # Time before auto-hiding controls during workout

# Maximum history items to display
MAX_HISTORY_ITEMS = 10

# Video feed settings
VIDEO_UPDATE_INTERVAL = 33      # ~30 FPS (1000ms / 30 = 33.33ms)

# Mirror settings
MIRROR_CAMERA = True  

# ============================================================================
# COLOR PALETTE EXPANSION (for charts/graphs if added later)
# ============================================================================

# Chart colors (consistent with theme)
CHART_COLORS = [
    COLOR_SUCCESS,              # First data series
    COLOR_ACCENT,               # Second data series
    COLOR_HIGHLIGHT,            # Third data series
    COLOR_WARNING,              # Fourth data series
    COLOR_INFO,                 # Fifth data series
]

# Quality indicator colors
COLOR_QUALITY_EXCELLENT = COLOR_SUCCESS
COLOR_QUALITY_GOOD = COLOR_WARNING
COLOR_QUALITY_POOR = COLOR_ERROR

# ============================================================================
# EXERCISE CONFIGURATION
# ============================================================================

# Available exercises
EXERCISE_OPTIONS = ["Squats", "Push-ups", "Curls"]

# Exercise to backend mapping
EXERCISE_MAPPING = {
    "Squats": "squat",
    "Push-ups": "pushup", 
    "Curls": "curl"
}

# Default exercise
DEFAULT_EXERCISE = "Squats"

# ============================================================================
# FEEDBACK MESSAGES
# ============================================================================

# Initial messages
INITIAL_VIDEO_MESSAGE = "Press START to begin"
CAMERA_READY_MESSAGE = "Camera ready! Press START to begin"
WORKOUT_COMPLETE_MESSAGE = "Workout completed!\nPress START to begin new session"

# State messages
STATE_READY = "READY"
STATE_ANALYZING = "ANALYZING"
STATE_COMPLETED = "COMPLETED"
STATE_SWITCHING = "SWITCHING"

# ============================================================================
# ICON PATHS
# ============================================================================

# Get the gui directory (MEIPASS-aware for PyInstaller bundles)
GUI_DIR = Path(resource_path("gui"))

# Icon paths
ICON_DIRECTORY = GUI_DIR / "assets" / "icons"

# Icon folders for each button
ICON_FOLDER_START = f"{ICON_DIRECTORY}/start"
ICON_FOLDER_STOP = f"{ICON_DIRECTORY}/stop"
ICON_FOLDER_RESET = f"{ICON_DIRECTORY}/reset"
ICON_FOLDER_HISTORY = f"{ICON_DIRECTORY}/history"

# Full icon paths for each state
ICON_PATH_START_NORMAL = f"{ICON_FOLDER_START}/normal.png"
ICON_PATH_START_HOVER = f"{ICON_FOLDER_START}/hover.png"
ICON_PATH_START_DISABLED = f"{ICON_FOLDER_START}/disabled.png"

ICON_PATH_STOP_NORMAL = f"{ICON_FOLDER_STOP}/normal.png"
ICON_PATH_STOP_HOVER = f"{ICON_FOLDER_STOP}/hover.png"
ICON_PATH_STOP_DISABLED = f"{ICON_FOLDER_STOP}/disabled.png"

ICON_PATH_RESET_NORMAL = f"{ICON_FOLDER_RESET}/normal.png"
ICON_PATH_RESET_HOVER = f"{ICON_FOLDER_RESET}/hover.png"
ICON_PATH_RESET_DISABLED = f"{ICON_FOLDER_RESET}/disabled.png"

ICON_PATH_HISTORY_NORMAL = f"{ICON_FOLDER_HISTORY}/normal.png"
ICON_PATH_HISTORY_HOVER = f"{ICON_FOLDER_HISTORY}/hover.png"
ICON_PATH_HISTORY_DISABLED = f"{ICON_FOLDER_HISTORY}/disabled.png"

# Icon sizes
ICON_SIZE_SMALL = (24, 24)
ICON_SIZE_MEDIUM = (32, 32)
ICON_SIZE_LARGE = (48, 48)

# Simple icon path constants for compatibility with existing code
ICON_PATH_START = str(ICON_PATH_START_NORMAL)
ICON_PATH_STOP = str(ICON_PATH_STOP_NORMAL)
ICON_PATH_RESET = str(ICON_PATH_RESET_NORMAL)
ICON_PATH_HISTORY = str(ICON_PATH_HISTORY_NORMAL)
ICON_PATH_START_HOVER = str(ICON_PATH_START_HOVER)
ICON_PATH_STOP_HOVER = str(ICON_PATH_STOP_HOVER)
ICON_PATH_RESET_HOVER = str(ICON_PATH_RESET_HOVER)
ICON_PATH_HISTORY_HOVER = str(ICON_PATH_HISTORY_HOVER)


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_color(color_code):
    """Validate hex color code format"""
    if not isinstance(color_code, str):
        return False
    if not color_code.startswith('#'):
        return False
    if len(color_code) != 7:
        return False
    try:
        int(color_code[1:], 16)
        return True
    except ValueError:
        return False

def validate_dimension(value):
    """Validate dimension values"""
    return isinstance(value, int) and value > 0

def get_exercise_backend_type(display_name):
    """Get backend exercise type from display name"""
    return EXERCISE_MAPPING.get(display_name, "squat")

def get_quality_color(quality):
    """Get color for quality rating"""
    quality_colors = {
        'excellent': COLOR_QUALITY_EXCELLENT,
        'good': COLOR_QUALITY_GOOD,
        'poor': COLOR_QUALITY_POOR
    }
    return quality_colors.get(quality, COLOR_TEXT_SECONDARY)

# ============================================================================
# DEBUG/DEVELOPMENT SETTINGS
# ============================================================================

# Debug mode
DEBUG_MODE = True

# Show layout guides (for development)
SHOW_LAYOUT_GUIDES = True

# Log GUI events
LOG_GUI_EVENTS = True

# Test mode (uses mock objects)
TEST_MODE = True

# ============================================================================
# COLOR SCHEME VALIDATION
# ============================================================================

# Validate all colors on import
if DEBUG_MODE:
    color_vars = {k: v for k, v in globals().items() if k.startswith('COLOR_')}
    for name, value in color_vars.items():
        if isinstance(value, str) and value.startswith('#'):
            if not validate_color(value):
                print(f"Warning: Invalid color format for {name}: {value}")

    print(f"Loaded GUI configuration with {len(color_vars)} colors")
    print(f"Layout: {LAYOUT_MAIN_WEIGHT}:{LAYOUT_SIDEBAR_WEIGHT} ({SIDEBAR_WIDTH_PERCENTAGE:.0f}% sidebar)")
    print(f"Exercises: {', '.join(EXERCISE_OPTIONS)}")

# ============================================================================
# EXPORTED CONSTANTS FOR EASY ACCESS
# ============================================================================

# __all__ = [
#     # Layout
#     'WINDOW_WIDTH', 'WINDOW_HEIGHT',
#     'LAYOUT_MAIN_WEIGHT', 'LAYOUT_SIDEBAR_WEIGHT', 'LAYOUT_VIDEO_WEIGHT',
#     'HEADER_HEIGHT', 'CONTROLS_HEIGHT',
#     'OUTER_PADDING_X', 'OUTER_PADDING_Y', 'SECTION_SPACING', 'INNER_PADDING',
#     'CORNER_RADIUS_LARGE', 'CORNER_RADIUS_SMALL',
#     
#     # Colors
#     'COLOR_BACKGROUND', 'COLOR_FRAME_HEADER', 'COLOR_FRAME_VID', 'COLOR_FRAME_INFO',
#     'COLOR_FRAME_FEEDBACK', 'COLOR_FRAME_EXERCISE', 'COLOR_FRAME_HISTORY',
#     'COLOR_FRAME_SUMMARY', 'COLOR_FRAME', 'COLOR_ACCENT',
#     'COLOR_SUCCESS', 'COLOR_SUCCESS_DARK', 'COLOR_ERROR', 'COLOR_ERROR_DARK',
#     'COLOR_WARNING', 'COLOR_WARNING_DARK', 'COLOR_TEXT_PRIMARY', 'COLOR_TEXT_HEADER',
#     'COLOR_TEXT_SECONDARY', 'COLOR_SEPARATOR', 'COLOR_SEPARATOR_DARK',
#     'COLOR_HIGHLIGHT', 'COLOR_INFO', 'COLOR_SUCCESS_HOVER', 'COLOR_ERROR_HOVER',
#     'COLOR_ACCENT_HOVER', 'COLOR_BUTTON_START', 'COLOR_BUTTON_STOP',
#     'COLOR_BUTTON_RESET', 'COLOR_BUTTON_HISTORY',
#     
#     # Fonts
#     'BUTTON_FONT', 'FONT_SIZE_TITLE', 'FONT_SIZE_LARGE', 'FONT_SIZE_MEDIUM', 'FONT_SIZE_SMALL',
#     'FONT_SIZE_TINY', 'FONT_SIZE_REP_DISPLAY', 'FONT_SIZE_STATE_DISPLAY',
#     'FONT_WEIGHT_BOLD', 'FONT_WEIGHT_NORMAL',
#     
#     # Controls
#     'BUTTON_WIDTH', 'BUTTON_HEIGHT', 'IMAGE_BUTTON_SIZE',
#     'DROPDOWN_WIDTH', 'DROPDOWN_HEIGHT',
#     'BORDER_WIDTH_NORMAL', 'BORDER_WIDTH_THICK',
#     
#     # Exercises
#     'EXERCISE_OPTIONS', 'EXERCISE_MAPPING', 'DEFAULT_EXERCISE',
#     
#     # Messages
#     'INITIAL_VIDEO_MESSAGE', 'CAMERA_READY_MESSAGE', 'WORKOUT_COMPLETE_MESSAGE',
#     'STATE_READY', 'STATE_ANALYZING', 'STATE_COMPLETED', 'STATE_SWITCHING',
#     
#     # Icons
#     'ICON_DIRECTORY', 'ICON_PATH_START', 'ICON_PATH_STOP',
#     'ICON_PATH_RESET', 'ICON_PATH_HISTORY',
#     'ICON_SIZE_SMALL', 'ICON_SIZE_MEDIUM', 'ICON_SIZE_LARGE',
#     
#     # Quality of Life
#     'TOOLTIP_DELAY', 'AUTO_HIDE_DELAY', 'MAX_HISTORY_ITEMS',
#     'VIDEO_UPDATE_INTERVAL', 'SIDEBAR_WIDTH_PERCENTAGE',
#     
#     # Functions
#     'validate_color', 'validate_dimension', 'get_exercise_backend_type', 'get_quality_color',
#     
#     # Debug
#     'DEBUG_MODE', 'SHOW_LAYOUT_GUIDES', 'LOG_GUI_EVENTS', 'TEST_MODE'
# ]

__all__ = [k for k, v in globals().items() if k.isupper()]