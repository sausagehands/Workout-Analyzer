# seed.py
def seed_exercise_types(cursor):
    """Insert default exercise types if they don't already exist"""
    default_exercises = ['squat', 'pushup', 'curl']
    
    for name in default_exercises:
        cursor.execute(
            "INSERT OR IGNORE INTO exercise_types (name) VALUES (?)",
            (name,)
        )
    
    # Commit is handled by the caller