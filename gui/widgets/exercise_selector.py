"""
Exercise selector dropdown widget
"""
import customtkinter as ctk
import gui.config.constants as config

class ExerciseSelector:
    def __init__(self, parent, initial_exercise="Squats", on_change_callback=None):
        """
        Initialize exercise selector
        
        Args:
            parent: Parent widget
            initial_exercise: Initial exercise selection
            on_change_callback: Callback function when exercise changes
        """
        self.parent = parent
        self.current_exercise = initial_exercise
        self.on_change_callback = on_change_callback
        self.dropdown = None
        
        self.create_widget()
    
    def create_widget(self):
        """Create the exercise selector dropdown"""
        # Container frame for better styling
        self.container = ctk.CTkFrame(self.parent, fg_color="transparent")
        
        # Label
        self.label = ctk.CTkLabel(
            self.container,
            text="EXERCISE",
            font=ctk.CTkFont(size=config.FONT_SIZE_MEDIUM, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_ACCENT
        )
        self.label.pack(pady=(0, 10))
        
        # Dropdown
        self.dropdown = ctk.CTkOptionMenu(
            self.container,
            values=["Squats", "Push-ups", "Curls"],
            dynamic_resizing=True,
            command=self._on_exercise_changed,
            font=ctk.CTkFont(size=config.FONT_SIZE_MEDIUM, weight=config.FONT_WEIGHT_BOLD),
            dropdown_font=ctk.CTkFont(size=config.FONT_SIZE_TINY, weight=config.FONT_WEIGHT_BOLD),
            width=config.DROPDOWN_WIDTH,
            height=config.DROPDOWN_HEIGHT,
            corner_radius=config.CORNER_RADIUS_SMALL,
            fg_color=config.COLOR_DROPDOWN_LABEL,
            button_color=config.COLOR_ACCENT,
            button_hover_color=config.COLOR_STAT_CARD_BG2,
            text_color=config.COLOR_BACKGROUND,
            dropdown_hover_color=config.COLOR_ACCENT,
            dropdown_text_color=config.COLOR_BACKGROUND
        )
        self.dropdown.set(self.current_exercise)
        self.dropdown.pack(pady=(0, 25))
    
    def _on_exercise_changed(self, choice):
        """Handle exercise selection change"""
        self.current_exercise = choice
        if self.on_change_callback:
            self.on_change_callback(choice)
    
    def pack(self, **kwargs):
        """Pack the container"""
        return self.container.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the container"""
        return self.container.grid(**kwargs)
    
    def place(self, **kwargs):
        """Place the container"""
        return self.container.place(**kwargs)
    
    def get_widget(self):
        """Get the container widget"""
        return self.container
    
    def get_dropdown(self):
        """Get the dropdown widget"""
        return self.dropdown
    
    def set_exercise(self, exercise):
        """Set current exercise"""
        if self.dropdown and exercise in ["Squats", "Push-ups", "Curls"]:
            self.current_exercise = exercise
            self.dropdown.set(exercise)
    
    def get_exercise(self):
        """Get current exercise"""
        return self.current_exercise
    
    def enable(self):
        """Enable the dropdown"""
        if self.dropdown:
            self.dropdown.configure(state="normal")
    
    def disable(self):
        """Disable the dropdown"""
        if self.dropdown:
            self.dropdown.configure(state="disabled")
    
    def is_enabled(self):
        """Check if dropdown is enabled"""
        return self.dropdown.cget("state") == "normal" if self.dropdown else False
    
    def set_change_callback(self, callback):
        """Set callback for exercise changes"""
        self.on_change_callback = callback
        if self.dropdown and callback:
            self.dropdown.configure(command=callback)
    
    def get_exercise_mapping(self, display_name=None):
        """
        Get exercise mapping for backend
        
        Args:
            display_name: Display name to map (optional)
        
        Returns:
            Dictionary mapping or specific backend type
        """
        exercise_map = {
            "Squats": "squat",
            "Push-ups": "pushup", 
            "Curls": "curl"
        }
        
        if display_name:
            return exercise_map.get(display_name, "squat")
        return exercise_map
    
    def get_backend_type(self, display_name=None):
        """
        Get backend exercise type
        
        Args:
            display_name: Display name to convert (uses current if None)
        
        Returns:
            Backend exercise type string
        """
        if display_name is None:
            display_name = self.current_exercise
        return self.get_exercise_mapping(display_name)