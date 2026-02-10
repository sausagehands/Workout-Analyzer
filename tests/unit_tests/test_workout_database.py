"""Unit tests for WorkoutDatabase facade module.

Tests initialization, convenience methods, and legacy delegation
using Arrange-Act-Assert structure with nominal and edge cases.
"""
import sqlite3

import pytest

from database.workout_database import WorkoutDatabase
from database.database_connection import DatabaseConnection
from database.users import UserRepository
from database.sessions import SessionRepository
from database.exercise import ExerciseSetRepository
from database.reps import RepRepository
from database.stats import StatsRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def tmp_db(tmp_path):
    """Return a path to a temporary .db file inside pytest's tmp directory."""
    return str(tmp_path / "test_workout.db")


@pytest.fixture
def wdb(tmp_db):
    """Yield a WorkoutDatabase backed by a temp file, then close it."""
    db = WorkoutDatabase(db_path=tmp_db)
    yield db
    if db.connection.conn is not None:
        db.close()


# ---------------------------------------------------------------------------
# Initialization – nominal cases
# ---------------------------------------------------------------------------
class TestInitNominal:
    """Verify WorkoutDatabase initializes correctly."""

    def test_connection_is_established(self, wdb):
        # Assert
        assert wdb.connection is not None
        assert wdb.connection.conn is not None

    def test_connection_is_database_connection(self, wdb):
        # Assert
        assert isinstance(wdb.connection, DatabaseConnection)

    def test_users_repo_initialized(self, wdb):
        # Assert
        assert isinstance(wdb.users, UserRepository)

    def test_sessions_repo_initialized(self, wdb):
        # Assert
        assert isinstance(wdb.sessions, SessionRepository)

    def test_exercise_sets_repo_initialized(self, wdb):
        # Assert
        assert isinstance(wdb.exercise_sets, ExerciseSetRepository)

    def test_reps_repo_initialized(self, wdb):
        # Assert
        assert isinstance(wdb.reps, RepRepository)

    def test_stats_repo_initialized(self, wdb):
        # Assert
        assert isinstance(wdb.stats, StatsRepository)

    def test_tables_created(self, wdb):
        # Act – query sqlite_master for expected tables
        wdb.connection.cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = {row["name"] for row in wdb.connection.cursor.fetchall()}

        # Assert
        expected = {
            "user_profile",
            "workout_sessions",
            "exercise_types",
            "exercise_sets",
            "reps",
            "monthly_stats",
        }
        assert expected.issubset(tables)

    def test_seed_exercise_types_present(self, wdb):
        # Act
        wdb.connection.cursor.execute(
            "SELECT name FROM exercise_types ORDER BY name"
        )
        names = [row["name"] for row in wdb.connection.cursor.fetchall()]

        # Assert – seed.py inserts squat, pushup, curl
        assert "squat" in names
        assert "pushup" in names
        assert "curl" in names

    def test_all_repos_share_same_connection(self, wdb):
        # Assert – every repo.conn points to the same DatabaseConnection
        assert wdb.users.conn is wdb.connection
        assert wdb.sessions.conn is wdb.connection
        assert wdb.exercise_sets.conn is wdb.connection
        assert wdb.reps.conn is wdb.connection
        assert wdb.stats.conn is wdb.connection


# ---------------------------------------------------------------------------
# Initialization – edge cases
# ---------------------------------------------------------------------------
class TestInitEdge:
    """Edge cases for WorkoutDatabase initialization."""

    def test_invalid_path_raises(self):
        # Act / Assert
        with pytest.raises(Exception):
            WorkoutDatabase(db_path="/no/such/dir/db.sqlite")

    def test_two_instances_same_path(self, tmp_db):
        # Arrange
        db1 = WorkoutDatabase(db_path=tmp_db)

        # Act – second instance re-uses same file
        db2 = WorkoutDatabase(db_path=tmp_db)

        # Assert – both work, tables already exist
        assert db1.connection.conn is not None
        assert db2.connection.conn is not None

        db2.close()
        db1.close()


# ---------------------------------------------------------------------------
# Convenience methods – nominal cases
# ---------------------------------------------------------------------------
class TestConvenienceMethodsNominal:
    """Verify convenience methods delegate to the right repos."""

    def test_start_workout_returns_int(self, wdb):
        # Act
        sid = wdb.start_workout()

        # Assert
        assert isinstance(sid, int)

    def test_start_workout_with_user(self, wdb):
        # Arrange
        uid = wdb.users.create_user("Alice")

        # Act
        sid = wdb.start_workout(user_id=uid)

        # Assert
        assert isinstance(sid, int)
        session = wdb.sessions.get_session(sid)
        assert session["user_id"] == uid

    def test_end_workout_returns_true(self, wdb):
        # Arrange
        sid = wdb.start_workout()

        # Act
        result = wdb.end_workout(sid)

        # Assert
        assert result is True

    def test_end_workout_sets_duration(self, wdb):
        # Arrange
        sid = wdb.start_workout()

        # Act
        wdb.end_workout(sid, notes="good session")

        # Assert
        session = wdb.sessions.get_session(sid)
        assert session["end_time"] is not None
        assert session["total_duration_seconds"] is not None
        assert session["notes"] == "good session"

    def test_add_exercise_to_workout_returns_int(self, wdb):
        # Arrange
        sid = wdb.start_workout()

        # Act
        set_id = wdb.add_exercise_to_workout(sid, "squat")

        # Assert
        assert isinstance(set_id, int)

    def test_get_workout_summary_returns_dict(self, wdb):
        # Arrange
        sid = wdb.start_workout()
        wdb.add_exercise_to_workout(sid, "squat")

        # Act
        summary = wdb.get_workout_summary(sid)

        # Assert
        assert isinstance(summary, dict)
        assert "session" in summary
        assert "exercise_sets" in summary

    def test_get_streaks_returns_dict(self, wdb):
        # Act
        streaks = wdb.get_streaks()

        # Assert
        assert isinstance(streaks, dict)
        assert "current_streak" in streaks
        assert "longest_streak" in streaks

    def test_get_total_stats_returns_dict(self, wdb):
        # Act
        stats = wdb.get_total_stats()

        # Assert
        assert isinstance(stats, dict)
        assert "total_sessions" in stats
        assert "total_all_reps" in stats
        assert "reps_by_exercise" in stats


# ---------------------------------------------------------------------------
# Convenience methods – edge cases
# ---------------------------------------------------------------------------
class TestConvenienceMethodsEdge:
    """Edge cases for convenience methods."""

    def test_end_workout_nonexistent_session(self, wdb):
        # Act
        result = wdb.end_workout(999)

        # Assert
        assert result is False

    def test_add_exercise_nonexistent_session(self, wdb):
        # Act
        result = wdb.add_exercise_to_workout(999, "squat")

        # Assert
        assert result is None

    def test_get_workout_summary_nonexistent_session(self, wdb):
        # Act
        summary = wdb.get_workout_summary(999)

        # Assert
        assert summary == {}


# ---------------------------------------------------------------------------
# Legacy methods – nominal cases
# ---------------------------------------------------------------------------
class TestLegacyMethodsNominal:
    """Verify legacy methods delegate correctly."""

    def test_start_session_delegates_to_start_workout(self, wdb):
        # Act
        sid = wdb.start_session()

        # Assert
        assert isinstance(sid, int)

    def test_end_session_delegates_to_end_workout(self, wdb):
        # Arrange
        sid = wdb.start_workout()

        # Act
        result = wdb.end_session(sid)

        # Assert
        assert result is True

    def test_create_exercise_set_delegates(self, wdb):
        # Arrange
        sid = wdb.start_workout()

        # Act
        set_id = wdb.create_exercise_set(sid, "pushup")

        # Assert
        assert isinstance(set_id, int)

    def test_update_exercise_set_delegates(self, wdb):
        # Arrange
        sid = wdb.start_workout()
        set_id = wdb.add_exercise_to_workout(sid, "squat")

        # Act
        result = wdb.update_exercise_set(set_id, {"total_reps": 10})

        # Assert
        assert result is True

    def test_get_session_summary_delegates(self, wdb):
        # Arrange
        sid = wdb.start_workout()

        # Act
        summary = wdb.get_session_summary(sid)

        # Assert
        assert isinstance(summary, dict)
        assert "session" in summary

    def test_get_recent_sessions_delegates(self, wdb):
        # Arrange
        wdb.start_workout()

        # Act
        sessions = wdb.get_recent_sessions()

        # Assert
        assert isinstance(sessions, list)
        assert len(sessions) == 1

    def test_get_recent_sessions_respects_limit(self, wdb):
        # Arrange
        for _ in range(5):
            wdb.start_workout()

        # Act
        sessions = wdb.get_recent_sessions(limit=3)

        # Assert
        assert len(sessions) == 3

    def test_get_streak_data_delegates(self, wdb):
        # Act
        streaks = wdb.get_streak_data()

        # Assert
        assert isinstance(streaks, dict)
        assert "current_streak" in streaks

    def test_log_rep_delegates(self, wdb):
        """log_rep -> log_rep_with_stats -> reps.log_rep."""
        # Arrange
        sid = wdb.start_workout()
        set_id = wdb.add_exercise_to_workout(sid, "squat")

        # Act
        result = wdb.log_rep(set_id, 1, "excellent", 90.0, 1.5)

        # Assert
        assert result is True


# ---------------------------------------------------------------------------
# Legacy methods – edge cases
# ---------------------------------------------------------------------------
class TestLegacyMethodsEdge:
    """Edge cases for legacy methods."""

    def test_end_session_nonexistent(self, wdb):
        # Act
        result = wdb.end_session(999)

        # Assert
        assert result is False

    def test_update_exercise_set_nonexistent(self, wdb):
        # Act
        result = wdb.update_exercise_set(999, {"total_reps": 5})

        # Assert
        assert result is False


# ---------------------------------------------------------------------------
# Full workflow – integration through facade
# ---------------------------------------------------------------------------
class TestFullWorkflowNominal:
    """End-to-end workflow through WorkoutDatabase facade."""

    def test_complete_workout_flow(self, wdb):
        # Arrange – create user
        uid = wdb.users.create_user("Alice")

        # Act – start workout, add exercises, log reps, end workout
        sid = wdb.start_workout(user_id=uid)
        set_id = wdb.add_exercise_to_workout(sid, "squat")
        wdb.reps.log_rep(set_id, 1, "excellent", 85.0, 1.2)
        wdb.reps.log_rep(set_id, 2, "good", 95.0, 1.5)
        wdb.reps.log_rep(set_id, 3, "poor", 120.0, 2.0)
        wdb.exercise_sets.update_exercise_set_stats(set_id, {
            "total_reps": 3,
            "excellent_reps": 1,
            "good_reps": 1,
            "poor_reps": 1,
            "average_angle": 100.0,
        })
        wdb.end_workout(sid, notes="first workout")

        # Assert – summary has everything
        summary = wdb.get_workout_summary(sid)
        assert summary["session"]["notes"] == "first workout"
        assert len(summary["exercise_sets"]) == 1
        assert summary["exercise_sets"][0]["exercise_name"] == "squat"
        assert summary["exercise_sets"][0]["total_reps"] == 3
        assert len(summary["exercise_sets"][0]["reps"]) == 3

    def test_stats_reflect_workout(self, wdb):
        # Arrange – complete a workout with reps
        sid = wdb.start_workout()
        set_id = wdb.add_exercise_to_workout(sid, "curl")
        wdb.exercise_sets.update_exercise_set_stats(set_id, {
            "total_reps": 8,
            "excellent_reps": 4,
            "good_reps": 3,
            "poor_reps": 1,
        })
        wdb.end_workout(sid)

        # Act
        stats = wdb.get_total_stats()

        # Assert
        assert stats["total_sessions"] == 1
        assert stats["total_all_reps"] == 8
        assert stats["total_excellent_reps"] == 4
        assert stats["reps_by_exercise"] == {"curl": 8}

    def test_multiple_exercises_in_workout(self, wdb):
        # Arrange
        sid = wdb.start_workout()
        squat_id = wdb.add_exercise_to_workout(sid, "squat")
        pushup_id = wdb.add_exercise_to_workout(sid, "pushup")
        wdb.exercise_sets.update_exercise_set_stats(squat_id, {"total_reps": 10})
        wdb.exercise_sets.update_exercise_set_stats(pushup_id, {"total_reps": 15})
        wdb.end_workout(sid)

        # Act
        stats = wdb.get_total_stats()

        # Assert
        assert stats["total_all_reps"] == 25
        assert stats["reps_by_exercise"]["squat"] == 10
        assert stats["reps_by_exercise"]["pushup"] == 15


# ---------------------------------------------------------------------------
# close – nominal & edge cases
# ---------------------------------------------------------------------------
class TestCloseNominal:
    """Verify close shuts down cleanly."""

    def test_close_sets_conn_to_none(self, tmp_db):
        # Arrange
        db = WorkoutDatabase(db_path=tmp_db)

        # Act
        db.close()

        # Assert
        assert db.connection.conn is None

    def test_close_sets_cursor_to_none(self, tmp_db):
        # Arrange
        db = WorkoutDatabase(db_path=tmp_db)

        # Act
        db.close()

        # Assert
        assert db.connection.cursor is None


class TestCloseEdge:
    """Edge cases for closing."""

    def test_double_close_does_not_raise(self, tmp_db):
        # Arrange
        db = WorkoutDatabase(db_path=tmp_db)

        # Act / Assert – no exception
        db.close()
        db.close()
