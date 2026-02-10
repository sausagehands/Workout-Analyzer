"""Unit tests for StatsRepository module.

Tests get_total_stats, get_streak_data, consolidate_old_data,
and get_monthly_stats using Arrange-Act-Assert structure with
nominal and edge cases.
"""
import sqlite3
from datetime import datetime, date, timedelta

import pytest

from database.database_connection import DatabaseConnection
from database.stats import StatsRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def tmp_db(tmp_path):
    """Return a path to a temporary .db file inside pytest's tmp directory."""
    return str(tmp_path / "test_stats.db")


@pytest.fixture
def db(tmp_db):
    """Yield a DatabaseConnection with all required tables, then close it."""
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
    conn.cursor.execute("""
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
    conn.commit()
    yield conn
    if conn.conn is not None:
        conn.close()


@pytest.fixture
def repo(db):
    """Return a StatsRepository backed by the test database."""
    return StatsRepository(db)


# ---------------------------------------------------------------------------
# Helpers – insert test data
# ---------------------------------------------------------------------------
def _seed_exercise_types(db):
    """Insert default exercise types and return their IDs."""
    types = {}
    for name in ["squat", "pushup", "curl"]:
        db.cursor.execute(
            "INSERT OR IGNORE INTO exercise_types (name) VALUES (?)", (name,)
        )
        db.cursor.execute(
            "SELECT exercise_type_id FROM exercise_types WHERE name = ?", (name,)
        )
        types[name] = db.cursor.fetchone()["exercise_type_id"]
    db.conn.commit()
    return types


def _create_session(db, start_time, duration=60):
    """Create a workout session with a given start_time and duration."""
    end_time = start_time  # simplified
    db.cursor.execute("""
        INSERT INTO workout_sessions (start_time, end_time, total_duration_seconds)
        VALUES (?, ?, ?)
    """, (start_time, end_time, duration))
    db.conn.commit()
    return db.cursor.lastrowid


def _create_exercise_set(db, session_id, exercise_type_id,
                         total_reps=0, excellent=0, good=0, poor=0,
                         average_angle=None):
    """Create an exercise set with given stats."""
    db.cursor.execute("""
        INSERT INTO exercise_sets
            (session_id, exercise_type_id, total_reps, excellent_reps, good_reps, poor_reps,
             average_angle)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (session_id, exercise_type_id, total_reps, excellent, good, poor,
          average_angle))
    db.conn.commit()
    return db.cursor.lastrowid


# ---------------------------------------------------------------------------
# get_total_stats – nominal cases
# ---------------------------------------------------------------------------
class TestGetTotalStatsNominal:
    """Verify all-time statistics aggregation."""

    def test_returns_dict(self, repo):
        # Act
        stats = repo.get_total_stats()

        # Assert
        assert isinstance(stats, dict)

    def test_has_all_expected_keys(self, repo):
        # Act
        stats = repo.get_total_stats()

        # Assert
        expected_keys = {
            "total_sessions", "total_time_seconds",
            "total_all_reps", "total_excellent_reps",
            "total_good_reps", "total_poor_reps",
            "reps_by_exercise",
        }
        assert set(stats.keys()) == expected_keys

    def test_counts_total_sessions(self, repo, db):
        # Arrange
        types = _seed_exercise_types(db)
        s1 = _create_session(db, "2024-06-01 10:00:00")
        s2 = _create_session(db, "2024-06-02 10:00:00")
        _create_exercise_set(db, s1, types["squat"], total_reps=5)
        _create_exercise_set(db, s2, types["squat"], total_reps=5)

        # Act
        stats = repo.get_total_stats()

        # Assert
        assert stats["total_sessions"] == 2

    def test_sums_duration(self, repo, db):
        # Arrange
        types = _seed_exercise_types(db)
        s1 = _create_session(db, "2024-06-01 10:00:00", duration=120)
        s2 = _create_session(db, "2024-06-02 10:00:00", duration=180)
        _create_exercise_set(db, s1, types["squat"], total_reps=5)
        _create_exercise_set(db, s2, types["squat"], total_reps=5)

        # Act
        stats = repo.get_total_stats()

        # Assert
        assert stats["total_time_seconds"] == 300

    def test_duration_not_double_counted_with_multiple_sets(self, repo, db):
        """Regression: a session with 3 sets should count duration once, not 3x."""
        # Arrange – one session, three exercise sets
        types = _seed_exercise_types(db)
        sid = _create_session(db, "2024-06-01 10:00:00", duration=300)
        _create_exercise_set(db, sid, types["squat"], total_reps=10)
        _create_exercise_set(db, sid, types["pushup"], total_reps=10)
        _create_exercise_set(db, sid, types["curl"], total_reps=10)

        # Act
        stats = repo.get_total_stats()

        # Assert – should be 300, NOT 900
        assert stats["total_time_seconds"] == 300

    def test_counts_by_exercise_type(self, repo, db):
        # Arrange
        types = _seed_exercise_types(db)
        sid = _create_session(db, "2024-06-01 10:00:00")
        _create_exercise_set(db, sid, types["squat"], total_reps=10)
        _create_exercise_set(db, sid, types["pushup"], total_reps=15)
        _create_exercise_set(db, sid, types["curl"], total_reps=20)

        # Act
        stats = repo.get_total_stats()

        # Assert
        reps = stats["reps_by_exercise"]
        assert reps["squat"] == 10
        assert reps["pushup"] == 15
        assert reps["curl"] == 20
        assert stats["total_all_reps"] == 45

    def test_counts_quality_breakdown(self, repo, db):
        # Arrange
        types = _seed_exercise_types(db)
        sid = _create_session(db, "2024-06-01 10:00:00")
        _create_exercise_set(db, sid, types["squat"],
                             total_reps=10, excellent=5, good=3, poor=2)

        # Act
        stats = repo.get_total_stats()

        # Assert
        assert stats["total_excellent_reps"] == 5
        assert stats["total_good_reps"] == 3
        assert stats["total_poor_reps"] == 2

    def test_new_exercise_type_appears_dynamically(self, repo, db):
        # Arrange – add a non-default exercise type
        db.cursor.execute(
            "INSERT INTO exercise_types (name) VALUES (?)", ("deadlift",)
        )
        deadlift_id = db.cursor.lastrowid
        sid = _create_session(db, "2024-06-01 10:00:00")
        _create_exercise_set(db, sid, deadlift_id, total_reps=25)

        # Act
        stats = repo.get_total_stats()

        # Assert – "deadlift" shows up without any code change
        assert stats["reps_by_exercise"]["deadlift"] == 25
        assert stats["total_all_reps"] == 25


# ---------------------------------------------------------------------------
# get_total_stats – edge cases
# ---------------------------------------------------------------------------
class TestGetTotalStatsEdge:
    """Edge cases for total stats."""

    def test_empty_database_returns_zeros(self, repo):
        # Act
        stats = repo.get_total_stats()

        # Assert
        assert stats["total_sessions"] == 0
        assert stats["total_time_seconds"] == 0
        assert stats["total_all_reps"] == 0
        assert stats["reps_by_exercise"] == {}

    def test_session_with_no_exercise_sets(self, repo, db):
        # Arrange – session exists but no sets
        _create_session(db, "2024-06-01 10:00:00")

        # Act
        stats = repo.get_total_stats()

        # Assert – JOIN means no rows, so zeros
        assert stats["total_sessions"] == 0
        assert stats["total_all_reps"] == 0

    def test_zero_rep_set_excluded_from_stats(self, repo, db):
        """Sets with total_reps=0 should not appear in stats."""
        # Arrange – one real set, one empty set
        types = _seed_exercise_types(db)
        sid = _create_session(db, "2024-06-01 10:00:00", duration=200)
        _create_exercise_set(db, sid, types["squat"], total_reps=10,
                             excellent=5, good=3, poor=2)
        _create_exercise_set(db, sid, types["pushup"], total_reps=0)

        # Act
        stats = repo.get_total_stats()

        # Assert – only squat counted
        assert stats["total_all_reps"] == 10
        assert stats["total_excellent_reps"] == 5
        assert stats["reps_by_exercise"] == {"squat": 10}
        assert "pushup" not in stats["reps_by_exercise"]

    def test_zero_rep_session_excluded_from_session_count(self, repo, db):
        """A session with only zero-rep sets is not a real workout."""
        # Arrange – session with only empty sets
        types = _seed_exercise_types(db)
        sid = _create_session(db, "2024-06-01 10:00:00", duration=60)
        _create_exercise_set(db, sid, types["squat"], total_reps=0)
        _create_exercise_set(db, sid, types["curl"], total_reps=0)

        # Act
        stats = repo.get_total_stats()

        # Assert – session doesn't count
        assert stats["total_sessions"] == 0
        assert stats["total_time_seconds"] == 0

    def test_zero_rep_set_duration_excluded(self, repo, db):
        """Duration only counted for sessions with real reps."""
        # Arrange – one real session, one empty session
        types = _seed_exercise_types(db)
        s1 = _create_session(db, "2024-06-01 10:00:00", duration=300)
        _create_exercise_set(db, s1, types["squat"], total_reps=10)
        s2 = _create_session(db, "2024-06-02 10:00:00", duration=200)
        _create_exercise_set(db, s2, types["pushup"], total_reps=0)

        # Act
        stats = repo.get_total_stats()

        # Assert – only first session's duration
        assert stats["total_sessions"] == 1
        assert stats["total_time_seconds"] == 300


# ---------------------------------------------------------------------------
# get_streak_data – nominal cases
# ---------------------------------------------------------------------------
class TestGetStreakDataNominal:
    """Verify streak calculations."""

    def test_returns_dict(self, repo):
        # Act
        streaks = repo.get_streak_data()

        # Assert
        assert isinstance(streaks, dict)

    def test_has_expected_keys(self, repo):
        # Act
        streaks = repo.get_streak_data()

        # Assert
        assert "current_streak" in streaks
        assert "longest_streak" in streaks

    def test_current_streak_today_only(self, repo, db):
        # Arrange – worked out today
        today = date.today().strftime("%Y-%m-%d 10:00:00")
        _create_session(db, today)

        # Act
        streaks = repo.get_streak_data()

        # Assert
        assert streaks["current_streak"] == 1

    def test_current_streak_consecutive_days(self, repo, db):
        # Arrange – worked out today, yesterday, and day before
        today = date.today()
        for i in range(3):
            day = (today - timedelta(days=i)).strftime("%Y-%m-%d 10:00:00")
            _create_session(db, day)

        # Act
        streaks = repo.get_streak_data()

        # Assert
        assert streaks["current_streak"] == 3

    def test_current_streak_broken_by_gap(self, repo, db):
        # Arrange – today and 2 days ago (skipped yesterday)
        today = date.today()
        _create_session(db, today.strftime("%Y-%m-%d 10:00:00"))
        _create_session(db, (today - timedelta(days=2)).strftime("%Y-%m-%d 10:00:00"))

        # Act
        streaks = repo.get_streak_data()

        # Assert – only today counts
        assert streaks["current_streak"] == 1

    def test_longest_streak(self, repo, db):
        # Arrange – 5 consecutive days in the past, then a gap, then today
        today = date.today()
        _create_session(db, today.strftime("%Y-%m-%d 10:00:00"))
        # Gap at day -1
        for i in range(2, 7):  # days -2 through -6 (5 consecutive)
            day = (today - timedelta(days=i)).strftime("%Y-%m-%d 10:00:00")
            _create_session(db, day)

        # Act
        streaks = repo.get_streak_data()

        # Assert
        assert streaks["longest_streak"] == 5
        assert streaks["current_streak"] == 1

    def test_multiple_sessions_same_day_count_as_one(self, repo, db):
        # Arrange – 3 sessions today
        today = date.today().strftime("%Y-%m-%d")
        _create_session(db, f"{today} 08:00:00")
        _create_session(db, f"{today} 12:00:00")
        _create_session(db, f"{today} 18:00:00")

        # Act
        streaks = repo.get_streak_data()

        # Assert – still just 1 day streak
        assert streaks["current_streak"] == 1


# ---------------------------------------------------------------------------
# get_streak_data – edge cases
# ---------------------------------------------------------------------------
class TestGetStreakDataEdge:
    """Edge cases for streak data."""

    def test_no_sessions_returns_zeros(self, repo):
        # Act
        streaks = repo.get_streak_data()

        # Assert
        assert streaks["current_streak"] == 0
        assert streaks["longest_streak"] == 0

    def test_only_old_sessions_no_current_streak(self, repo, db):
        # Arrange – session from 30 days ago
        old_day = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d 10:00:00")
        _create_session(db, old_day)

        # Act
        streaks = repo.get_streak_data()

        # Assert
        assert streaks["current_streak"] == 0
        assert streaks["longest_streak"] == 1

    def test_single_session_in_past(self, repo, db):
        # Arrange
        old_day = (date.today() - timedelta(days=10)).strftime("%Y-%m-%d 10:00:00")
        _create_session(db, old_day)

        # Act
        streaks = repo.get_streak_data()

        # Assert
        assert streaks["longest_streak"] == 1


# ---------------------------------------------------------------------------
# consolidate_old_data – nominal cases
# ---------------------------------------------------------------------------
class TestConsolidateOldDataNominal:
    """Verify data consolidation into monthly stats."""

    def test_returns_dict(self, repo):
        # Act
        result = repo.consolidate_old_data()

        # Assert
        assert isinstance(result, dict)

    def test_has_expected_keys(self, repo):
        # Act
        result = repo.consolidate_old_data()

        # Assert
        assert "months_consolidated" in result
        assert "sessions_deleted" in result
        assert "sets_deleted" in result
        assert "reps_deleted" in result
        assert "errors" in result

    def test_consolidates_old_month(self, repo, db):
        # Arrange – data from 2 years ago
        types = _seed_exercise_types(db)
        old_date = "2022-03-15 10:00:00"
        sid = _create_session(db, old_date, duration=300)
        _create_exercise_set(db, sid, types["squat"],
                             total_reps=20, excellent=10, good=7, poor=3)

        # Act
        result = repo.consolidate_old_data(retention_days=365)

        # Assert
        assert result["months_consolidated"] >= 1
        assert result["errors"] == []

    def test_creates_monthly_stats_row(self, repo, db):
        # Arrange
        types = _seed_exercise_types(db)
        old_date = "2022-06-10 10:00:00"
        sid = _create_session(db, old_date, duration=200)
        _create_exercise_set(db, sid, types["curl"],
                             total_reps=15, excellent=8, good=5, poor=2)

        # Act
        repo.consolidate_old_data(retention_days=365)

        # Assert – monthly_stats should have a row for 2022-06
        db.cursor.execute("""
            SELECT * FROM monthly_stats WHERE year = 2022 AND month = 6
        """)
        row = db.cursor.fetchone()
        assert row is not None
        assert row["total_reps"] == 15
        assert row["excellent_reps"] == 8

    def test_deletes_old_sessions(self, repo, db):
        # Arrange
        types = _seed_exercise_types(db)
        old_date = "2022-01-15 10:00:00"
        sid = _create_session(db, old_date)
        _create_exercise_set(db, sid, types["squat"], total_reps=5)

        # Act
        result = repo.consolidate_old_data(retention_days=365)

        # Assert
        assert result["sessions_deleted"] >= 1
        db.cursor.execute(
            "SELECT COUNT(*) as cnt FROM workout_sessions WHERE session_id = ?", (sid,)
        )
        assert db.cursor.fetchone()["cnt"] == 0

    def test_deletes_old_exercise_sets(self, repo, db):
        # Arrange
        types = _seed_exercise_types(db)
        old_date = "2022-01-15 10:00:00"
        sid = _create_session(db, old_date)
        set_id = _create_exercise_set(db, sid, types["squat"], total_reps=5)

        # Act
        result = repo.consolidate_old_data(retention_days=365)

        # Assert
        assert result["sets_deleted"] >= 1
        db.cursor.execute(
            "SELECT COUNT(*) as cnt FROM exercise_sets WHERE set_id = ?", (set_id,)
        )
        assert db.cursor.fetchone()["cnt"] == 0

    def test_average_angle_defaults_to_zero_not_null(self, repo, db):
        """COALESCE wraps AVG so consumers never get None for average_angle."""
        # Arrange – exercise set with no angle data
        types = _seed_exercise_types(db)
        old_date = "2022-07-10 10:00:00"
        sid = _create_session(db, old_date, duration=100)
        _create_exercise_set(db, sid, types["squat"], total_reps=5)

        # Act
        repo.consolidate_old_data(retention_days=365)

        # Assert
        db.cursor.execute("""
            SELECT average_angle FROM monthly_stats WHERE year = 2022 AND month = 7
        """)
        row = db.cursor.fetchone()
        assert row is not None
        assert row["average_angle"] == 0

    def test_average_angle_weighted_by_reps(self, repo, db):
        """Average angle is weighted by reps, not a plain AVG."""
        # Arrange – 2 reps at 90° and 8 reps at 110°
        types = _seed_exercise_types(db)
        old_date = "2022-08-10 10:00:00"
        sid = _create_session(db, old_date, duration=100)
        _create_exercise_set(db, sid, types["squat"], total_reps=2, average_angle=90.0)
        _create_exercise_set(db, sid, types["squat"], total_reps=8, average_angle=110.0)

        # Act
        repo.consolidate_old_data(retention_days=365)

        # Assert – weighted: (2*90 + 8*110) / (2+8) = 1060/10 = 106.0
        # A plain AVG would give 100.0 — that's wrong
        db.cursor.execute("""
            SELECT average_angle FROM monthly_stats WHERE year = 2022 AND month = 8
        """)
        row = db.cursor.fetchone()
        assert row is not None
        assert row["average_angle"] == 106.0

    def test_does_not_delete_recent_data(self, repo, db):
        # Arrange – session from yesterday (well within retention)
        types = _seed_exercise_types(db)
        yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d 10:00:00")
        sid = _create_session(db, yesterday)
        _create_exercise_set(db, sid, types["squat"], total_reps=10)

        # Act
        result = repo.consolidate_old_data(retention_days=365)

        # Assert – nothing deleted
        assert result["months_consolidated"] == 0
        assert result["sessions_deleted"] == 0
        db.cursor.execute(
            "SELECT COUNT(*) as cnt FROM workout_sessions WHERE session_id = ?", (sid,)
        )
        assert db.cursor.fetchone()["cnt"] == 1


# ---------------------------------------------------------------------------
# consolidate_old_data – edge cases
# ---------------------------------------------------------------------------
class TestConsolidateOldDataEdge:
    """Edge cases for data consolidation."""

    def test_empty_database(self, repo):
        # Act
        result = repo.consolidate_old_data()

        # Assert
        assert result["months_consolidated"] == 0
        assert result["sessions_deleted"] == 0
        assert result["errors"] == []

    def test_zero_rep_set_excluded_from_consolidation(self, repo, db):
        """Zero-rep sets should not create monthly_stats rows."""
        # Arrange – old session with one real set and one empty set
        types = _seed_exercise_types(db)
        old_date = "2022-09-10 10:00:00"
        sid = _create_session(db, old_date, duration=100)
        _create_exercise_set(db, sid, types["squat"], total_reps=10,
                             excellent=5, good=3, poor=2)
        _create_exercise_set(db, sid, types["pushup"], total_reps=0)

        # Act
        repo.consolidate_old_data(retention_days=365)

        # Assert – squat row exists, pushup row does not
        db.cursor.execute("""
            SELECT exercise_type_id, total_reps FROM monthly_stats
            WHERE year = 2022 AND month = 9
        """)
        rows = db.cursor.fetchall()
        assert len(rows) == 1
        assert rows[0]["total_reps"] == 10

    def test_upsert_does_not_duplicate(self, repo, db):
        # Arrange
        types = _seed_exercise_types(db)
        old_date = "2022-04-10 10:00:00"
        sid = _create_session(db, old_date)
        _create_exercise_set(db, sid, types["squat"], total_reps=10)

        # Act – consolidate twice (second time re-inserts same data before deletion)
        # First consolidation
        repo.consolidate_old_data(retention_days=365)

        # Assert – only one monthly_stats row for that month/exercise
        db.cursor.execute("""
            SELECT COUNT(*) as cnt FROM monthly_stats
            WHERE year = 2022 AND month = 4
        """)
        assert db.cursor.fetchone()["cnt"] == 1


# ---------------------------------------------------------------------------
# get_monthly_stats – nominal cases
# ---------------------------------------------------------------------------
class TestGetMonthlyStatsNominal:
    """Verify fetching consolidated monthly stats."""

    def test_returns_list(self, repo):
        # Act
        stats = repo.get_monthly_stats()

        # Assert
        assert isinstance(stats, list)

    def test_returns_all_stats_unfiltered(self, repo, db):
        # Arrange – insert monthly stats directly
        types = _seed_exercise_types(db)
        db.cursor.execute("""
            INSERT INTO monthly_stats
                (year, month, exercise_type_id, total_reps)
            VALUES (2024, 1, ?, 100)
        """, (types["squat"],))
        db.cursor.execute("""
            INSERT INTO monthly_stats
                (year, month, exercise_type_id, total_reps)
            VALUES (2024, 2, ?, 200)
        """, (types["squat"],))
        db.conn.commit()

        # Act
        stats = repo.get_monthly_stats()

        # Assert
        assert len(stats) == 2

    def test_filter_by_year_and_month(self, repo, db):
        # Arrange
        types = _seed_exercise_types(db)
        db.cursor.execute("""
            INSERT INTO monthly_stats
                (year, month, exercise_type_id, total_reps)
            VALUES (2024, 3, ?, 50)
        """, (types["curl"],))
        db.cursor.execute("""
            INSERT INTO monthly_stats
                (year, month, exercise_type_id, total_reps)
            VALUES (2024, 4, ?, 75)
        """, (types["curl"],))
        db.conn.commit()

        # Act
        stats = repo.get_monthly_stats(year=2024, month=3)

        # Assert
        assert len(stats) == 1
        assert stats[0]["total_reps"] == 50

    def test_filter_by_year_only(self, repo, db):
        # Arrange
        types = _seed_exercise_types(db)
        db.cursor.execute("""
            INSERT INTO monthly_stats
                (year, month, exercise_type_id, total_reps)
            VALUES (2024, 1, ?, 100)
        """, (types["squat"],))
        db.cursor.execute("""
            INSERT INTO monthly_stats
                (year, month, exercise_type_id, total_reps)
            VALUES (2024, 6, ?, 200)
        """, (types["squat"],))
        db.cursor.execute("""
            INSERT INTO monthly_stats
                (year, month, exercise_type_id, total_reps)
            VALUES (2023, 12, ?, 50)
        """, (types["squat"],))
        db.conn.commit()

        # Act
        stats = repo.get_monthly_stats(year=2024)

        # Assert
        assert len(stats) == 2

    def test_includes_exercise_name(self, repo, db):
        # Arrange
        types = _seed_exercise_types(db)
        db.cursor.execute("""
            INSERT INTO monthly_stats
                (year, month, exercise_type_id, total_reps)
            VALUES (2024, 5, ?, 30)
        """, (types["pushup"],))
        db.conn.commit()

        # Act
        stats = repo.get_monthly_stats()

        # Assert
        assert stats[0]["exercise_name"] == "pushup"

    def test_each_entry_is_dict(self, repo, db):
        # Arrange
        types = _seed_exercise_types(db)
        db.cursor.execute("""
            INSERT INTO monthly_stats
                (year, month, exercise_type_id, total_reps)
            VALUES (2024, 1, ?, 10)
        """, (types["squat"],))
        db.conn.commit()

        # Act
        stats = repo.get_monthly_stats()

        # Assert
        assert isinstance(stats[0], dict)

    def test_ordered_most_recent_first(self, repo, db):
        # Arrange
        types = _seed_exercise_types(db)
        db.cursor.execute("""
            INSERT INTO monthly_stats
                (year, month, exercise_type_id, total_reps)
            VALUES (2024, 1, ?, 10)
        """, (types["squat"],))
        db.cursor.execute("""
            INSERT INTO monthly_stats
                (year, month, exercise_type_id, total_reps)
            VALUES (2024, 6, ?, 20)
        """, (types["squat"],))
        db.conn.commit()

        # Act
        stats = repo.get_monthly_stats()

        # Assert – June before January
        assert stats[0]["month"] == 6
        assert stats[1]["month"] == 1


# ---------------------------------------------------------------------------
# get_monthly_stats – edge cases
# ---------------------------------------------------------------------------
class TestGetMonthlyStatsEdge:
    """Edge cases for monthly stats."""

    def test_empty_returns_empty_list(self, repo):
        # Act
        stats = repo.get_monthly_stats()

        # Assert
        assert stats == []

    def test_nonexistent_year_returns_empty(self, repo, db):
        # Arrange
        types = _seed_exercise_types(db)
        db.cursor.execute("""
            INSERT INTO monthly_stats
                (year, month, exercise_type_id, total_reps)
            VALUES (2024, 1, ?, 10)
        """, (types["squat"],))
        db.conn.commit()

        # Act
        stats = repo.get_monthly_stats(year=2099)

        # Assert
        assert stats == []

    def test_nonexistent_month_returns_empty(self, repo, db):
        # Arrange
        types = _seed_exercise_types(db)
        db.cursor.execute("""
            INSERT INTO monthly_stats
                (year, month, exercise_type_id, total_reps)
            VALUES (2024, 1, ?, 10)
        """, (types["squat"],))
        db.conn.commit()

        # Act
        stats = repo.get_monthly_stats(year=2024, month=12)

        # Assert
        assert stats == []
