# stats.py
import sqlite3
from datetime import datetime, timedelta, date
from typing import Dict, Any, List


class StatsRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_total_stats(self) -> Dict[str, Any]:
        """Get all-time statistics across all workouts"""
        default = {
            'total_sessions': 0,
            'total_time_seconds': 0,
            'total_all_reps': 0,
            'total_excellent_reps': 0,
            'total_good_reps': 0,
            'total_poor_reps': 0,
            'reps_by_exercise': {}
        }

        with self.conn.connection_lock:
            try:
                stats = dict(default)

                # Query 1 — Session stats (only sessions with reps)
                self.conn.cursor.execute("""
                    SELECT
                        COUNT(*) AS total_sessions,
                        COALESCE(SUM(total_duration_seconds), 0) AS total_time_seconds
                    FROM workout_sessions
                    WHERE session_id IN (
                        SELECT DISTINCT session_id
                        FROM exercise_sets
                        WHERE total_reps > 0
                    )
                """)
                row = self.conn.cursor.fetchone()
                if row:
                    stats['total_sessions'] = row['total_sessions']
                    stats['total_time_seconds'] = row['total_time_seconds']

                # Query 2 — Rep totals & quality breakdown
                self.conn.cursor.execute("""
                    SELECT
                        COALESCE(SUM(es.total_reps), 0) AS total_all_reps,
                        COALESCE(SUM(es.excellent_reps), 0) AS total_excellent_reps,
                        COALESCE(SUM(es.good_reps), 0) AS total_good_reps,
                        COALESCE(SUM(es.poor_reps), 0) AS total_poor_reps
                    FROM exercise_sets es
                    WHERE es.total_reps > 0
                """)
                row = self.conn.cursor.fetchone()
                if row:
                    stats['total_all_reps'] = row['total_all_reps']
                    stats['total_excellent_reps'] = row['total_excellent_reps']
                    stats['total_good_reps'] = row['total_good_reps']
                    stats['total_poor_reps'] = row['total_poor_reps']

                # Query 3 — Per-exercise rep totals (dynamic)
                self.conn.cursor.execute("""
                    SELECT et.name, COALESCE(SUM(es.total_reps), 0) as total_reps
                    FROM exercise_sets es
                    JOIN exercise_types et ON es.exercise_type_id = et.exercise_type_id
                    WHERE es.total_reps > 0
                    GROUP BY et.name
                """)
                stats['reps_by_exercise'] = {
                    row['name']: row['total_reps']
                    for row in self.conn.cursor.fetchall()
                }

                return stats
            except sqlite3.Error as e:
                print(f"Error getting total stats: {e}")
                return default

    def get_streak_data(self) -> Dict[str, int]:
        """Calculate workout streak information"""
        with self.conn.connection_lock:
            try:
                self.conn.cursor.execute("""
                    SELECT DATE(ws.start_time) as workout_date
                    FROM workout_sessions ws
                    WHERE ws.start_time IS NOT NULL
                      AND ws.session_id IN (
                          SELECT DISTINCT session_id
                          FROM exercise_sets
                          WHERE total_reps > 0
                      )
                    GROUP BY DATE(ws.start_time)
                    ORDER BY workout_date DESC
                """)

                rows = self.conn.cursor.fetchall()
                dates = [row['workout_date'] for row in rows]

                if not dates:
                    return {'current_streak': 0, 'longest_streak': 0}

                # Calculate current streak
                current_streak = 0
                today = date.today()

                for i, date_str in enumerate(dates):
                    try:
                        workout_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        expected_date = today - timedelta(days=i)

                        if workout_date == expected_date:
                            current_streak += 1
                        else:
                            break
                    except ValueError:
                        continue  # Skip invalid dates

                # Calculate longest streak
                longest_streak = 1
                current_run = 1

                for i in range(1, len(dates)):
                    try:
                        prev_date = datetime.strptime(dates[i-1], '%Y-%m-%d').date()
                        curr_date = datetime.strptime(dates[i], '%Y-%m-%d').date()

                        if (prev_date - curr_date).days == 1:
                            current_run += 1
                            longest_streak = max(longest_streak, current_run)
                        else:
                            current_run = 1
                    except ValueError:
                        current_run = 1  # Reset on invalid date

                return {
                    'current_streak': current_streak,
                    'longest_streak': longest_streak
                }
            except sqlite3.Error as e:
                print(f"Error getting streak data: {e}")
                return {'current_streak': 0, 'longest_streak': 0}

    # def get_exercise_progress(self, exercise_name: str, days_back: int = 30) -> List[Dict[str, Any]]:
    #     """Get progress for a specific exercise over time"""
    #     with self.conn.connection_lock:
    #         try:
    #             self.conn.cursor.execute("""
    #                 SELECT
    #                     DATE(ws.start_time) as workout_date,
    #                     COUNT(DISTINCT es.set_id) as total_sets,
    #                     AVG(es.average_angle) as avg_angle,
    #                     AVG(es.min_angle) as avg_min_angle,
    #                     AVG(es.max_angle) as avg_max_angle,
    #                     SUM(es.total_reps) as total_reps,
    #                     SUM(es.excellent_reps) as excellent_reps,
    #                     SUM(es.good_reps) as good_reps,
    #                     SUM(es.poor_reps) as poor_reps,
    #                     AVG(es.duration_seconds) as avg_set_duration
    #                 FROM exercise_sets es
    #                 JOIN workout_sessions ws ON es.session_id = ws.session_id
    #                 JOIN exercise_types et ON es.exercise_type_id = et.exercise_type_id
    #                 WHERE et.name = ?
    #                   AND ws.start_time >= DATE('now', ?)
    #                 GROUP BY DATE(ws.start_time)
    #                 ORDER BY workout_date
    #             """, (exercise_name, f'-{days_back} days'))

    #             rows = self.conn.cursor.fetchall()
    #             return [dict(row) for row in rows]
    #         except sqlite3.Error as e:
    #             print(f"Error getting exercise progress: {e}")
    #             return []

    # def get_weekly_summary(self) -> Dict[str, Any]:
    #     """Get summary of the past week's workouts"""
    #     with self.conn.connection_lock:
    #         try:
    #             self.conn.cursor.execute("""
    #                 SELECT
    #                     DATE(ws.start_time) as workout_date,
    #                     COUNT(DISTINCT ws.session_id) as sessions,
    #                     COUNT(DISTINCT es.set_id) as total_sets,
    #                     COALESCE(SUM(es.total_reps), 0) as total_reps,
    #                     CASE
    #                         WHEN COALESCE(SUM(es.total_reps), 0) > 0
    #                         THEN ROUND(100.0 * COALESCE(SUM(es.excellent_reps), 0) / SUM(es.total_reps), 1)
    #                         ELSE 0.0
    #                     END as excellent_percentage
    #                 FROM workout_sessions ws
    #                 LEFT JOIN exercise_sets es ON ws.session_id = es.session_id
    #                 WHERE ws.start_time >= DATE('now', '-7 days')
    #                 GROUP BY DATE(ws.start_time)
    #                 ORDER BY workout_date DESC
    #             """)

    #             rows = self.conn.cursor.fetchall()
    #             daily_data = [dict(row) for row in rows]

    #             # Calculate weekly totals (handle None values)
    #             total_sessions = sum(day['sessions'] or 0 for day in daily_data)
    #             total_sets = sum(day['total_sets'] or 0 for day in daily_data)
    #             total_reps = sum(day['total_reps'] or 0 for day in daily_data)

    #             return {
    #                 'daily_data': daily_data,
    #                 'weekly_totals': {
    #                     'total_sessions': total_sessions,
    #                     'total_sets': total_sets,
    #                     'total_reps': total_reps,
    #                     'days_worked_out': len(daily_data)
    #                 }
    #             }
    #         except sqlite3.Error as e:
    #             print(f"Error getting weekly summary: {e}")
    #             return {'daily_data': [], 'weekly_totals': {}}

    def consolidate_old_data(self, retention_days: int = 365) -> Dict[str, Any]:
        """
        Consolidate data older than retention_days into monthly_stats and delete daily records.

        Data retention policy:
        - Keep daily data for retention_days (default 1 year)
        - After retention_days, consolidate to monthly summaries
        - Delete original daily data after consolidation

        Returns dict with consolidation results.
        """
        cutoff_date = (date.today() - timedelta(days=retention_days)).strftime('%Y-%m-%d')
        results = {
            'months_consolidated': 0,
            'sessions_deleted': 0,
            'sets_deleted': 0,
            'reps_deleted': 0,
            'errors': []
        }

        with self.conn.connection_lock:
            try:
                # Find all months with data older than cutoff that haven't been consolidated
                self.conn.cursor.execute("""
                    SELECT DISTINCT
                        strftime('%Y', ws.start_time) as year,
                        strftime('%m', ws.start_time) as month
                    FROM workout_sessions ws
                    WHERE DATE(ws.start_time) < ?
                    ORDER BY year, month
                """, (cutoff_date,))

                months_to_consolidate = self.conn.cursor.fetchall()

                for row in months_to_consolidate:
                    year = int(row['year'])
                    month = int(row['month'])

                    # Consolidate this month's data by exercise type
                    success = self._consolidate_month(year, month)
                    if success:
                        results['months_consolidated'] += 1
                    else:
                        results['errors'].append(f"Failed to consolidate {year}-{month:02d}")

                # Delete old data after successful consolidation
                if results['months_consolidated'] > 0:
                    delete_results = self._delete_old_data(cutoff_date)
                    results.update(delete_results)

                self.conn.commit()
                return results

            except sqlite3.Error as e:
                print(f"Error consolidating data: {e}")
                self.conn.rollback()
                results['errors'].append(str(e))
                return results

    def _consolidate_month(self, year: int, month: int) -> bool:
        """Consolidate a single month's data into monthly_stats"""
        try:
            # Get aggregated stats for this month by exercise type
            # Duration uses a subquery to avoid double-counting when
            # a session has multiple sets of the same exercise type.
            self.conn.cursor.execute("""
                SELECT
                    es.exercise_type_id,
                    COUNT(DISTINCT ws.session_id) as total_sessions,
                    COALESCE(SUM(es.total_reps), 0) as total_reps,
                    COALESCE(SUM(es.excellent_reps), 0) as excellent_reps,
                    COALESCE(SUM(es.good_reps), 0) as good_reps,
                    COALESCE(SUM(es.poor_reps), 0) as poor_reps,
                    COALESCE((
                        SELECT SUM(ws2.total_duration_seconds)
                        FROM workout_sessions ws2
                        WHERE ws2.session_id IN (
                            SELECT DISTINCT es2.session_id
                            FROM exercise_sets es2
                            WHERE es2.exercise_type_id = es.exercise_type_id
                              AND es2.total_reps > 0
                        )
                        AND strftime('%Y', ws2.start_time) = ?
                        AND strftime('%m', ws2.start_time) = ?
                    ), 0) as total_duration_seconds,
                    COALESCE(
                        SUM(es.average_angle * es.total_reps) / NULLIF(SUM(es.total_reps), 0),
                    0) as average_angle
                FROM exercise_sets es
                JOIN workout_sessions ws ON es.session_id = ws.session_id
                WHERE strftime('%Y', ws.start_time) = ?
                  AND strftime('%m', ws.start_time) = ?
                  AND es.total_reps > 0
                GROUP BY es.exercise_type_id
            """, (str(year), f'{month:02d}', str(year), f'{month:02d}'))

            rows = self.conn.cursor.fetchall()

            for row in rows:
                # Insert or update monthly stats (upsert)
                self.conn.cursor.execute("""
                    INSERT INTO monthly_stats
                        (year, month, exercise_type_id, total_sessions, total_reps,
                         excellent_reps, good_reps, poor_reps, total_duration_seconds, average_angle)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(year, month, exercise_type_id) DO UPDATE SET
                        total_sessions = excluded.total_sessions,
                        total_reps = excluded.total_reps,
                        excellent_reps = excluded.excellent_reps,
                        good_reps = excluded.good_reps,
                        poor_reps = excluded.poor_reps,
                        total_duration_seconds = excluded.total_duration_seconds,
                        average_angle = excluded.average_angle
                """, (
                    year, month, row['exercise_type_id'],
                    row['total_sessions'], row['total_reps'],
                    row['excellent_reps'], row['good_reps'], row['poor_reps'],
                    row['total_duration_seconds'], row['average_angle']
                ))

            return True

        except sqlite3.Error as e:
            print(f"Error consolidating month {year}-{month:02d}: {e}")
            return False

    def _delete_old_data(self, cutoff_date: str) -> Dict[str, int]:
        """Delete daily data older than cutoff date"""
        results = {'sessions_deleted': 0, 'sets_deleted': 0, 'reps_deleted': 0}

        try:
            # Get session IDs to delete
            self.conn.cursor.execute("""
                SELECT session_id FROM workout_sessions
                WHERE DATE(start_time) < ?
            """, (cutoff_date,))
            session_ids = [row['session_id'] for row in self.conn.cursor.fetchall()]

            if not session_ids:
                return results

            # Delete reps (cascade from sets)
            self.conn.cursor.execute("""
                DELETE FROM reps WHERE set_id IN (
                    SELECT set_id FROM exercise_sets WHERE session_id IN ({})
                )
            """.format(','.join('?' * len(session_ids))), session_ids)
            results['reps_deleted'] = self.conn.cursor.rowcount

            # Delete exercise sets
            self.conn.cursor.execute("""
                DELETE FROM exercise_sets WHERE session_id IN ({})
            """.format(','.join('?' * len(session_ids))), session_ids)
            results['sets_deleted'] = self.conn.cursor.rowcount

            # Delete sessions
            self.conn.cursor.execute("""
                DELETE FROM workout_sessions WHERE session_id IN ({})
            """.format(','.join('?' * len(session_ids))), session_ids)
            results['sessions_deleted'] = self.conn.cursor.rowcount

            return results

        except sqlite3.Error as e:
            print(f"Error deleting old data: {e}")
            return results

    def get_monthly_stats(self, year: int = None, month: int = None) -> List[Dict[str, Any]]:
        """Get consolidated monthly stats, optionally filtered by year/month"""
        with self.conn.connection_lock:
            try:
                if year and month:
                    self.conn.cursor.execute("""
                        SELECT ms.*, et.name as exercise_name
                        FROM monthly_stats ms
                        JOIN exercise_types et ON ms.exercise_type_id = et.exercise_type_id
                        WHERE ms.year = ? AND ms.month = ?
                        ORDER BY ms.year DESC, ms.month DESC
                    """, (year, month))
                elif year:
                    self.conn.cursor.execute("""
                        SELECT ms.*, et.name as exercise_name
                        FROM monthly_stats ms
                        JOIN exercise_types et ON ms.exercise_type_id = et.exercise_type_id
                        WHERE ms.year = ?
                        ORDER BY ms.month DESC
                    """, (year,))
                else:
                    self.conn.cursor.execute("""
                        SELECT ms.*, et.name as exercise_name
                        FROM monthly_stats ms
                        JOIN exercise_types et ON ms.exercise_type_id = et.exercise_type_id
                        ORDER BY ms.year DESC, ms.month DESC
                    """)

                return [dict(row) for row in self.conn.cursor.fetchall()]

            except sqlite3.Error as e:
                print(f"Error getting monthly stats: {e}")
                return []
