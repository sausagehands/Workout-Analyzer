"""Integration tests — full workout lifecycle.

Exercises the real call chain that workout_engine.py uses:
  start_session → create_exercise_set → log_rep (× N)
  → update_exercise_set_stats → end_session
  → get_session_summary / get_total_stats / get_exercise_history

Every test goes through WorkoutDatabase (the facade) so all five
repositories collaborate through a single shared connection.
"""
import time

import pytest

from database.workout_database import WorkoutDatabase


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def wdb(tmp_path):
    """Yield a WorkoutDatabase backed by a temp file, then close it."""
    db = WorkoutDatabase(db_path=str(tmp_path / "integration.db"))
    yield db
    if db.connection.conn is not None:
        db.close()


def _do_reps(wdb, set_id, reps):
    """Log a list of (quality, angle, duration) tuples through the facade."""
    for i, (quality, angle, duration) in enumerate(reps, start=1):
        wdb.log_rep(set_id, i, quality, angle, duration)


# ---------------------------------------------------------------------------
# Single-workout lifecycle
# ---------------------------------------------------------------------------
class TestSingleWorkoutLifecycle:
    """Start → exercise → reps → update stats → end → verify."""

    def test_session_summary_matches_logged_reps(self, wdb):
        # Arrange / Act — mimic workout_engine flow
        sid = wdb.start_workout()
        set_id = wdb.add_exercise_to_workout(sid, "squat")
        _do_reps(wdb, set_id, [
            ("excellent", 85.0, 1.2),
            ("good", 95.0, 1.5),
            ("poor", 120.0, 2.0),
        ])
        wdb.update_exercise_set(set_id, {
            "total_reps": 3, "excellent_reps": 1, "good_reps": 1,
            "poor_reps": 1, "average_angle": 100.0,
            "min_angle": 85.0, "max_angle": 120.0, "duration_seconds": 5,
        })
        wdb.end_workout(sid, notes="leg day")

        # Assert — summary pulls from sessions + exercise_sets + reps
        summary = wdb.get_workout_summary(sid)
        assert summary["session"]["notes"] == "leg day"
        assert summary["session"]["total_duration_seconds"] is not None

        es = summary["exercise_sets"]
        assert len(es) == 1
        assert es[0]["exercise_name"] == "squat"
        assert es[0]["total_reps"] == 3
        assert len(es[0]["reps"]) == 3

    def test_rep_counters_increment_via_log_rep(self, wdb):
        """log_rep atomically bumps exercise_sets counters."""
        sid = wdb.start_workout()
        set_id = wdb.add_exercise_to_workout(sid, "curl")

        _do_reps(wdb, set_id, [
            ("excellent", 40.0, 1.0),
            ("excellent", 42.0, 1.1),
            ("good", 55.0, 1.3),
        ])

        # Read counters directly — should reflect log_rep increments
        wdb.connection.cursor.execute(
            "SELECT total_reps, excellent_reps, good_reps, poor_reps "
            "FROM exercise_sets WHERE set_id = ?", (set_id,)
        )
        row = dict(wdb.connection.cursor.fetchone())
        assert row["total_reps"] == 3
        assert row["excellent_reps"] == 2
        assert row["good_reps"] == 1
        assert row["poor_reps"] == 0

    def test_update_exercise_set_overwrites_counters(self, wdb):
        """update_exercise_set replaces the counters set by log_rep."""
        sid = wdb.start_workout()
        set_id = wdb.add_exercise_to_workout(sid, "pushup")

        # Log 2 reps via log_rep
        _do_reps(wdb, set_id, [
            ("excellent", 80.0, 1.0),
            ("poor", 130.0, 2.5),
        ])

        # Overwrite with final stats (workout_engine does this)
        wdb.update_exercise_set(set_id, {
            "total_reps": 2, "excellent_reps": 1, "good_reps": 0,
            "poor_reps": 1, "average_angle": 105.0,
            "min_angle": 80.0, "max_angle": 130.0, "duration_seconds": 4,
        })

        wdb.connection.cursor.execute(
            "SELECT average_angle, min_angle, max_angle, duration_seconds "
            "FROM exercise_sets WHERE set_id = ?", (set_id,)
        )
        row = dict(wdb.connection.cursor.fetchone())
        assert row["average_angle"] == pytest.approx(105.0)
        assert row["min_angle"] == pytest.approx(80.0)
        assert row["max_angle"] == pytest.approx(130.0)
        assert row["duration_seconds"] == 4

    def test_multiple_sets_in_one_session(self, wdb):
        """Session with squats then curls — summary returns both."""
        sid = wdb.start_workout()

        squat_id = wdb.add_exercise_to_workout(sid, "squat")
        _do_reps(wdb, squat_id, [("excellent", 85.0, 1.0)])
        wdb.update_exercise_set(squat_id, {
            "total_reps": 1, "excellent_reps": 1,
        })

        curl_id = wdb.add_exercise_to_workout(sid, "curl")
        _do_reps(wdb, curl_id, [("good", 50.0, 1.5)])
        wdb.update_exercise_set(curl_id, {
            "total_reps": 1, "good_reps": 1,
        })

        wdb.end_workout(sid)

        summary = wdb.get_workout_summary(sid)
        names = [s["exercise_name"] for s in summary["exercise_sets"]]
        assert "squat" in names
        assert "curl" in names
        assert len(summary["exercise_sets"]) == 2


# ---------------------------------------------------------------------------
# Cross-session stats
# ---------------------------------------------------------------------------
class TestCrossSessionStats:
    """Stats aggregate correctly across multiple sessions."""

    def _quick_workout(self, wdb, exercise, reps_data, notes=""):
        """Helper: start → add exercise → log reps → update stats → end."""
        sid = wdb.start_workout()
        set_id = wdb.add_exercise_to_workout(sid, exercise)
        _do_reps(wdb, set_id, reps_data)
        total = len(reps_data)
        excellent = sum(1 for q, _, _ in reps_data if q == "excellent")
        good = sum(1 for q, _, _ in reps_data if q == "good")
        poor = sum(1 for q, _, _ in reps_data if q == "poor")
        angles = [a for _, a, _ in reps_data]
        wdb.update_exercise_set(set_id, {
            "total_reps": total, "excellent_reps": excellent,
            "good_reps": good, "poor_reps": poor,
            "average_angle": sum(angles) / len(angles),
            "min_angle": min(angles), "max_angle": max(angles),
        })
        wdb.end_workout(sid, notes=notes)
        return sid

    def test_total_stats_accumulate_across_sessions(self, wdb):
        # Arrange – two separate workouts
        self._quick_workout(wdb, "squat", [
            ("excellent", 85.0, 1.0),
            ("good", 95.0, 1.2),
        ])
        self._quick_workout(wdb, "squat", [
            ("excellent", 80.0, 1.0),
            ("poor", 125.0, 2.0),
            ("excellent", 82.0, 1.1),
        ])

        # Act
        stats = wdb.get_total_stats()

        # Assert
        assert stats["total_sessions"] == 2
        assert stats["total_all_reps"] == 5
        assert stats["total_excellent_reps"] == 3
        assert stats["total_good_reps"] == 1
        assert stats["total_poor_reps"] == 1
        assert stats["reps_by_exercise"]["squat"] == 5

    def test_reps_by_exercise_tracks_multiple_types(self, wdb):
        self._quick_workout(wdb, "squat", [("excellent", 85.0, 1.0)] * 4)
        self._quick_workout(wdb, "curl", [("good", 50.0, 1.0)] * 6)
        self._quick_workout(wdb, "pushup", [("poor", 110.0, 1.0)] * 3)

        stats = wdb.get_total_stats()
        assert stats["reps_by_exercise"]["squat"] == 4
        assert stats["reps_by_exercise"]["curl"] == 6
        assert stats["reps_by_exercise"]["pushup"] == 3
        assert stats["total_all_reps"] == 13

    def test_exercise_history_returns_sets_with_reps(self, wdb):
        """get_exercise_history filters out zero-rep sets."""
        sid = wdb.start_workout()

        # Set with reps
        s1 = wdb.add_exercise_to_workout(sid, "squat")
        wdb.update_exercise_set(s1, {"total_reps": 10, "excellent_reps": 10})

        # Set without reps (user started but didn't do any)
        wdb.add_exercise_to_workout(sid, "squat")

        wdb.end_workout(sid)

        history = wdb.exercise_sets.get_exercise_history("squat")
        assert len(history) == 1
        assert history[0]["total_reps"] == 10

    def test_recent_sessions_ordered_newest_first(self, wdb):
        s1 = wdb.start_workout()
        wdb.end_workout(s1, notes="first")
        s2 = wdb.start_workout()
        wdb.end_workout(s2, notes="second")
        s3 = wdb.start_workout()
        wdb.end_workout(s3, notes="third")

        recent = wdb.get_recent_sessions(limit=3)
        assert recent[0]["notes"] == "third"
        assert recent[2]["notes"] == "first"


# ---------------------------------------------------------------------------
# User ↔ session relationship
# ---------------------------------------------------------------------------
class TestUserSessionRelationship:
    """Verify user ↔ session foreign key flows."""

    def test_session_linked_to_user(self, wdb):
        uid = wdb.users.create_user("Alice")
        sid = wdb.start_workout(user_id=uid)

        session = wdb.sessions.get_session(sid)
        assert session["user_id"] == uid
        assert session["user_name"] == "Alice"

    def test_session_without_user(self, wdb):
        sid = wdb.start_workout()
        session = wdb.sessions.get_session(sid)
        assert session["user_id"] is None
        assert session["user_name"] is None

    def test_user_rename_reflected_in_session(self, wdb):
        uid = wdb.users.create_user("Alice")
        sid = wdb.start_workout(user_id=uid)
        wdb.users.update_profile(uid, name="Bob")

        session = wdb.sessions.get_session(sid)
        assert session["user_name"] == "Bob"

    def test_multiple_users_separate_sessions(self, wdb):
        u1 = wdb.users.create_user("Alice")
        u2 = wdb.users.create_user("Bob")
        s1 = wdb.start_workout(user_id=u1)
        s2 = wdb.start_workout(user_id=u2)

        assert wdb.sessions.get_session(s1)["user_name"] == "Alice"
        assert wdb.sessions.get_session(s2)["user_name"] == "Bob"


# ---------------------------------------------------------------------------
# Exercise type creation (dynamic)
# ---------------------------------------------------------------------------
class TestDynamicExerciseTypes:
    """Exercise types are created on-the-fly by create_exercise_set."""

    def test_seed_types_exist_at_startup(self, wdb):
        wdb.connection.cursor.execute(
            "SELECT name FROM exercise_types ORDER BY name"
        )
        names = [r["name"] for r in wdb.connection.cursor.fetchall()]
        assert set(names) >= {"curl", "pushup", "squat"}

    def test_new_exercise_type_created_on_first_use(self, wdb):
        sid = wdb.start_workout()
        wdb.add_exercise_to_workout(sid, "deadlift")

        wdb.connection.cursor.execute(
            "SELECT name FROM exercise_types WHERE name = 'deadlift'"
        )
        assert wdb.connection.cursor.fetchone() is not None

    def test_reuses_existing_exercise_type(self, wdb):
        sid = wdb.start_workout()
        wdb.add_exercise_to_workout(sid, "squat")
        wdb.add_exercise_to_workout(sid, "squat")

        wdb.connection.cursor.execute(
            "SELECT COUNT(*) as cnt FROM exercise_types WHERE name = 'squat'"
        )
        assert wdb.connection.cursor.fetchone()["cnt"] == 1

    def test_new_type_appears_in_stats(self, wdb):
        sid = wdb.start_workout()
        set_id = wdb.add_exercise_to_workout(sid, "lunges")
        wdb.update_exercise_set(set_id, {"total_reps": 12, "excellent_reps": 12})
        wdb.end_workout(sid)

        stats = wdb.get_total_stats()
        assert stats["reps_by_exercise"]["lunges"] == 12


# ---------------------------------------------------------------------------
# Rep logging ↔ reps table ↔ exercise_sets counters
# ---------------------------------------------------------------------------
class TestRepIntegration:
    """log_rep inserts into reps AND increments exercise_sets counters."""

    def test_rep_stats_match_logged_reps(self, wdb):
        sid = wdb.start_workout()
        set_id = wdb.add_exercise_to_workout(sid, "curl")
        _do_reps(wdb, set_id, [
            ("excellent", 40.0, 1.0),
            ("excellent", 42.0, 1.1),
            ("good", 55.0, 1.3),
            ("poor", 70.0, 2.0),
        ])

        rep_stats = wdb.reps.get_rep_stats(set_id)
        assert rep_stats["total_reps"] == 4
        assert rep_stats["excellent_reps"] == 2
        assert rep_stats["good_reps"] == 1
        assert rep_stats["poor_reps"] == 1
        assert rep_stats["avg_peak_angle"] == pytest.approx(51.75)
        assert rep_stats["min_peak_angle"] == pytest.approx(40.0)
        assert rep_stats["max_peak_angle"] == pytest.approx(70.0)

    def test_reps_appear_in_session_summary(self, wdb):
        sid = wdb.start_workout()
        set_id = wdb.add_exercise_to_workout(sid, "pushup")
        _do_reps(wdb, set_id, [
            ("excellent", 80.0, 1.0),
            ("good", 100.0, 1.5),
        ])
        wdb.update_exercise_set(set_id, {"total_reps": 2, "excellent_reps": 1, "good_reps": 1})
        wdb.end_workout(sid)

        summary = wdb.get_workout_summary(sid)
        reps = summary["exercise_sets"][0]["reps"]
        assert len(reps) == 2
        assert reps[0]["form_quality"] == "excellent"
        assert reps[1]["form_quality"] == "good"

    def test_invalid_rep_does_not_corrupt_counters(self, wdb):
        sid = wdb.start_workout()
        set_id = wdb.add_exercise_to_workout(sid, "squat")

        # Valid rep
        wdb.log_rep(set_id, 1, "excellent", 85.0, 1.0)
        # Invalid quality — should fail
        result = wdb.log_rep(set_id, 2, "amazing", 90.0, 1.0)
        assert result is False

        # Counter should still be 1
        wdb.connection.cursor.execute(
            "SELECT total_reps FROM exercise_sets WHERE set_id = ?", (set_id,)
        )
        assert wdb.connection.cursor.fetchone()["total_reps"] == 1


# ---------------------------------------------------------------------------
# Zero-rep filtering consistency
# ---------------------------------------------------------------------------
class TestZeroRepFiltering:
    """Zero-rep sets excluded consistently across stats, history, sessions."""

    def test_zero_rep_set_excluded_from_total_stats(self, wdb):
        sid = wdb.start_workout()
        # Set with reps
        s1 = wdb.add_exercise_to_workout(sid, "squat")
        wdb.update_exercise_set(s1, {"total_reps": 5, "excellent_reps": 5})
        # Set without reps
        wdb.add_exercise_to_workout(sid, "curl")
        wdb.end_workout(sid)

        stats = wdb.get_total_stats()
        assert stats["total_all_reps"] == 5
        assert "curl" not in stats["reps_by_exercise"]

    def test_session_with_only_zero_rep_sets_not_counted(self, wdb):
        # Session 1 — real workout
        s1 = wdb.start_workout()
        set1 = wdb.add_exercise_to_workout(s1, "squat")
        wdb.update_exercise_set(set1, {"total_reps": 10, "excellent_reps": 10})
        wdb.end_workout(s1)

        # Session 2 — user started but quit immediately
        s2 = wdb.start_workout()
        wdb.add_exercise_to_workout(s2, "squat")
        wdb.end_workout(s2)

        stats = wdb.get_total_stats()
        assert stats["total_sessions"] == 1  # only session 1
        assert stats["total_all_reps"] == 10

    def test_zero_rep_set_still_in_summary(self, wdb):
        """Session summary shows ALL sets (including zero-rep) for debugging."""
        sid = wdb.start_workout()
        s1 = wdb.add_exercise_to_workout(sid, "squat")
        wdb.update_exercise_set(s1, {"total_reps": 5, "excellent_reps": 5})
        wdb.add_exercise_to_workout(sid, "curl")  # zero-rep
        wdb.end_workout(sid)

        summary = wdb.get_workout_summary(sid)
        # Summary shows both sets (it's a detailed view, no filtering)
        assert len(summary["exercise_sets"]) == 2


# ---------------------------------------------------------------------------
# Data consolidation lifecycle
# ---------------------------------------------------------------------------
class TestConsolidationLifecycle:
    """Old data → consolidate → monthly_stats → delete originals."""

    def _insert_old_workout(self, wdb, start_time, exercise, total_reps,
                            excellent=0, good=0, poor=0, duration=300):
        """Insert a workout directly with an old start_time."""
        cur = wdb.connection.cursor
        end_time = start_time  # simplify
        cur.execute("""
            INSERT INTO workout_sessions (start_time, end_time, total_duration_seconds)
            VALUES (?, ?, ?)
        """, (start_time, end_time, duration))
        sid = cur.lastrowid

        cur.execute(
            "SELECT exercise_type_id FROM exercise_types WHERE name = ?",
            (exercise,)
        )
        etype = cur.fetchone()["exercise_type_id"]

        cur.execute("""
            INSERT INTO exercise_sets
                (session_id, exercise_type_id, total_reps,
                 excellent_reps, good_reps, poor_reps)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (sid, etype, total_reps, excellent, good, poor))
        wdb.connection.commit()
        return sid

    def test_consolidation_creates_monthly_stats(self, wdb):
        self._insert_old_workout(
            wdb, "2022-03-15 10:00:00", "squat", 20,
            excellent=10, good=7, poor=3, duration=600,
        )

        result = wdb.stats.consolidate_old_data(retention_days=365)
        assert result["months_consolidated"] >= 1

        monthly = wdb.stats.get_monthly_stats(year=2022, month=3)
        assert len(monthly) == 1
        assert monthly[0]["exercise_name"] == "squat"
        assert monthly[0]["total_reps"] == 20
        assert monthly[0]["excellent_reps"] == 10

    def test_consolidation_deletes_original_data(self, wdb):
        sid = self._insert_old_workout(
            wdb, "2022-05-10 10:00:00", "curl", 15,
        )

        wdb.stats.consolidate_old_data(retention_days=365)

        # Original session should be gone
        wdb.connection.cursor.execute(
            "SELECT COUNT(*) as cnt FROM workout_sessions WHERE session_id = ?",
            (sid,)
        )
        assert wdb.connection.cursor.fetchone()["cnt"] == 0

    def test_recent_data_survives_consolidation(self, wdb):
        # Old workout — will be consolidated & deleted
        self._insert_old_workout(wdb, "2022-01-10 10:00:00", "squat", 10)

        # Recent workout — should survive
        recent_sid = wdb.start_workout()
        set_id = wdb.add_exercise_to_workout(recent_sid, "squat")
        wdb.update_exercise_set(set_id, {"total_reps": 5, "excellent_reps": 5})
        wdb.end_workout(recent_sid)

        wdb.stats.consolidate_old_data(retention_days=365)

        # Recent session still exists
        session = wdb.sessions.get_session(recent_sid)
        assert session is not None

        # Monthly stats have old data
        monthly = wdb.stats.get_monthly_stats(year=2022, month=1)
        assert len(monthly) == 1
        assert monthly[0]["total_reps"] == 10

    def test_consolidation_aggregates_multiple_sessions_per_month(self, wdb):
        self._insert_old_workout(
            wdb, "2022-06-05 10:00:00", "squat", 10,
            excellent=5, good=3, poor=2,
        )
        self._insert_old_workout(
            wdb, "2022-06-20 10:00:00", "squat", 8,
            excellent=4, good=2, poor=2,
        )

        wdb.stats.consolidate_old_data(retention_days=365)

        monthly = wdb.stats.get_monthly_stats(year=2022, month=6)
        assert len(monthly) == 1
        assert monthly[0]["total_reps"] == 18
        assert monthly[0]["excellent_reps"] == 9
        assert monthly[0]["total_sessions"] == 2


# ---------------------------------------------------------------------------
# Streak tracking across sessions
# ---------------------------------------------------------------------------
class TestStreakIntegration:
    """Streaks reflect real session data across days."""

    def _insert_session_on_date(self, wdb, date_str):
        """Insert a session with the given start_time date."""
        wdb.connection.cursor.execute(
            "INSERT INTO workout_sessions (start_time) VALUES (?)",
            (f"{date_str} 10:00:00",)
        )
        wdb.connection.commit()

    def test_streak_counts_consecutive_days(self, wdb):
        from datetime import date, timedelta
        today = date.today()
        for i in range(3):
            d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            self._insert_session_on_date(wdb, d)

        streaks = wdb.get_streaks()
        assert streaks["current_streak"] == 3
        assert streaks["longest_streak"] >= 3

    def test_streak_broken_by_gap(self, wdb):
        from datetime import date, timedelta
        today = date.today()
        # Today + yesterday
        self._insert_session_on_date(wdb, today.strftime("%Y-%m-%d"))
        self._insert_session_on_date(
            wdb, (today - timedelta(days=1)).strftime("%Y-%m-%d")
        )
        # Skip day 2, add day 3
        self._insert_session_on_date(
            wdb, (today - timedelta(days=3)).strftime("%Y-%m-%d")
        )

        streaks = wdb.get_streaks()
        assert streaks["current_streak"] == 2

    def test_no_sessions_zero_streak(self, wdb):
        streaks = wdb.get_streaks()
        assert streaks["current_streak"] == 0
        assert streaks["longest_streak"] == 0


# ---------------------------------------------------------------------------
# Foreign key integrity
# ---------------------------------------------------------------------------
class TestForeignKeyIntegrity:
    """Verify FK constraints are enforced across repos."""

    def test_exercise_set_requires_valid_session(self, wdb):
        result = wdb.add_exercise_to_workout(99999, "squat")
        assert result is None

    def test_log_rep_requires_valid_set(self, wdb):
        result = wdb.log_rep(99999, 1, "excellent", 85.0, 1.0)
        assert result is False

    def test_session_with_exercises_and_reps_all_linked(self, wdb):
        """Verify the full FK chain: session → set → rep."""
        uid = wdb.users.create_user("Alice")
        sid = wdb.start_workout(user_id=uid)
        set_id = wdb.add_exercise_to_workout(sid, "squat")
        wdb.log_rep(set_id, 1, "excellent", 85.0, 1.0)
        wdb.end_workout(sid)

        # Session → set FK
        wdb.connection.cursor.execute(
            "SELECT session_id FROM exercise_sets WHERE set_id = ?", (set_id,)
        )
        assert wdb.connection.cursor.fetchone()["session_id"] == sid

        # Set → rep FK
        wdb.connection.cursor.execute(
            "SELECT set_id FROM reps WHERE set_id = ?", (set_id,)
        )
        assert wdb.connection.cursor.fetchone()["set_id"] == set_id

        # Session → user FK
        wdb.connection.cursor.execute(
            "SELECT user_id FROM workout_sessions WHERE session_id = ?", (sid,)
        )
        assert wdb.connection.cursor.fetchone()["user_id"] == uid


# ---------------------------------------------------------------------------
# Database persistence (close + reopen)
# ---------------------------------------------------------------------------
class TestPersistence:
    """Data survives close → reopen cycle."""

    def test_data_persists_after_close_reopen(self, tmp_path):
        db_path = str(tmp_path / "persist.db")

        # First connection — write data
        db1 = WorkoutDatabase(db_path=db_path)
        uid = db1.users.create_user("Alice")
        sid = db1.start_workout(user_id=uid)
        set_id = db1.add_exercise_to_workout(sid, "squat")
        db1.update_exercise_set(set_id, {"total_reps": 10, "excellent_reps": 10})
        db1.end_workout(sid)
        db1.close()

        # Second connection — read data
        db2 = WorkoutDatabase(db_path=db_path)
        user = db2.users.get_user(uid)
        assert user["name"] == "Alice"

        stats = db2.get_total_stats()
        assert stats["total_sessions"] == 1
        assert stats["total_all_reps"] == 10
        db2.close()

    def test_seed_types_not_duplicated_on_reopen(self, tmp_path):
        db_path = str(tmp_path / "reseed.db")

        db1 = WorkoutDatabase(db_path=db_path)
        db1.close()

        db2 = WorkoutDatabase(db_path=db_path)
        db2.connection.cursor.execute(
            "SELECT COUNT(*) as cnt FROM exercise_types WHERE name = 'squat'"
        )
        assert db2.connection.cursor.fetchone()["cnt"] == 1
        db2.close()
