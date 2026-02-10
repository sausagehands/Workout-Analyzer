from typing import Optional, Dict, List
from database.database_connection import DatabaseConnection
from database.schema import create_tables
from database.users import UserRepository
from database.sessions import SessionRepository
from database.exercise import ExerciseSetRepository
from database.reps import RepRepository
from database.stats import StatsRepository
from config.app_constants import DATABASE_PATH


class WorkoutDatabase:
    """
    Main database class that orchestrates all repositories.
    Manages SQLite database for workout history with flexible exercise types.
    """

    def __init__(self, db_path: str = DATABASE_PATH):
        # Initialize connection
        self.connection = DatabaseConnection(db_path)
        
        # Create tables if they don't exist
        with self.connection.connection_lock:
            try:
                create_tables(self.connection.cursor)
                self.connection.commit()
            except Exception as e:
                print(f"Error creating tables: {e}")
                raise
        
        # Initialize all repositories
        self.users = UserRepository(self.connection)
        self.sessions = SessionRepository(self.connection)
        self.exercise_sets = ExerciseSetRepository(self.connection)
        self.reps = RepRepository(self.connection)
        self.stats = StatsRepository(self.connection)
    
    # ========== CONVENIENCE METHODS ==========
    
    def start_workout(self, user_id: Optional[int] = None) -> Optional[int]:
        """Convenience method to start a workout session"""
        return self.sessions.start_session(user_id)
    
    def end_workout(self, session_id: int, notes: str = "") -> bool:
        """Convenience method to end a workout session"""
        return self.sessions.end_session(session_id, notes)
    
    def add_exercise_to_workout(self, session_id: int, exercise_name: str) -> Optional[int]:
        """Convenience method to add an exercise to a workout"""
        return self.exercise_sets.create_exercise_set(session_id, exercise_name)
    
    def log_rep_with_stats(self, set_id: int, rep_number: int, form_quality: str,
                          peak_angle: float, duration_seconds: float) -> bool:
        """Convenience method to log a rep with statistics"""
        return self.reps.log_rep(set_id, rep_number, form_quality, peak_angle, duration_seconds)
    
    def get_workout_summary(self, session_id: int) -> Dict:
        """Get comprehensive workout summary"""
        return self.sessions.get_session_summary(session_id)
    
    # def get_lifetime_stats(self) -> Dict:
    #     """Get lifetime workout statistics"""
    #     return self.stats.get_total_stats()
    
    def get_streaks(self) -> Dict:
        """Get streak information"""
        return self.stats.get_streak_data()
    
    def get_total_stats(self) -> Dict:
        """Get all-time statistics (legacy method for backward compatibility)"""
        return self.stats.get_total_stats()
    
    # ========== LEGACY METHODS FOR BACKWARD COMPATIBILITY ==========
    
    def start_session(self, user_id: Optional[int] = None) -> Optional[int]:
        """Legacy method for backward compatibility - use start_workout() instead"""
        return self.start_workout(user_id)
    
    def end_session(self, session_id: int, notes: str = "") -> bool:
        """Legacy method for backward compatibility - use end_workout() instead"""
        return self.end_workout(session_id, notes)
    
    def create_exercise_set(self, session_id: int, exercise_name: str) -> Optional[int]:
        """Legacy method for backward compatibility - use add_exercise_to_workout() instead"""
        return self.add_exercise_to_workout(session_id, exercise_name)
    
    def log_rep(self, set_id: int, rep_number: int, form_quality: str,
                peak_angle: float, duration_seconds: float) -> bool:
        """Legacy method for backward compatibility - use log_rep_with_stats() instead"""
        return self.log_rep_with_stats(set_id, rep_number, form_quality, peak_angle, duration_seconds)
    
    def update_exercise_set(self, set_id: int, stats: Dict) -> bool:
        """Legacy method for backward compatibility"""
        return self.exercise_sets.update_exercise_set_stats(set_id, stats)
    
    def get_session_summary(self, session_id: int) -> Dict:
        """Legacy method for backward compatibility - use get_workout_summary() instead"""
        return self.get_workout_summary(session_id)
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """Legacy method for backward compatibility"""
        return self.sessions.get_recent_sessions(limit)
    
    # def get_exercise_history(self, exercise_type: str, limit: int = 30) -> List[Dict]:
    #     """Legacy method for backward compatibility"""
    #     return self.exercise_sets.get_exercise_history(exercise_type, limit)
    
    def get_streak_data(self) -> Dict:
        """Legacy method for backward compatibility - use get_streaks() instead"""
        return self.get_streaks()

    # def consolidate_old_data(self, retention_days: int = 365) -> Dict:
    #     """Consolidate data older than retention_days into monthly summaries"""
    #     return self.stats.consolidate_old_data(retention_days)

    # def get_monthly_stats(self, year: int = None, month: int = None) -> List[Dict]:
    #     """Get consolidated monthly statistics"""
    #     return self.stats.get_monthly_stats(year, month)
    
    # ========== UTILITY METHODS ==========
    
    # def backup_database(self, backup_path: str) -> bool:
    #     """Create a backup of the database"""
    #     import shutil
    #     try:
    #         shutil.copy2(self.connection.db_path, backup_path)
    #         return True
    #     except Exception as e:
    #         print(f"Error backing up database: {e}")
    #         return False
    
    # def vacuum(self):
    #     """Optimize database (reclaim unused space)"""
    #     with self.connection.connection_lock:
    #         try:
    #             self.connection.cursor.execute("VACUUM")
    #             self.connection.commit()
    #         except Exception as e:
    #             print(f"Error vacuuming database: {e}")
    
    def close(self):
        """Close database connection"""
        self.connection.close()
    
    # def __enter__(self):
    #     """Context manager entry"""
    #     return self
    
    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     """Context manager exit"""
    #     self.close()