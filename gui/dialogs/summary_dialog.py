"""
Workout summary dialog
"""
import customtkinter as ctk
import gui.config.constants as config

class SummaryDialog:
    def __init__(self, parent, db):
        self.parent = parent
        self.db = db
    
    def show(self, session_id):
        """Show workout summary dialog"""
        try:
            summary = self.db.get_session_summary(session_id)
            
            if not summary:
                print("No summary data available")
                return
            
            # Create popup window
            popup = ctk.CTkToplevel(self.parent)
            popup.title("Workout Complete!")
            popup.geometry("400x500")
            popup.configure(fg_color=config.COLOR_BACKGROUND)
            popup.transient(self.parent)
            popup.grab_set()
            
            # Center the popup
            self._center_window(popup)
            
            # Create dialog content
            self._create_content(popup, summary)
            
        except Exception as e:
            print(f"Error showing workout summary: {e}")
    
    def _center_window(self, window):
        """Center window on screen"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_content(self, parent, summary):
        """Create dialog content"""
        # Title
        title_label = ctk.CTkLabel(
            parent,
            text="Workout Complete!",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=config.COLOR_DROPDOWN_LABEL
        )
        title_label.pack(pady=20)
        
        # Summary frame
        summary_frame = ctk.CTkFrame(
            parent, 
            fg_color=config.COLOR_FRAME_SUMMARY, 
            corner_radius=config.CORNER_RADIUS_LARGE
        )
        summary_frame.pack(pady=(0, 20), padx=20, fill="both", expand=True)
        
        # Summary content
        summary_text = self._generate_summary_text(summary)
        
        summary_label = ctk.CTkLabel(
            summary_frame,
            text=summary_text,
            font=ctk.CTkFont(size=12),
            justify="left",
            text_color=config.COLOR_TEXT_PRIMARY
        )
        summary_label.pack(pady=20, padx=20)
        
        # Close button
        close_button = ctk.CTkButton(
            parent,
            text="Close",
            command=parent.destroy,
            width=100,
            fg_color=config.COLOR_SUCCESS,
            hover_color=config.COLOR_SUCCESS_HOVER
        )
        close_button.pack(pady=(0, 20))
    
    def _generate_summary_text(self, summary):
        """Generate formatted summary text"""
        session_data = summary.get('session', {})
        duration = session_data.get('total_duration_seconds') or 0
        minutes = duration // 60
        seconds = duration % 60

        text = f"Duration: {minutes}m {seconds}s\n\n"
        text += f"Summary:\n\n"

        total_reps = 0
        total_excellent = 0
        total_good = 0
        total_poor = 0

        for exercise_set in summary.get('exercise_sets', []):
            text += f"{exercise_set['exercise_name'].upper()}:\n"
            text += f"  Reps: {exercise_set['total_reps']}\n"
            text += f"  Excellent: {exercise_set['excellent_reps']}\n"
            text += f"  Good: {exercise_set['good_reps']}\n"
            text += f"  Poor: {exercise_set['poor_reps']}\n\n"

            total_reps += exercise_set['total_reps']
            total_excellent += exercise_set['excellent_reps']
            total_good += exercise_set['good_reps']
            total_poor += exercise_set['poor_reps']

        text += f"Total: {total_reps} reps "
        text += f"({total_excellent} excellent, {total_good} good, {total_poor} poor)"

        return text