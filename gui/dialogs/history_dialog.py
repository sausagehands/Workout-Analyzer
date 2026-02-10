"""
Workout history dialog
"""
import customtkinter as ctk
from datetime import datetime
import gui.config.constants as config

class HistoryDialog:
    def __init__(self, parent, db):
        self.parent = parent
        self.db = db
    
    def show(self):
        """Show history dialog"""
        try:
            recent = self.db.get_recent_sessions(limit=config.MAX_HISTORY_ITEMS)
            
            # Create popup window
            popup = ctk.CTkToplevel(self.parent)
            popup.title("Workout History")
            popup.geometry("500x600")
            popup.configure(fg_color=config.COLOR_BACKGROUND)
            popup.transient(self.parent)
            popup.grab_set()
            
            # Center the popup
            self._center_window(popup)
            
            # Create dialog content
            self._create_content(popup, recent)
            
        except Exception as e:
            print(f"Error showing history: {e}")
    
    def _center_window(self, window):
        """Center window on screen"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_content(self, parent, recent_sessions):
        """Create dialog content"""
        # Title
        title_label = ctk.CTkLabel(
            parent,
            text="Workout History",
            font=ctk.CTkFont(size=config.FONT_SIZE_TITLE, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_ACCENT
        )
        title_label.pack(pady=20)
        
        # Create scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(parent, height=400, fg_color=config.COLOR_STAT_CARD_BG)
        scroll_frame.pack(pady=(0, 20), padx=20, fill="both", expand=True)
        
        if not recent_sessions:
            self._show_no_data_message(scroll_frame)
        else:
            self._show_sessions_list(scroll_frame, recent_sessions)
        
        # Close button
        close_button = ctk.CTkButton(
            parent,
            text="Close",
            command=parent.destroy,
            width=100,
            fg_color=config.COLOR_ACCENT,
            text_color=config.COLOR_BACKGROUND,
            font=ctk.CTkFont(size=config.FONT_SIZE_SMALL, weight=config.FONT_WEIGHT_BOLD),
            hover_color=config.COLOR_TEXT_POP2
        )
        close_button.pack(pady=(0, 20))
    
    def _show_no_data_message(self, parent):
        """Show message when no data available"""
        no_data_label = ctk.CTkLabel(
            parent,
            text="No workouts yet!\n\nStart your first workout to see history here.",
            font=ctk.CTkFont(size=config.FONT_SIZE_SMALL, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_TEXT_POP
        )
        no_data_label.pack(pady=20)
    
    def _show_sessions_list(self, parent, sessions):
        """Show list of workout sessions (only those with reps > 0)"""
        has_valid = False
        for session in sessions:
            summary = self.db.get_session_summary(session['session_id'])

            if not summary or not summary.get('session'):
                continue

            # Skip sessions where no reps were completed
            total_reps = sum(
                es.get('total_reps', 0) for es in summary.get('exercise_sets', [])
            )
            if total_reps == 0:
                continue

            has_valid = True
            session_data = summary['session']

            # Format date
            try:
                start_time = datetime.fromisoformat(session_data['start_time'])
                date_str = start_time.strftime("%b %d, %I:%M %p")
            except (ValueError, AttributeError, TypeError):
                date_str = "Unknown date"

            # Create session frame
            session_frame = ctk.CTkFrame(
                parent,
                fg_color=config.COLOR_STAT_CARD_BG,
                corner_radius=config.CORNER_RADIUS_SMALL,
                border_width=2,
                border_color=config.COLOR_SEPARATOR
            )
            session_frame.pack(fill="x", pady=5, padx=5)

            # Session info
            info_text = f"{date_str}\n"
            duration = session_data.get('total_duration_seconds') or 0
            minutes = duration // 60
            seconds = duration % 60
            info_text += f"Duration: {minutes}m {seconds}s\n\n"

            for exercise_set in summary.get('exercise_sets', []):
                if exercise_set.get('total_reps', 0) == 0:
                    continue
                info_text += f"{exercise_set['exercise_name'].title()}: "
                info_text += f"{exercise_set['total_reps']} reps "
                info_text += f"({exercise_set['excellent_reps']} excellent, {exercise_set['good_reps']} good)\n"
            
            session_label = ctk.CTkLabel(
                session_frame,
                text=info_text,
                font=ctk.CTkFont(size=config.FONT_SIZE_TINY, weight=config.FONT_WEIGHT_BOLD),
                text_color=config.COLOR_DROPDOWN_LABEL,
                justify="left",
                wraplength=400
            )
            session_label.pack(padx=10, pady=10)

        if not has_valid:
            self._show_no_data_message(parent)