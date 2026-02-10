# schema.py
from .seed import seed_exercise_types


def create_tables(cursor):
    """Create all database tables if they don't exist"""
    # -----------------------------
    # User profile (single-user app)
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            height_cm REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # -----------------------------
    # Workout sessions
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workout_sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            total_duration_seconds INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id)
                REFERENCES user_profile(user_id)
                ON DELETE SET NULL
        )
    """)

    # -----------------------------
    # Exercise types (flexible lookup table)
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exercise_types (
            exercise_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)

    # -----------------------------
    # Exercise sets with detailed metrics
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exercise_sets (
            set_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            exercise_type_id INTEGER NOT NULL,
            total_reps INTEGER DEFAULT 0,
            excellent_reps INTEGER DEFAULT 0,
            good_reps INTEGER DEFAULT 0,
            poor_reps INTEGER DEFAULT 0,
            average_angle REAL,
            min_angle REAL,
            max_angle REAL,
            duration_seconds INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id)
                REFERENCES workout_sessions(session_id)
                ON DELETE CASCADE,
            FOREIGN KEY (exercise_type_id)
                REFERENCES exercise_types(exercise_type_id)
        )
    """)

    # -----------------------------
    # Individual reps with form quality
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reps (
            rep_id INTEGER PRIMARY KEY AUTOINCREMENT,
            set_id INTEGER NOT NULL,
            rep_number INTEGER NOT NULL,
            form_quality TEXT NOT NULL CHECK (form_quality IN ('excellent', 'good', 'poor')),
            peak_angle REAL NOT NULL,
            duration_seconds REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (set_id)
                REFERENCES exercise_sets(set_id)
                ON DELETE CASCADE
        )
    """)

    # -----------------------------
    # Monthly stats (consolidated data for retention)
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monthly_stats (
            stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            exercise_type_id INTEGER NOT NULL,
            total_sessions INTEGER DEFAULT 0,
            total_reps INTEGER DEFAULT 0,
            excellent_reps INTEGER DEFAULT 0,
            good_reps INTEGER DEFAULT 0,
            poor_reps INTEGER DEFAULT 0,
            total_duration_seconds INTEGER DEFAULT 0,
            average_angle REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (exercise_type_id)
                REFERENCES exercise_types(exercise_type_id),
            UNIQUE(year, month, exercise_type_id)
        )
    """)

    # -----------------------------
    # Indexes for performance
    # -----------------------------
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_sessions_start ON workout_sessions(start_time)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_sessions_user ON workout_sessions(user_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_sets_session ON exercise_sets(session_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_sets_type ON exercise_sets(exercise_type_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_reps_set ON reps(set_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_reps_quality ON reps(form_quality)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_monthly_stats_date ON monthly_stats(year, month)"
    )

    # Seed default exercise types
    seed_exercise_types(cursor)