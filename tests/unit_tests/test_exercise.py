"""Unit tests for ExerciseSetRepository module.

Tests create_exercise_set, update_exercise_set_stats, and
get_exercise_history using Arrange-Act-Assert structure with
nominal and edge cases.
"""
import sqlite3
from datetime import datetime

import pytest

from database.database_connection import DatabaseConnection
from database.exercise import ExerciseSetRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def tmp_db(tmp_path):
    """Return a path to a temporary .db file inside pytest's tmp directory."""
    return str(tmp_path / "test_exercise.db")


@pytest.fixture
def db(tmp_db):
    """Yield a DatabaseConnection with required tables, then close it."""
    conn = DatabaseConnection(db_path=tmp_db)

    conn.cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            height_cm REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.cursor.execute("""
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
    conn.cursor.execute("""
        CREATE TABLE IF NOT EXISTS exercise_types (
            exercise_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)
    conn.cursor.execute("""
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
    conn.commit()
    yield conn
    if conn.conn is not None:
        conn.close()


@pytest.fixture
def repo(db):
    """Return an ExerciseSetRepository backed by the test database."""
    return ExerciseSetRepository(db)


@pytest.fixture
def session_id(db):
    """Create a test workout session and return its session_id."""
    now = datetime.now()
    db.cursor.execute(
        "INSERT INTO workout_sessions (start_time) VALUES (?)", (now,)
    )
    db.conn.commit()
    return db.cursor.lastrowid


# ---------------------------------------------------------------------------
# Helper – read an exercise set directly from the database
# ---------------------------------------------------------------------------
def _get_set(db, set_id):
    """Fetch an exercise_sets row by set_id."""
    db.cursor.execute("SELECT * FROM exercise_sets WHERE set_id = ?", (set_id,))
    row = db.cursor.fetchone()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# create_exercise_set – nominal cases
# ---------------------------------------------------------------------------
class TestCreateExerciseSetNominal:
    """Verify creating exercise sets within a session."""

    def test_returns_integer_id(self, repo, session_id):
        # Act
        set_id = repo.create_exercise_set(session_id, "squat")

        # Assert
        assert isinstance(set_id, int)

    def test_first_set_gets_id_1(self, repo, session_id):
        # Act
        set_id = repo.create_exercise_set(session_id, "squat")

        # Assert
        assert set_id == 1

    def test_sequential_ids(self, repo, session_id):
        # Act
        id1 = repo.create_exercise_set(session_id, "squat")
        id2 = repo.create_exercise_set(session_id, "curl")

        # Assert
        assert id2 == id1 + 1

    def test_creates_new_exercise_type(self, repo, session_id, db):
        # Act
        repo.create_exercise_set(session_id, "deadlift")

        # Assert – exercise_types table should have the new type
        db.cursor.execute(
            "SELECT name FROM exercise_types WHERE name = ?", ("deadlift",)
        )
        row = db.cursor.fetchone()
        assert row is not None
        assert row["name"] == "deadlift"

    def test_reuses_existing_exercise_type(self, repo, session_id, db):
        # Arrange – create first set with "squat"
        repo.create_exercise_set(session_id, "squat")

        # Act – create second set with same exercise name
        repo.create_exercise_set(session_id, "squat")

        # Assert – only one row in exercise_types for "squat"
        db.cursor.execute(
            "SELECT COUNT(*) as cnt FROM exercise_types WHERE name = ?", ("squat",)
        )
        assert db.cursor.fetchone()["cnt"] == 1

    def test_set_linked_to_correct_session(self, repo, session_id, db):
        # Act
        set_id = repo.create_exercise_set(session_id, "squat")

        # Assert
        exercise_set = _get_set(db, set_id)
        assert exercise_set["session_id"] == session_id

    def test_set_defaults_zero_reps(self, repo, session_id, db):
        # Act
        set_id = repo.create_exercise_set(session_id, "squat")

        # Assert
        exercise_set = _get_set(db, set_id)
        assert exercise_set["total_reps"] == 0
        assert exercise_set["excellent_reps"] == 0
        assert exercise_set["good_reps"] == 0
        assert exercise_set["poor_reps"] == 0

    def test_multiple_sets_same_exercise(self, repo, session_id):
        # Act – 3 sets of squats in one session
        id1 = repo.create_exercise_set(session_id, "squat")
        id2 = repo.create_exercise_set(session_id, "squat")
        id3 = repo.create_exercise_set(session_id, "squat")

        # Assert – all unique IDs
        assert len({id1, id2, id3}) == 3


# ---------------------------------------------------------------------------
# create_exercise_set – edge cases
# ---------------------------------------------------------------------------
class TestCreateExerciseSetEdge:
    """Edge cases for creating exercise sets."""

    def test_nonexistent_session_returns_none(self, repo):
        # Act – FK constraint rejects invalid session_id
        set_id = repo.create_exercise_set(999, "squat")

        # Assert
        assert set_id is None

    def test_exercise_name_with_special_characters(self, repo, session_id, db):
        # Arrange
        name = "single-arm dumbbell row (left)"

        # Act
        set_id = repo.create_exercise_set(session_id, name)

        # Assert
        assert set_id is not None
        db.cursor.execute(
            "SELECT name FROM exercise_types WHERE name = ?", (name,)
        )
        assert db.cursor.fetchone()["name"] == name

    def test_exercise_name_case_sensitive(self, repo, session_id, db):
        # Act – "Squat" and "squat" are different types
        repo.create_exercise_set(session_id, "squat")
        repo.create_exercise_set(session_id, "Squat")

        # Assert – two distinct exercise types
        db.cursor.execute("SELECT COUNT(*) as cnt FROM exercise_types")
        assert db.cursor.fetchone()["cnt"] == 2


# ---------------------------------------------------------------------------
# update_exercise_set_stats – nominal cases
# ---------------------------------------------------------------------------
class TestUpdateExerciseSetStatsNominal:
    """Verify updating exercise set statistics."""

    def test_returns_true(self, repo, session_id):
        # Arrange
        set_id = repo.create_exercise_set(session_id, "squat")
        stats = {"total_reps": 10, "excellent_reps": 5, "good_reps": 3, "poor_reps": 2}

        # Act
        result = repo.update_exercise_set_stats(set_id, stats)

        # Assert
        assert result is True

    def test_persists_rep_counts(self, repo, session_id, db):
        # Arrange
        set_id = repo.create_exercise_set(session_id, "squat")
        stats = {
            "total_reps": 12,
            "excellent_reps": 6,
            "good_reps": 4,
            "poor_reps": 2,
        }

        # Act
        repo.update_exercise_set_stats(set_id, stats)

        # Assert
        exercise_set = _get_set(db, set_id)
        assert exercise_set["total_reps"] == 12
        assert exercise_set["excellent_reps"] == 6
        assert exercise_set["good_reps"] == 4
        assert exercise_set["poor_reps"] == 2

    def test_persists_angle_stats(self, repo, session_id, db):
        # Arrange
        set_id = repo.create_exercise_set(session_id, "curl")
        stats = {
            "average_angle": 45.5,
            "min_angle": 30.0,
            "max_angle": 60.0,
        }

        # Act
        repo.update_exercise_set_stats(set_id, stats)

        # Assert
        exercise_set = _get_set(db, set_id)
        assert exercise_set["average_angle"] == pytest.approx(45.5)
        assert exercise_set["min_angle"] == pytest.approx(30.0)
        assert exercise_set["max_angle"] == pytest.approx(60.0)

    def test_persists_duration(self, repo, session_id, db):
        # Arrange
        set_id = repo.create_exercise_set(session_id, "pushup")
        stats = {"duration_seconds": 120}

        # Act
        repo.update_exercise_set_stats(set_id, stats)

        # Assert
        exercise_set = _get_set(db, set_id)
        assert exercise_set["duration_seconds"] == 120

    def test_full_stats_dict(self, repo, session_id, db):
        # Arrange
        set_id = repo.create_exercise_set(session_id, "squat")
        stats = {
            "total_reps": 15,
            "excellent_reps": 8,
            "good_reps": 5,
            "poor_reps": 2,
            "average_angle": 90.0,
            "min_angle": 75.0,
            "max_angle": 110.0,
            "duration_seconds": 180,
        }

        # Act
        repo.update_exercise_set_stats(set_id, stats)

        # Assert
        exercise_set = _get_set(db, set_id)
        assert exercise_set["total_reps"] == 15
        assert exercise_set["average_angle"] == pytest.approx(90.0)
        assert exercise_set["duration_seconds"] == 180

    def test_update_overwrites_previous_stats(self, repo, session_id, db):
        # Arrange
        set_id = repo.create_exercise_set(session_id, "squat")
        repo.update_exercise_set_stats(set_id, {"total_reps": 5})

        # Act – update again with new stats
        repo.update_exercise_set_stats(set_id, {"total_reps": 10})

        # Assert
        exercise_set = _get_set(db, set_id)
        assert exercise_set["total_reps"] == 10


# ---------------------------------------------------------------------------
# update_exercise_set_stats – edge cases
# ---------------------------------------------------------------------------
class TestUpdateExerciseSetStatsEdge:
    """Edge cases for updating exercise set statistics."""

    def test_nonexistent_set_returns_false(self, repo):
        # Act
        result = repo.update_exercise_set_stats(999, {"total_reps": 10})

        # Assert
        assert result is False

    def test_empty_stats_dict_uses_defaults(self, repo, session_id, db):
        # Arrange
        set_id = repo.create_exercise_set(session_id, "squat")

        # Act – empty dict, stats.get() defaults kick in
        result = repo.update_exercise_set_stats(set_id, {})

        # Assert
        assert result is True
        exercise_set = _get_set(db, set_id)
        assert exercise_set["total_reps"] == 0
        assert exercise_set["excellent_reps"] == 0
        assert exercise_set["good_reps"] == 0
        assert exercise_set["poor_reps"] == 0
        assert exercise_set["average_angle"] is None
        assert exercise_set["min_angle"] is None
        assert exercise_set["max_angle"] is None
        assert exercise_set["duration_seconds"] is None

    def test_missing_keys_use_defaults(self, repo, session_id, db):
        # Arrange
        set_id = repo.create_exercise_set(session_id, "curl")

        # Act – only provide some keys
        repo.update_exercise_set_stats(set_id, {"total_reps": 8, "excellent_reps": 3})

        # Assert – missing rep keys default to 0, missing angles default to None
        exercise_set = _get_set(db, set_id)
        assert exercise_set["total_reps"] == 8
        assert exercise_set["excellent_reps"] == 3
        assert exercise_set["good_reps"] == 0
        assert exercise_set["poor_reps"] == 0
        assert exercise_set["average_angle"] is None


# ---------------------------------------------------------------------------
# get_exercise_history – nominal cases
# ---------------------------------------------------------------------------
class TestGetExerciseHistoryNominal:
    """Verify fetching exercise history."""

    def test_returns_list(self, repo, session_id):
        # Arrange
        repo.create_exercise_set(session_id, "squat")

        # Act
        history = repo.get_exercise_history("squat")

        # Assert
        assert isinstance(history, list)

    def test_returns_correct_exercise(self, repo, session_id):
        # Arrange
        squat_id = repo.create_exercise_set(session_id, "squat")
        curl_id = repo.create_exercise_set(session_id, "curl")
        repo.update_exercise_set_stats(squat_id, {"total_reps": 5})
        repo.update_exercise_set_stats(curl_id, {"total_reps": 3})

        # Act
        history = repo.get_exercise_history("squat")

        # Assert – only squats returned
        assert len(history) == 1
        assert history[0]["exercise_name"] == "squat"

    def test_includes_session_date(self, repo, session_id):
        # Arrange
        set_id = repo.create_exercise_set(session_id, "squat")
        repo.update_exercise_set_stats(set_id, {"total_reps": 5})

        # Act
        history = repo.get_exercise_history("squat")

        # Assert
        assert history[0]["session_date"] is not None

    def test_each_entry_is_dict(self, repo, session_id):
        # Arrange
        set_id = repo.create_exercise_set(session_id, "squat")
        repo.update_exercise_set_stats(set_id, {"total_reps": 5})

        # Act
        history = repo.get_exercise_history("squat")

        # Assert
        assert isinstance(history[0], dict)

    def test_respects_limit(self, repo, db):
        # Arrange – create 5 sessions with squats (each with reps)
        for _ in range(5):
            now = datetime.now()
            db.cursor.execute(
                "INSERT INTO workout_sessions (start_time) VALUES (?)", (now,)
            )
            sid = db.cursor.lastrowid
            set_id = repo.create_exercise_set(sid, "squat")
            repo.update_exercise_set_stats(set_id, {"total_reps": 5})

        # Act
        history = repo.get_exercise_history("squat", limit=3)

        # Assert
        assert len(history) == 3

    def test_default_limit_is_30(self, repo, db):
        # Arrange – create 35 sessions with squats (each with reps)
        for _ in range(35):
            now = datetime.now()
            db.cursor.execute(
                "INSERT INTO workout_sessions (start_time) VALUES (?)", (now,)
            )
            sid = db.cursor.lastrowid
            set_id = repo.create_exercise_set(sid, "squat")
            repo.update_exercise_set_stats(set_id, {"total_reps": 5})

        # Act
        history = repo.get_exercise_history("squat")

        # Assert
        assert len(history) == 30

    def test_ordered_most_recent_first(self, repo, db):
        # Arrange – create 3 sets with distinct created_at timestamps
        set_ids = []
        timestamps = ["2024-01-01 10:00:00", "2024-01-02 10:00:00", "2024-01-03 10:00:00"]
        for ts in timestamps:
            db.cursor.execute(
                "INSERT INTO workout_sessions (start_time) VALUES (?)", (ts,)
            )
            sid = db.cursor.lastrowid
            # Insert exercise type once
            db.cursor.execute(
                "INSERT OR IGNORE INTO exercise_types (name) VALUES (?)", ("squat",)
            )
            db.cursor.execute(
                "SELECT exercise_type_id FROM exercise_types WHERE name = ?", ("squat",)
            )
            etype_id = db.cursor.fetchone()["exercise_type_id"]
            db.cursor.execute("""
                INSERT INTO exercise_sets (session_id, exercise_type_id, total_reps, created_at)
                VALUES (?, ?, 5, ?)
            """, (sid, etype_id, ts))
            set_ids.append(db.cursor.lastrowid)
        db.conn.commit()

        # Act
        history = repo.get_exercise_history("squat")

        # Assert – most recent first (Jan 3 before Jan 1)
        assert history[0]["set_id"] == set_ids[2]
        assert history[-1]["set_id"] == set_ids[0]


# ---------------------------------------------------------------------------
# get_exercise_history – edge cases
# ---------------------------------------------------------------------------
class TestGetExerciseHistoryEdge:
    """Edge cases for exercise history."""

    def test_no_history_returns_empty_list(self, repo):
        # Act
        history = repo.get_exercise_history("squat")

        # Assert
        assert history == []

    def test_nonexistent_exercise_returns_empty_list(self, repo, session_id):
        # Arrange
        repo.create_exercise_set(session_id, "squat")

        # Act
        history = repo.get_exercise_history("deadlift")

        # Assert
        assert history == []

    def test_zero_rep_set_excluded_from_history(self, repo, session_id, db):
        """Sets with total_reps=0 should not appear in history."""
        # Arrange – create set (starts with 0 reps), don't update it
        repo.create_exercise_set(session_id, "squat")

        # Act
        history = repo.get_exercise_history("squat")

        # Assert – empty set is excluded
        assert history == []

    def test_limit_zero_returns_empty(self, repo, session_id):
        # Arrange
        repo.create_exercise_set(session_id, "squat")

        # Act
        history = repo.get_exercise_history("squat", limit=0)

        # Assert
        assert history == []
