# exercise.py
import sqlite3
from typing import Optional, Dict, Any, List


class ExerciseSetRepository:
    def __init__(self, conn):
        self.conn = conn

    def create_exercise_set(self, session_id: int, exercise_name: str) -> Optional[int]:
        """Create a new exercise set within a session"""
        with self.conn.connection_lock:
            try:
                # Get or create exercise type
                self.conn.cursor.execute("""
                    SELECT exercise_type_id
                    FROM exercise_types
                    WHERE name = ?
                """, (exercise_name,))

                row = self.conn.cursor.fetchone()
                if not row:
                    # Create new exercise type if it doesn't exist
                    self.conn.cursor.execute("""
                        INSERT INTO exercise_types (name)
                        VALUES (?)
                    """, (exercise_name,))
                    exercise_type_id = self.conn.cursor.lastrowid
                else:
                    exercise_type_id = row['exercise_type_id']
                
                # Create exercise set
                self.conn.cursor.execute("""
                    INSERT INTO exercise_sets (session_id, exercise_type_id)
                    VALUES (?, ?)
                """, (session_id, exercise_type_id))
                
                self.conn.commit()
                return self.conn.cursor.lastrowid
            except sqlite3.Error as e:
                print(f"Error creating exercise set: {e}")
                self.conn.rollback()
                return None

    def update_exercise_set_stats(self, set_id: int, stats: Dict[str, Any]) -> bool:
        """Update exercise set with final statistics"""
        with self.conn.connection_lock:
            try:
                self.conn.cursor.execute("""
                    UPDATE exercise_sets
                    SET total_reps = ?,
                        excellent_reps = ?,
                        good_reps = ?,
                        poor_reps = ?,
                        average_angle = ?,
                        min_angle = ?,
                        max_angle = ?,
                        duration_seconds = ?
                    WHERE set_id = ?
                """, (
                    stats.get('total_reps', 0),
                    stats.get('excellent_reps', 0),
                    stats.get('good_reps', 0),
                    stats.get('poor_reps', 0),
                    stats.get('average_angle'),
                    stats.get('min_angle'),
                    stats.get('max_angle'),
                    stats.get('duration_seconds'),
                    set_id
                ))
                
                if self.conn.cursor.rowcount == 0:
                    print(f"Warning: Set {set_id} not found")
                    return False
                
                self.conn.commit()
                return True
            except sqlite3.Error as e:
                print(f"Error updating exercise set stats: {e}")
                self.conn.rollback()
                return False

    # def get_exercise_set(self, set_id: int) -> Optional[Dict[str, Any]]:
    #     """Get exercise set details"""
    #     with self.conn.connection_lock:
    #         try:
    #             self.conn.cursor.execute("""
    #                 SELECT es.*, et.name as exercise_name
    #                 FROM exercise_sets es
    #                 JOIN exercise_types et ON es.exercise_type_id = et.exercise_type_id
    #                 WHERE es.set_id = ?
    #             """, (set_id,))

    #             row = self.conn.cursor.fetchone()
    #             return dict(row) if row else None
    #         except sqlite3.Error as e:
    #             print(f"Error getting exercise set: {e}")
    #             return None

    def get_exercise_history(self, exercise_name: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Get history for a specific exercise type"""
        with self.conn.connection_lock:
            try:
                self.conn.cursor.execute("""
                    SELECT es.*, et.name as exercise_name, ws.start_time as session_date
                    FROM exercise_sets es
                    JOIN exercise_types et ON es.exercise_type_id = et.exercise_type_id
                    JOIN workout_sessions ws ON es.session_id = ws.session_id
                    WHERE et.name = ?
                      AND es.total_reps > 0
                    ORDER BY es.created_at DESC
                    LIMIT ?
                """, (exercise_name, limit))

                rows = self.conn.cursor.fetchall()
                return [dict(row) for row in rows]
            except sqlite3.Error as e:
                print(f"Error getting exercise history: {e}")
                return []

    # def get_all_exercise_types(self) -> List[Dict[str, Any]]:
    #     """Get all available exercise types"""
    #     with self.conn.connection_lock:
    #         try:
    #             self.conn.cursor.execute("""
    #                 SELECT et.*, COUNT(es.set_id) as usage_count
    #                 FROM exercise_types et
    #                 LEFT JOIN exercise_sets es ON et.exercise_type_id = es.exercise_type_id
    #                 GROUP BY et.exercise_type_id
    #                 ORDER BY et.name
    #             """)

    #             rows = self.conn.cursor.fetchall()
    #             return [dict(row) for row in rows]
    #         except sqlite3.Error as e:
    #             print(f"Error getting exercise types: {e}")
    #             return []

    # def add_exercise_type(self, name: str) -> Optional[int]:
    #     """Add a new exercise type"""
    #     with self.conn.connection_lock:
    #         try:
    #             self.conn.cursor.execute("""
    #                 INSERT OR IGNORE INTO exercise_types (name)
    #                 VALUES (?)
    #             """, (name,))
                
    #             self.conn.commit()
    #             return self.conn.cursor.lastrowid
    #         except sqlite3.Error as e:
    #             print(f"Error adding exercise type: {e}")
    #             self.conn.rollback()
    #             return None