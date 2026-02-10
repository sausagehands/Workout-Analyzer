"""
Fixed StateImageButton without recursion issues - FIXED VERSION
"""
import customtkinter as ctk
from typing import Optional
from PIL import Image, ImageDraw

class StateImageButton(ctk.CTkButton):
    """Custom button with different images for normal, hover, and disabled states"""
    def __init__(self, master, 
                 normal_img: ctk.CTkImage,
                 hover_img: Optional[ctk.CTkImage] = None,
                 disabled_img: Optional[ctk.CTkImage] = None,
                 command=None,
                 tooltip_text: str = "",
                 **kwargs):
        
        # Store images
        self.normal_img = normal_img
        self.hover_img = hover_img or normal_img
        self.disabled_img = disabled_img or normal_img
        
        # Track current state
        self._current_state = "normal"
        self._is_hovering = False
        
        # Initialize with normal image
        kwargs['image'] = normal_img
        kwargs['text'] = ""
        
        # Store original kwargs
        self._original_kwargs = kwargs.copy()
        
        super().__init__(master, **kwargs)
        
        if command:
            self.configure(command=command)
        
        # Bind hover events
        self.bind("<Enter>", self._on_mouse_enter)
        self.bind("<Leave>", self._on_mouse_leave)
    
    def _on_mouse_enter(self, event):
        """Mouse enters button"""
        if self._current_state == "normal":
            self._is_hovering = True
            self._update_image_direct()
    
    def _on_mouse_leave(self, event):
        """Mouse leaves button"""
        self._is_hovering = False
        self._update_image_direct()
    
    def _update_image_direct(self):
        """Update the button image directly without recursion"""
        if self._current_state == "disabled":
            image_to_use = self.disabled_img
        elif self._is_hovering:
            image_to_use = self.hover_img
        else:
            image_to_use = self.normal_img
        
        # Use direct attribute assignment instead of configure()
        self._image = image_to_use
        
        # Force redraw if the widget exists
        if self.winfo_exists():
            try:
                # Try to update the image directly
                self._draw_image()
            except:
                # Fallback to after() schedule
                self.after(10, self._draw_image)
    
    def _draw_image(self):
        """Force the button to redraw its image"""
        try:
            if hasattr(self, '_draw'):
                self._draw()
        except:
            pass
    
    def set_state(self, state: str):
        """Set button state: 'normal' or 'disabled'"""
        valid_states = ["normal", "disabled"]
        if state not in valid_states:
            raise ValueError(f"State must be one of {valid_states}")
        
        self._current_state = state
        
        # Update CTkButton state
        if state == "disabled":
            # Use parent's configure for state only
            super().configure(state="disabled")
            self._is_hovering = False  # Can't hover when disabled
        else:
            super().configure(state="normal")
        
        # Update image without recursion
        self._update_image_direct()
    
    def enable(self):
        """Enable the button"""
        self.set_state("normal")
    
    def disable(self):
        """Disable the button"""
        self.set_state("disabled")
    
    def is_enabled(self) -> bool:
        """Check if button is enabled"""
        return self._current_state != "disabled"
    
    # Override configure carefully to avoid recursion
    def configure(self, **kwargs):
        """Handle configure calls, especially for state changes"""
        # Handle image changes separately
        if "image" in kwargs:
            self.normal_img = kwargs.pop("image")
            self._update_image_direct()
        
        # Handle state changes
        if "state" in kwargs:
            state = kwargs.pop("state")
            if state in ["normal", "disabled"]:
                self.set_state(state)
        
        # Handle command separately
        if "command" in kwargs:
            command = kwargs.pop("command")
            super().configure(command=command)
        
        # Pass any remaining kwargs to parent (except image/state)
        if kwargs:
            super().configure(**kwargs)
    
    @staticmethod
    def create_fallback_image(color, size=32):
        """Create a simple circle image for fallback"""
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([0, 0, size, size], fill=color)
        return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))