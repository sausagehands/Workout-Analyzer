"""Unit tests for RepRepository module.

Tests log_rep and get_rep_stats using Arrange-Act-Assert structure
with nominal and edge cases.
"""
import sqlite3
from datetime import datetime

import pytest

from database.database_connection import DatabaseConnection
from database.reps import RepRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def tmp_db(tmp_path):
    """Return a path to a temporary .db file inside pytest's tmp directory."""
    return str(tmp_path / "test_reps.db")


@pytest.fixture
def db(tmp_db):
    """Yield a DatabaseConnection with required tables, then close it."""
    conn = DatabaseConnection(db_path=tmp_db)

    conn.cursor.execute("""
        CREATE TABLE IF NOT EXISTS workout_sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            total_duration_seconds INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    """Return a RepRepository backed by the test database."""
    return RepRepository(db)


@pytest.fixture
def set_id(db):
    """Create a session + exercise set and return the set_id."""
    now = datetime.now()
    db.cursor.execute(
        "INSERT INTO workout_sessions (start_time) VALUES (?)", (now,)
    )
    session_id = db.cursor.lastrowid
    db.cursor.execute(
        "INSERT INTO exercise_types (name) VALUES (?)", ("squat",)
    )
    exercise_type_id = db.cursor.lastrowid
    db.cursor.execute("""
        INSERT INTO exercise_sets (session_id, exercise_type_id)
        VALUES (?, ?)
    """, (session_id, exercise_type_id))
    db.conn.commit()
    return db.cursor.lastrowid


# ---------------------------------------------------------------------------
# Helper – read exercise_sets row directly
# ---------------------------------------------------------------------------
def _get_set(db, set_id):
    """Fetch an exercise_sets row by set_id."""
    db.cursor.execute("SELECT * FROM exercise_sets WHERE set_id = ?", (set_id,))
    row = db.cursor.fetchone()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# log_rep – nominal cases
# ---------------------------------------------------------------------------
class TestLogRepNominal:
    """Verify logging individual reps."""

    def test_returns_true(self, repo, set_id):
        # Act
        result = repo.log_rep(set_id, 1, "excellent", 45.0, 2.5)

        # Assert
        assert result is True

    def test_inserts_rep_into_table(self, repo, set_id, db):
        # Act
        repo.log_rep(set_id, 1, "good", 50.0, 3.0)

        # Assert
        db.cursor.execute("SELECT * FROM reps WHERE set_id = ?", (set_id,))
        row = db.cursor.fetchone()
        assert row is not None
        assert row["rep_number"] == 1
        assert row["form_quality"] == "good"
        assert row["peak_angle"] == pytest.approx(50.0)
        assert row["duration_seconds"] == pytest.approx(3.0)

    def test_increments_total_reps(self, repo, set_id, db):
        # Act
        repo.log_rep(set_id, 1, "excellent", 45.0, 2.0)
        repo.log_rep(set_id, 2, "good", 50.0, 2.5)
        repo.log_rep(set_id, 3, "poor", 60.0, 3.0)

        # Assert
        exercise_set = _get_set(db, set_id)
        assert exercise_set["total_reps"] == 3

    def test_increments_excellent_counter(self, repo, set_id, db):
        # Act
        repo.log_rep(set_id, 1, "excellent", 45.0, 2.0)
        repo.log_rep(set_id, 2, "excellent", 46.0, 2.1)

        # Assert
        exercise_set = _get_set(db, set_id)
        assert exercise_set["excellent_reps"] == 2
        assert exercise_set["good_reps"] == 0
        assert exercise_set["poor_reps"] == 0

    def test_increments_good_counter(self, repo, set_id, db):
        # Act
        repo.log_rep(set_id, 1, "good", 50.0, 2.5)

        # Assert
        exercise_set = _get_set(db, set_id)
        assert exercise_set["good_reps"] == 1

    def test_increments_poor_counter(self, repo, set_id, db):
        # Act
        repo.log_rep(set_id, 1, "poor", 70.0, 4.0)

        # Assert
        exercise_set = _get_set(db, set_id)
        assert exercise_set["poor_reps"] == 1

    def test_mixed_quality_reps(self, repo, set_id, db):
        # Act
        repo.log_rep(set_id, 1, "excellent", 45.0, 2.0)
        repo.log_rep(set_id, 2, "good", 50.0, 2.5)
        repo.log_rep(set_id, 3, "good", 52.0, 2.6)
        repo.log_rep(set_id, 4, "poor", 70.0, 4.0)

        # Assert
        exercise_set = _get_set(db, set_id)
        assert exercise_set["total_reps"] == 4
        assert exercise_set["excellent_reps"] == 1
        assert exercise_set["good_reps"] == 2
        assert exercise_set["poor_reps"] == 1

    def test_rep_has_timestamp(self, repo, set_id, db):
        # Act
        repo.log_rep(set_id, 1, "excellent", 45.0, 2.0)

        # Assert
        db.cursor.execute("SELECT timestamp FROM reps WHERE set_id = ?", (set_id,))
        row = db.cursor.fetchone()
        assert row["timestamp"] is not None


# ---------------------------------------------------------------------------
# log_rep – edge cases
# ---------------------------------------------------------------------------
class TestLogRepEdge:
    """Edge cases for logging reps."""

    def test_invalid_form_quality_returns_false(self, repo, set_id):
        # Act
        result = repo.log_rep(set_id, 1, "amazing", 45.0, 2.0)

        # Assert
        assert result is False

    def test_invalid_quality_does_not_insert(self, repo, set_id, db):
        # Act
        repo.log_rep(set_id, 1, "amazing", 45.0, 2.0)

        # Assert – no rep inserted
        db.cursor.execute("SELECT COUNT(*) as cnt FROM reps WHERE set_id = ?", (set_id,))
        assert db.cursor.fetchone()["cnt"] == 0

    def test_invalid_quality_does_not_increment_counters(self, repo, set_id, db):
        # Act
        repo.log_rep(set_id, 1, "amazing", 45.0, 2.0)

        # Assert – counters unchanged
        exercise_set = _get_set(db, set_id)
        assert exercise_set["total_reps"] == 0

    def test_nonexistent_set_returns_false(self, repo):
        # Act
        result = repo.log_rep(999, 1, "excellent", 45.0, 2.0)

        # Assert
        assert result is False

    def test_zero_peak_angle(self, repo, set_id, db):
        # Act
        result = repo.log_rep(set_id, 1, "excellent", 0.0, 2.0)

        # Assert
        assert result is True
        db.cursor.execute("SELECT peak_angle FROM reps WHERE set_id = ?", (set_id,))
        assert db.cursor.fetchone()["peak_angle"] == 0.0

    def test_zero_duration(self, repo, set_id, db):
        # Act
        result = repo.log_rep(set_id, 1, "excellent", 45.0, 0.0)

        # Assert
        assert result is True
        db.cursor.execute("SELECT duration_seconds FROM reps WHERE set_id = ?", (set_id,))
        assert db.cursor.fetchone()["duration_seconds"] == 0.0

    def test_uppercase_quality_returns_false(self, repo, set_id):
        # Act – validation expects lowercase
        result = repo.log_rep(set_id, 1, "EXCELLENT", 45.0, 2.0)

        # Assert
        assert result is False


# ---------------------------------------------------------------------------
# get_rep_stats – nominal cases
# ---------------------------------------------------------------------------
class TestGetRepStatsNominal:
    """Verify rep statistics aggregation."""

    def test_returns_dict(self, repo, set_id):
        # Arrange
        repo.log_rep(set_id, 1, "excellent", 45.0, 2.0)

        # Act
        stats = repo.get_rep_stats(set_id)

        # Assert
        assert isinstance(stats, dict)

    def test_total_reps_count(self, repo, set_id):
        # Arrange
        repo.log_rep(set_id, 1, "excellent", 45.0, 2.0)
        repo.log_rep(set_id, 2, "good", 50.0, 2.5)
        repo.log_rep(set_id, 3, "poor", 60.0, 3.0)

        # Act
        stats = repo.get_rep_stats(set_id)

        # Assert
        assert stats["total_reps"] == 3

    def test_quality_breakdown(self, repo, set_id):
        # Arrange
        repo.log_rep(set_id, 1, "excellent", 45.0, 2.0)
        repo.log_rep(set_id, 2, "excellent", 46.0, 2.1)
        repo.log_rep(set_id, 3, "good", 50.0, 2.5)
        repo.log_rep(set_id, 4, "poor", 70.0, 4.0)

        # Act
        stats = repo.get_rep_stats(set_id)

        # Assert
        assert stats["excellent_reps"] == 2
        assert stats["good_reps"] == 1
        assert stats["poor_reps"] == 1

    def test_average_peak_angle(self, repo, set_id):
        # Arrange
        repo.log_rep(set_id, 1, "excellent", 40.0, 2.0)
        repo.log_rep(set_id, 2, "excellent", 50.0, 2.0)
        repo.log_rep(set_id, 3, "excellent", 60.0, 2.0)

        # Act
        stats = repo.get_rep_stats(set_id)

        # Assert – avg of 40, 50, 60 = 50
        assert stats["avg_peak_angle"] == pytest.approx(50.0)

    def test_min_and_max_peak_angle(self, repo, set_id):
        # Arrange
        repo.log_rep(set_id, 1, "excellent", 30.0, 2.0)
        repo.log_rep(set_id, 2, "good", 50.0, 2.5)
        repo.log_rep(set_id, 3, "poor", 80.0, 4.0)

        # Act
        stats = repo.get_rep_stats(set_id)

        # Assert
        assert stats["min_peak_angle"] == pytest.approx(30.0)
        assert stats["max_peak_angle"] == pytest.approx(80.0)

    def test_average_duration(self, repo, set_id):
        # Arrange
        repo.log_rep(set_id, 1, "excellent", 45.0, 2.0)
        repo.log_rep(set_id, 2, "excellent", 45.0, 4.0)

        # Act
        stats = repo.get_rep_stats(set_id)

        # Assert – avg of 2.0, 4.0 = 3.0
        assert stats["avg_duration"] == pytest.approx(3.0)

    def test_has_all_expected_keys(self, repo, set_id):
        # Arrange
        repo.log_rep(set_id, 1, "excellent", 45.0, 2.0)

        # Act
        stats = repo.get_rep_stats(set_id)

        # Assert
        expected_keys = {
            "total_reps", "avg_peak_angle", "min_peak_angle",
            "max_peak_angle", "avg_duration", "excellent_reps",
            "good_reps", "poor_reps",
        }
        assert set(stats.keys()) == expected_keys


# ---------------------------------------------------------------------------
# get_rep_stats – edge cases
# ---------------------------------------------------------------------------
class TestGetRepStatsEdge:
    """Edge cases for rep statistics."""

    def test_no_reps_returns_zero_total(self, repo, set_id):
        # Act – no reps logged
        stats = repo.get_rep_stats(set_id)

        # Assert – COUNT(*) on empty set returns 0
        assert stats["total_reps"] == 0

    def test_no_reps_nulls_for_aggregates(self, repo, set_id):
        # Act
        stats = repo.get_rep_stats(set_id)

        # Assert – AVG/MIN/MAX on empty set return None
        assert stats["avg_peak_angle"] is None
        assert stats["min_peak_angle"] is None
        assert stats["max_peak_angle"] is None
        assert stats["avg_duration"] is None

    def test_nonexistent_set_returns_zero_total(self, repo):
        # Act – set_id 999 doesn't exist, but SQL still returns a row with COUNT=0
        stats = repo.get_rep_stats(999)

        # Assert
        assert stats["total_reps"] == 0

    def test_single_rep_stats(self, repo, set_id):
        # Arrange
        repo.log_rep(set_id, 1, "good", 55.5, 3.2)

        # Act
        stats = repo.get_rep_stats(set_id)

        # Assert – min == max == avg for single rep
        assert stats["avg_peak_angle"] == pytest.approx(55.5)
        assert stats["min_peak_angle"] == pytest.approx(55.5)
        assert stats["max_peak_angle"] == pytest.approx(55.5)
        assert stats["avg_duration"] == pytest.approx(3.2)
