"""Unit tests for SessionRepository module.

Tests start_session, end_session, get_session, get_recent_sessions,
and get_session_summary using Arrange-Act-Assert structure with
nominal and edge cases.
"""
import sqlite3
import time

import pytest

from database.database_connection import DatabaseConnection
from database.sessions import SessionRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def tmp_db(tmp_path):
    """Return a path to a temporary .db file inside pytest's tmp directory."""
    return str(tmp_path / "test_sessions.db")


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
    conn.cursor.execute("""
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
    conn.commit()
    yield conn
    if conn.conn is not None:
        conn.close()


@pytest.fixture
def repo(db):
    """Return a SessionRepository backed by the test database."""
    return SessionRepository(db)


@pytest.fixture
def user_id(db):
    """Create a test user and return the user_id."""
    db.cursor.execute("INSERT INTO user_profile (name) VALUES (?)", ("Alice",))
    db.conn.commit()
    return db.cursor.lastrowid


# ---------------------------------------------------------------------------
# start_session – nominal cases
# ---------------------------------------------------------------------------
class TestStartSessionNominal:
    """Verify starting workout sessions."""

    def test_returns_integer_id(self, repo):
        # Act
        session_id = repo.start_session()

        # Assert
        assert isinstance(session_id, int)

    def test_first_session_gets_id_1(self, repo):
        # Act
        session_id = repo.start_session()

        # Assert
        assert session_id == 1

    def test_sequential_ids(self, repo):
        # Act
        id1 = repo.start_session()
        id2 = repo.start_session()

        # Assert
        assert id2 == id1 + 1

    def test_session_without_user(self, repo):
        # Act
        session_id = repo.start_session()
        session = repo.get_session(session_id)

        # Assert
        assert session is not None
        assert session["user_id"] is None

    def test_session_with_user(self, repo, user_id):
        # Act
        session_id = repo.start_session(user_id=user_id)
        session = repo.get_session(session_id)

        # Assert
        assert session["user_id"] == user_id

    def test_start_time_is_set(self, repo):
        # Act
        session_id = repo.start_session()
        session = repo.get_session(session_id)

        # Assert
        assert session["start_time"] is not None

    def test_end_time_starts_null(self, repo):
        # Act
        session_id = repo.start_session()
        session = repo.get_session(session_id)

        # Assert
        assert session["end_time"] is None

    def test_duration_starts_null(self, repo):
        # Act
        session_id = repo.start_session()
        session = repo.get_session(session_id)

        # Assert
        assert session["total_duration_seconds"] is None


# ---------------------------------------------------------------------------
# start_session – edge cases
# ---------------------------------------------------------------------------
class TestStartSessionEdge:
    """Edge cases for starting sessions."""

    def test_nonexistent_user_id_returns_none(self, repo):
        # Act – FK constraint rejects invalid user_id
        session_id = repo.start_session(user_id=999)

        # Assert – error handler catches IntegrityError, returns None
        assert session_id is None

    def test_multiple_sessions_same_user(self, repo, user_id):
        # Act
        id1 = repo.start_session(user_id=user_id)
        id2 = repo.start_session(user_id=user_id)
        id3 = repo.start_session(user_id=user_id)

        # Assert – all unique
        assert len({id1, id2, id3}) == 3


# ---------------------------------------------------------------------------
# end_session – nominal cases
# ---------------------------------------------------------------------------
class TestEndSessionNominal:
    """Verify ending workout sessions."""

    def test_returns_true(self, repo):
        # Arrange
        session_id = repo.start_session()

        # Act
        result = repo.end_session(session_id)

        # Assert
        assert result is True

    def test_sets_end_time(self, repo):
        # Arrange
        session_id = repo.start_session()

        # Act
        repo.end_session(session_id)
        session = repo.get_session(session_id)

        # Assert
        assert session["end_time"] is not None

    def test_calculates_duration(self, repo, db):
        # Arrange – insert session with a start_time 60 seconds in the past
        from datetime import datetime, timedelta
        past = datetime.now() - timedelta(seconds=60)
        db.cursor.execute(
            "INSERT INTO workout_sessions (start_time) VALUES (?)", (past,)
        )
        db.conn.commit()
        session_id = db.cursor.lastrowid

        # Act
        repo.end_session(session_id)
        session = repo.get_session(session_id)

        # Assert – duration should be approximately 60 seconds
        assert session["total_duration_seconds"] >= 59

    def test_stores_notes(self, repo):
        # Arrange
        session_id = repo.start_session()

        # Act
        repo.end_session(session_id, notes="Great workout!")
        session = repo.get_session(session_id)

        # Assert
        assert session["notes"] == "Great workout!"

    def test_empty_notes_default(self, repo):
        # Arrange
        session_id = repo.start_session()

        # Act
        repo.end_session(session_id)
        session = repo.get_session(session_id)

        # Assert
        assert session["notes"] == ""


# ---------------------------------------------------------------------------
# end_session – edge cases
# ---------------------------------------------------------------------------
class TestEndSessionEdge:
    """Edge cases for ending sessions."""

    def test_nonexistent_session_returns_false(self, repo):
        # Act
        result = repo.end_session(999)

        # Assert
        assert result is False

    def test_end_same_session_twice(self, repo):
        # Arrange
        session_id = repo.start_session()
        repo.end_session(session_id, notes="First end")

        # Act – ending again should overwrite
        result = repo.end_session(session_id, notes="Second end")

        # Assert
        assert result is True
        session = repo.get_session(session_id)
        assert session["notes"] == "Second end"

    def test_notes_with_special_characters(self, repo):
        # Arrange
        session_id = repo.start_session()
        notes = "Felt sore 😤 — couldn't finish O'Brien's routine"

        # Act
        repo.end_session(session_id, notes=notes)
        session = repo.get_session(session_id)

        # Assert
        assert session["notes"] == notes


# ---------------------------------------------------------------------------
# get_session – nominal cases
# ---------------------------------------------------------------------------
class TestGetSessionNominal:
    """Verify fetching sessions by ID."""

    def test_returns_dict(self, repo):
        # Arrange
        session_id = repo.start_session()

        # Act
        session = repo.get_session(session_id)

        # Assert
        assert isinstance(session, dict)

    def test_includes_user_name_when_linked(self, repo, user_id):
        # Arrange
        session_id = repo.start_session(user_id=user_id)

        # Act
        session = repo.get_session(session_id)

        # Assert – LEFT JOIN pulls user name
        assert session["user_name"] == "Alice"

    def test_user_name_null_when_no_user(self, repo):
        # Arrange
        session_id = repo.start_session()

        # Act
        session = repo.get_session(session_id)

        # Assert
        assert session["user_name"] is None

    def test_correct_session_returned(self, repo):
        # Arrange
        repo.start_session()
        id2 = repo.start_session()

        # Act
        session = repo.get_session(id2)

        # Assert
        assert session["session_id"] == id2


# ---------------------------------------------------------------------------
# get_session – edge cases
# ---------------------------------------------------------------------------
class TestGetSessionEdge:
    """Edge cases for session retrieval."""

    def test_nonexistent_id_returns_none(self, repo):
        # Act
        session = repo.get_session(999)

        # Assert
        assert session is None

    def test_negative_id_returns_none(self, repo):
        # Act
        session = repo.get_session(-1)

        # Assert
        assert session is None


# ---------------------------------------------------------------------------
# get_recent_sessions – nominal cases
# ---------------------------------------------------------------------------
class TestGetRecentSessionsNominal:
    """Verify fetching recent sessions."""

    def test_returns_list(self, repo):
        # Act
        sessions = repo.get_recent_sessions()

        # Assert
        assert isinstance(sessions, list)

    def test_returns_sessions_in_descending_order(self, repo):
        # Arrange
        repo.start_session()
        time.sleep(0.1)
        repo.start_session()
        time.sleep(0.1)
        repo.start_session()

        # Act
        sessions = repo.get_recent_sessions()

        # Assert – most recent first
        assert sessions[0]["session_id"] > sessions[-1]["session_id"]

    def test_respects_limit(self, repo):
        # Arrange
        for _ in range(5):
            repo.start_session()

        # Act
        sessions = repo.get_recent_sessions(limit=3)

        # Assert
        assert len(sessions) == 3

    def test_default_limit_is_10(self, repo):
        # Arrange
        for _ in range(15):
            repo.start_session()

        # Act
        sessions = repo.get_recent_sessions()

        # Assert
        assert len(sessions) == 10

    def test_each_entry_is_dict(self, repo):
        # Arrange
        repo.start_session()

        # Act
        sessions = repo.get_recent_sessions()

        # Assert
        assert isinstance(sessions[0], dict)

    def test_includes_user_name(self, repo, user_id):
        # Arrange
        repo.start_session(user_id=user_id)

        # Act
        sessions = repo.get_recent_sessions()

        # Assert
        assert sessions[0]["user_name"] == "Alice"


# ---------------------------------------------------------------------------
# get_recent_sessions – edge cases
# ---------------------------------------------------------------------------
class TestGetRecentSessionsEdge:
    """Edge cases for recent sessions."""

    def test_empty_database_returns_empty_list(self, repo):
        # Act
        sessions = repo.get_recent_sessions()

        # Assert
        assert sessions == []

    def test_fewer_sessions_than_limit(self, repo):
        # Arrange
        repo.start_session()
        repo.start_session()

        # Act
        sessions = repo.get_recent_sessions(limit=10)

        # Assert
        assert len(sessions) == 2

    def test_limit_zero_returns_empty(self, repo):
        # Arrange
        repo.start_session()

        # Act
        sessions = repo.get_recent_sessions(limit=0)

        # Assert
        assert sessions == []


# ---------------------------------------------------------------------------
# get_session_summary – nominal cases
# ---------------------------------------------------------------------------
class TestGetSessionSummaryNominal:
    """Verify session summary with exercises and reps."""

    def test_returns_dict_with_session_key(self, repo):
        # Arrange
        session_id = repo.start_session()

        # Act
        summary = repo.get_session_summary(session_id)

        # Assert
        assert "session" in summary
        assert summary["session"]["session_id"] == session_id

    def test_returns_dict_with_exercise_sets_key(self, repo):
        # Arrange
        session_id = repo.start_session()

        # Act
        summary = repo.get_session_summary(session_id)

        # Assert
        assert "exercise_sets" in summary
        assert isinstance(summary["exercise_sets"], list)

    def test_empty_session_has_no_exercise_sets(self, repo):
        # Arrange
        session_id = repo.start_session()

        # Act
        summary = repo.get_session_summary(session_id)

        # Assert
        assert summary["exercise_sets"] == []

    def test_summary_includes_exercise_sets(self, repo, db):
        # Arrange – manually insert exercise type and set
        session_id = repo.start_session()
        db.cursor.execute(
            "INSERT INTO exercise_types (name) VALUES (?)", ("squat",)
        )
        exercise_type_id = db.cursor.lastrowid
        db.cursor.execute("""
            INSERT INTO exercise_sets (session_id, exercise_type_id, total_reps)
            VALUES (?, ?, ?)
        """, (session_id, exercise_type_id, 10))
        db.conn.commit()

        # Act
        summary = repo.get_session_summary(session_id)

        # Assert
        assert len(summary["exercise_sets"]) == 1
        assert summary["exercise_sets"][0]["exercise_name"] == "squat"
        assert summary["exercise_sets"][0]["total_reps"] == 10

    def test_summary_includes_reps(self, repo, db):
        # Arrange – insert exercise type, set, and reps
        session_id = repo.start_session()
        db.cursor.execute(
            "INSERT INTO exercise_types (name) VALUES (?)", ("curl",)
        )
        exercise_type_id = db.cursor.lastrowid
        db.cursor.execute("""
            INSERT INTO exercise_sets (session_id, exercise_type_id)
            VALUES (?, ?)
        """, (session_id, exercise_type_id))
        set_id = db.cursor.lastrowid
        db.cursor.execute("""
            INSERT INTO reps (set_id, rep_number, form_quality, peak_angle, duration_seconds)
            VALUES (?, ?, ?, ?, ?)
        """, (set_id, 1, "excellent", 45.0, 2.5))
        db.cursor.execute("""
            INSERT INTO reps (set_id, rep_number, form_quality, peak_angle, duration_seconds)
            VALUES (?, ?, ?, ?, ?)
        """, (set_id, 2, "good", 50.0, 3.0))
        db.conn.commit()

        # Act
        summary = repo.get_session_summary(session_id)

        # Assert
        reps = summary["exercise_sets"][0]["reps"]
        assert len(reps) == 2
        assert reps[0]["form_quality"] == "excellent"
        assert reps[1]["form_quality"] == "good"

    def test_summary_multiple_exercise_sets(self, repo, db):
        # Arrange
        session_id = repo.start_session()
        db.cursor.execute(
            "INSERT INTO exercise_types (name) VALUES (?)", ("squat",)
        )
        squat_id = db.cursor.lastrowid
        db.cursor.execute(
            "INSERT INTO exercise_types (name) VALUES (?)", ("curl",)
        )
        curl_id = db.cursor.lastrowid

        db.cursor.execute("""
            INSERT INTO exercise_sets (session_id, exercise_type_id)
            VALUES (?, ?)
        """, (session_id, squat_id))
        db.cursor.execute("""
            INSERT INTO exercise_sets (session_id, exercise_type_id)
            VALUES (?, ?)
        """, (session_id, curl_id))
        db.conn.commit()

        # Act
        summary = repo.get_session_summary(session_id)

        # Assert
        assert len(summary["exercise_sets"]) == 2


# ---------------------------------------------------------------------------
# get_session_summary – edge cases
# ---------------------------------------------------------------------------
class TestGetSessionSummaryEdge:
    """Edge cases for session summary."""

    def test_nonexistent_session_returns_empty_dict(self, repo):
        # Act
        summary = repo.get_session_summary(999)

        # Assert
        assert summary == {}

    def test_exercise_set_with_no_reps(self, repo, db):
        # Arrange
        session_id = repo.start_session()
        db.cursor.execute(
            "INSERT INTO exercise_types (name) VALUES (?)", ("pushup",)
        )
        exercise_type_id = db.cursor.lastrowid
        db.cursor.execute("""
            INSERT INTO exercise_sets (session_id, exercise_type_id)
            VALUES (?, ?)
        """, (session_id, exercise_type_id))
        db.conn.commit()

        # Act
        summary = repo.get_session_summary(session_id)

        # Assert – set exists but reps list is empty
        assert len(summary["exercise_sets"]) == 1
        assert summary["exercise_sets"][0]["reps"] == []
