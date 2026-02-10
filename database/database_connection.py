# connection.py
import sqlite3
import threading
from typing import Optional

from config.app_constants import DATABASE_PATH


class DatabaseConnection:
    """Handles database connection and basic operations"""

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.connection_lock = threading.RLock()
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self._connect()
    
    def _connect(self):
        """Establish database connection with error handling"""
        
        with self.connection_lock:
            try:
                self.conn = sqlite3.connect(
                    self.db_path,
                    check_same_thread=False
                )
                self.conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
                
                '''connection holds database, cursor talks to database-- use it to execute queries'''
                self.cursor = self.conn.cursor()
                
                # Enable foreign keys and WAL mode for better performance
                self.cursor.execute("PRAGMA foreign_keys = ON")
                
                '''WAL allows read & writes to happen together'''
                self.cursor.execute("PRAGMA journal_mode = WAL")
                self.conn.commit()
                
            except sqlite3.Error as e:
                print(f"Database connection error: {e}")
                raise
    
    def commit(self):
        """Commit pending transactions"""
        with self.connection_lock:
            #makes sure db is still connected
            if self.conn:
                #commits the changes
                self.conn.commit()
    
    def rollback(self):
        """Rollback pending transactions-- pretend everything since last commit didn't happen
        jic app crashes mid write, stats break, or inconsistent state-- protects integrity
        """
        with self.connection_lock:
            if self.conn:
                self.conn.rollback()
    
    def close(self):
        """Close database connection safely"""
        #lock ensyres nothing is writing while closing
        with self.connection_lock:
            if self.conn:
                #always commits before closing app
                self.conn.commit()
                self.conn.close()
                self.conn = None
                self.cursor = None
    
    # def __enter__(self):
    #     """Context manager entry"""
    #     return self

    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     """Context manager exit"""
    #     self.close()