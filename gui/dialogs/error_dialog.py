"""
Error dialog for displaying error messages
"""
import customtkinter as ctk
import gui.config.constants as config

class ErrorDialog:
    def __init__(self, parent):
        self.parent = parent
    
    def show(self, message):
        """Show error dialog with message"""
        def show_dialog():
            popup = ctk.CTkToplevel(self.parent)
            popup.title("Error")
            popup.geometry("350x200")
            popup.configure(fg_color=config.COLOR_STAT_CARD_BG)
            popup.transient(self.parent)
            popup.grab_set()
            
            # Center the popup
            self._center_window(popup)
            
            # Create dialog content
            self._create_content(popup, message)
        
        # Schedule on main thread
        self.parent.after(0, show_dialog)
    
    def _center_window(self, window):
        """Center window on screen"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_content(self, parent, message):
        """Create error dialog content"""
        # Error icon/title
        error_title = ctk.CTkLabel(
            parent,
            text="Error",
            font=ctk.CTkFont(size=config.FONT_SIZE_MEDIUM, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_ERROR
        )
        error_title.pack(pady=20)
        
        # Error message
        error_message = ctk.CTkLabel(
            parent,
            text=message,
            font=ctk.CTkFont(size=config.FONT_SIZE_MEDIUM, weight=config.FONT_WEIGHT_BOLD),
            wraplength=300,
            justify="center",
            text_color=config.COLOR_DROPDOWN_LABEL
        )
        error_message.pack(pady=10, padx=20)
        
        # OK button
        ok_button = ctk.CTkButton(
            parent,
            text="OK",
            command=parent.destroy,
            width=100,
            fg_color=config.COLOR_ERROR,
            hover_color=config.COLOR_ERROR_HOVER
        )
        ok_button.pack(pady=20)