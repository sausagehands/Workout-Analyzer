# sessions.py
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any


class SessionRepository:
    def __init__(self, conn):
        self.conn = conn

    def start_session(self, user_id: Optional[int] = None) -> Optional[int]:
        """Start a new workout session"""
        with self.conn.connection_lock:
            try:
                now = datetime.now()
                if user_id:
                    self.conn.cursor.execute("""
                        INSERT INTO workout_sessions (user_id, start_time)
                        VALUES (?, ?)
                    """, (user_id, now))
                else:
                    self.conn.cursor.execute("""
                        INSERT INTO workout_sessions (start_time)
                        VALUES (?)
                    """, (now,))
                
                self.conn.commit()
                return self.conn.cursor.lastrowid
            except sqlite3.Error as e:
                print(f"Error starting session: {e}")
                self.conn.rollback()
                return None

    def end_session(self, session_id: int, notes: str = "") -> bool:
        """End a workout session and calculate duration"""
        with self.conn.connection_lock:
            try:
                now = datetime.now()
                self.conn.cursor.execute("""
                    UPDATE workout_sessions
                    SET end_time = ?,
                        total_duration_seconds = (
                            CAST((julianday(?) - julianday(start_time)) * 86400 AS INTEGER)
                        ),
                        notes = ?
                    WHERE session_id = ?
                """, (now, now, notes, session_id))
                
                if self.conn.cursor.rowcount == 0:
                    print(f"Warning: Session {session_id} not found")
                    return False
                
                self.conn.commit()
                return True
            except sqlite3.Error as e:
                print(f"Error ending session: {e}")
                self.conn.rollback()
                return False

    def get_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Get session details by ID"""
        try:
            self.conn.cursor.execute("""
                SELECT s.*, u.name as user_name
                FROM workout_sessions s
                LEFT JOIN user_profile u ON s.user_id = u.user_id
                WHERE s.session_id = ?
            """, (session_id,))
            
            row = self.conn.cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"Error getting session: {e}")
            return None

    def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent workout sessions"""
        try:
            self.conn.cursor.execute("""
                SELECT s.*, u.name as user_name
                FROM workout_sessions s
                LEFT JOIN user_profile u ON s.user_id = u.user_id
                ORDER BY s.start_time DESC
                LIMIT ?
            """, (limit,))
            
            rows = self.conn.cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"Error getting recent sessions: {e}")
            return []

    def get_session_summary(self, session_id: int) -> Dict[str, Any]:
        """Get detailed summary of a workout session with exercises"""
        try:
            # Get session info
            session = self.get_session(session_id)
            if not session:
                return {}
            
            # Get exercise sets for this session
            self.conn.cursor.execute("""
                SELECT es.*, et.name as exercise_name
                FROM exercise_sets es
                JOIN exercise_types et ON es.exercise_type_id = et.exercise_type_id
                WHERE es.session_id = ?
                ORDER BY es.created_at
            """, (session_id,))
            
            exercise_sets = []
            for row in self.conn.cursor.fetchall():
                set_data = dict(row)
                
                # Get reps for this set
                self.conn.cursor.execute("""
                    SELECT rep_id, rep_number, form_quality, peak_angle, duration_seconds
                    FROM reps
                    WHERE set_id = ?
                    ORDER BY rep_number
                """, (set_data['set_id'],))
                
                reps = [dict(rep_row) for rep_row in self.conn.cursor.fetchall()]
                set_data['reps'] = reps
                exercise_sets.append(set_data)
            
            return {
                'session': session,
                'exercise_sets': exercise_sets
            }
        except sqlite3.Error as e:
            print(f"Error getting session summary: {e}")
            return {}