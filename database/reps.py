# reps.py
import sqlite3
from typing import Dict, Any


class RepRepository:
    def __init__(self, conn):
        self.conn = conn

    def log_rep(self, set_id: int, rep_number: int, form_quality: str, 
                peak_angle: float, duration_seconds: float) -> bool:
        
        """Log an individual rep with detailed metrics"""
        with self.conn.connection_lock:
            try:
                # Validate form quality
                valid_qualities = ['excellent', 'good', 'poor']
                if form_quality not in valid_qualities:
                    raise ValueError(f"Invalid form quality: {form_quality}. Must be one of {valid_qualities}")
                
                # Insert the rep
                self.conn.cursor.execute("""
                    INSERT INTO reps (set_id, rep_number, form_quality, peak_angle, duration_seconds)
                    VALUES (?, ?, ?, ?, ?)
                """, (set_id, rep_number, form_quality, peak_angle, duration_seconds))
                
                # Update the exercise set counters
                quality_column = f"{form_quality}_reps"
                self.conn.cursor.execute(f"""
                    UPDATE exercise_sets
                    SET total_reps = total_reps + 1,
                        {quality_column} = {quality_column} + 1
                    WHERE set_id = ?
                """, (set_id,))
                
                self.conn.commit()
                return True
            except (sqlite3.Error, ValueError) as e:
                print(f"Error logging rep: {e}")
                self.conn.rollback()
                return False

    # def get_reps_for_set(self, set_id: int) -> List[Dict[str, Any]]:
    #     """Get all reps for a specific set"""
    #     try:
    #         self.conn.cursor.execute("""
    #             SELECT rep_id, rep_number, form_quality, peak_angle, duration_seconds, timestamp
    #             FROM reps
    #             WHERE set_id = ?
    #             ORDER BY rep_number
    #         """, (set_id,))
            
    #         rows = self.conn.cursor.fetchall()
    #         return [dict(row) for row in rows]
    #     except sqlite3.Error as e:
    #         print(f"Error getting reps: {e}")
    #         return []

    def get_rep_stats(self, set_id: int) -> Dict[str, Any]:
        """Get statistics for reps in a set"""
        try:
            self.conn.cursor.execute("""
                SELECT 
                    COUNT(*) as total_reps,
                    AVG(peak_angle) as avg_peak_angle,
                    MIN(peak_angle) as min_peak_angle,
                    MAX(peak_angle) as max_peak_angle,
                    AVG(duration_seconds) as avg_duration,
                    SUM(CASE WHEN form_quality = 'excellent' THEN 1 ELSE 0 END) as excellent_reps,
                    SUM(CASE WHEN form_quality = 'good' THEN 1 ELSE 0 END) as good_reps,
                    SUM(CASE WHEN form_quality = 'poor' THEN 1 ELSE 0 END) as poor_reps
                FROM reps
                WHERE set_id = ?
            """, (set_id,))
            
            row = self.conn.cursor.fetchone()
            return dict(row) if row else {}
        except sqlite3.Error as e:
            print(f"Error getting rep stats: {e}")
            return {}