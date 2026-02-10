# users.py
import sqlite3
from typing import Optional, Dict, Any


class UserRepository:
    def __init__(self, conn):
        self.conn = conn

    def create_user(self, name: str) -> Optional[int]:
        """Create a new user in the database"""
        with self.conn.connection_lock:
            try:
                self.conn.cursor.execute("""
                    INSERT INTO user_profile (name)
                    VALUES (?)
                """, (name,))
                self.conn.commit()
                return self.conn.cursor.lastrowid
            except sqlite3.Error as e:
                print(f"Error creating user: {e}")
                self.conn.rollback()
                return None

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user profile by ID"""
        try:
            self.conn.cursor.execute("""
                SELECT user_id, name, height_cm, created_at, updated_at
                FROM user_profile
                WHERE user_id = ?
            """, (user_id,))
            row = self.conn.cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"Error getting user: {e}")
            return None

    def update_profile(self, user_id: int, **profile) -> bool:
        """Update user profile fields"""
        with self.conn.connection_lock:
            try:
                fields = []
                values = []
                
                for key, value in profile.items():
                    if key in ['name', 'height_cm']:
                        fields.append(f"{key} = ?")
                        values.append(value)
                
                if not fields:
                    return False
                
                values.append(user_id)
                
                self.conn.cursor.execute(f"""
                    UPDATE user_profile
                    SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, tuple(values))
                
                if self.conn.cursor.rowcount == 0:
                    print(f"Warning: User {user_id} not found")
                    return False
                
                self.conn.commit()
                return True
            except sqlite3.Error as e:
                print(f"Error updating profile: {e}")
                self.conn.rollback()
                return False

    def get_default_user(self) -> Optional[Dict[str, Any]]:
        """Get the first user (for single-user apps)"""
        try:
            self.conn.cursor.execute("""
                SELECT user_id, name, height_cm, created_at
                FROM user_profile
                ORDER BY user_id
                LIMIT 1
            """)
            row = self.conn.cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"Error getting default user: {e}")
            return None