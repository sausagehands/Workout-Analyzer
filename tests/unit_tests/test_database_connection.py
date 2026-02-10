"""Unit tests for DatabaseConnection module.

Tests __init__, _connect, commit, and close using
Arrange-Act-Assert structure with nominal and edge cases.
"""
import os
import sqlite3
import tempfile
import threading

import pytest

from database.database_connection import DatabaseConnection


# ---------------------------------------------------------------------------
# Helper – create a temp database path that auto-cleans after the test
# ---------------------------------------------------------------------------
@pytest.fixture
def tmp_db(tmp_path):
    """Return a path to a temporary .db file inside pytest's tmp directory."""
    return str(tmp_path / "test_workouts.db")


@pytest.fixture
def db(tmp_db):
    """Yield a DatabaseConnection backed by a temp file, then close it."""
    conn = DatabaseConnection(db_path=tmp_db)
    yield conn
    # teardown – close if still open
    if conn.conn is not None:
        conn.close()


# ---------------------------------------------------------------------------
# __init__ / _connect – nominal cases
# ---------------------------------------------------------------------------
class TestConnectNominal:
    """Verify a fresh connection is properly configured."""

    def test_connection_is_established(self, db):
        # Assert
        assert db.conn is not None

    def test_cursor_is_created(self, db):
        # Assert
        assert db.cursor is not None

    def test_row_factory_is_sqlite_row(self, db):
        # Assert
        assert db.conn.row_factory is sqlite3.Row

    def test_foreign_keys_enabled(self, db):
        # Act
        db.cursor.execute("PRAGMA foreign_keys")
        result = db.cursor.fetchone()

        # Assert – PRAGMA returns 1 when ON
        assert result[0] == 1

    def test_journal_mode_is_wal(self, db):
        # Act
        db.cursor.execute("PRAGMA journal_mode")
        mode = db.cursor.fetchone()[0]

        # Assert
        assert mode.lower() == "wal"

    def test_db_path_stored(self, tmp_db):
        # Arrange / Act
        conn = DatabaseConnection(db_path=tmp_db)

        # Assert
        assert conn.db_path == tmp_db
        conn.close()

    def test_creates_file_on_disk(self, tmp_db):
        # Arrange / Act
        conn = DatabaseConnection(db_path=tmp_db)

        # Assert
        assert os.path.exists(tmp_db)
        conn.close()

    def test_connection_lock_is_rlock(self, db):
        # Assert
        assert isinstance(db.connection_lock, type(threading.RLock()))


# ---------------------------------------------------------------------------
# __init__ / _connect – edge cases
# ---------------------------------------------------------------------------
class TestConnectEdge:
    """Connection failures, bad paths, and unusual inputs."""

    def test_invalid_path_raises_error(self):
        # Arrange – path that cannot be created
        bad_path = "/nonexistent_root_dir_abc123/impossible/test.db"

        # Act / Assert
        with pytest.raises(sqlite3.OperationalError):
            DatabaseConnection(db_path=bad_path)

    def test_empty_string_path_creates_in_memory_or_raises(self):
        # Arrange – sqlite3.connect("") opens a temp on-disk db
        conn = DatabaseConnection(db_path="")

        # Assert – should still produce a usable connection
        assert conn.conn is not None
        conn.close()

    def test_in_memory_path(self):
        # Arrange / Act
        conn = DatabaseConnection(db_path=":memory:")

        # Assert
        assert conn.conn is not None
        conn.close()

    def test_two_connections_same_file_locks(self, tmp_db):
        # Arrange – first connection holds WAL lock
        conn1 = DatabaseConnection(db_path=tmp_db)

        # Act / Assert – second connection can't set WAL, raises OperationalError
        with pytest.raises(sqlite3.OperationalError, match="database is locked"):
            DatabaseConnection(db_path=tmp_db)

        conn1.close()

    def test_read_only_directory_raises(self, tmp_path):
        # Arrange – create a read-only directory
        ro_dir = tmp_path / "readonly"
        ro_dir.mkdir()
        ro_dir.chmod(0o444)
        db_path = str(ro_dir / "test.db")

        # Act / Assert
        with pytest.raises(sqlite3.OperationalError):
            DatabaseConnection(db_path=db_path)

        # Cleanup – restore permissions so pytest can remove the dir
        ro_dir.chmod(0o755)

    def test_special_characters_in_path(self, tmp_path):
        # Arrange – spaces and dashes in filename
        db_path = str(tmp_path / "my work-out (1).db")

        # Act
        conn = DatabaseConnection(db_path=db_path)

        # Assert
        assert conn.conn is not None
        assert os.path.exists(db_path)
        conn.close()


# ---------------------------------------------------------------------------
# commit – nominal cases
# ---------------------------------------------------------------------------
class TestCommitNominal:
    """Verify commit persists data."""

    def test_commit_persists_data(self, db, tmp_db):
        # Arrange – create table and insert data
        db.cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, val TEXT)")
        db.cursor.execute("INSERT INTO test (val) VALUES ('hello')")

        # Act
        db.commit()

        # Assert – open a second connection and verify data is there
        verify_conn = sqlite3.connect(tmp_db)
        row = verify_conn.execute("SELECT val FROM test").fetchone()
        assert row[0] == "hello"
        verify_conn.close()

    def test_commit_returns_none(self, db):
        # Act
        result = db.commit()

        # Assert
        assert result is None

    def test_multiple_commits(self, db, tmp_db):
        # Arrange
        db.cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, val TEXT)")

        # Act – insert and commit twice
        db.cursor.execute("INSERT INTO test (val) VALUES ('first')")
        db.commit()
        db.cursor.execute("INSERT INTO test (val) VALUES ('second')")
        db.commit()

        # Assert
        verify_conn = sqlite3.connect(tmp_db)
        rows = verify_conn.execute("SELECT val FROM test ORDER BY id").fetchall()
        assert len(rows) == 2
        assert rows[0][0] == "first"
        assert rows[1][0] == "second"
        verify_conn.close()


# ---------------------------------------------------------------------------
# commit – edge cases
# ---------------------------------------------------------------------------
class TestCommitEdge:
    """Edge cases around commit behavior."""

    def test_commit_with_no_pending_changes(self, db):
        # Act / Assert – should not raise
        db.commit()

    def test_commit_after_close_is_noop(self, db):
        # Arrange
        db.close()

        # Act / Assert – conn is None, commit should silently do nothing
        db.commit()


# ---------------------------------------------------------------------------
# close – nominal cases
# ---------------------------------------------------------------------------
class TestCloseNominal:
    """Verify close tears down connection properly."""

    def test_close_sets_conn_to_none(self, db):
        # Act
        db.close()

        # Assert
        assert db.conn is None

    def test_close_sets_cursor_to_none(self, db):
        # Act
        db.close()

        # Assert
        assert db.cursor is None

    def test_close_commits_before_closing(self, tmp_db):
        # Arrange
        db = DatabaseConnection(db_path=tmp_db)
        db.cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, val TEXT)")
        db.cursor.execute("INSERT INTO test (val) VALUES ('saved')")

        # Act – close should auto-commit
        db.close()

        # Assert – data should persist
        verify_conn = sqlite3.connect(tmp_db)
        row = verify_conn.execute("SELECT val FROM test").fetchone()
        assert row[0] == "saved"
        verify_conn.close()

    def test_close_returns_none(self, db):
        # Act
        result = db.close()

        # Assert
        assert result is None


# ---------------------------------------------------------------------------
# close – edge cases
# ---------------------------------------------------------------------------
class TestCloseEdge:
    """Edge cases for closing connections."""

    def test_double_close_does_not_raise(self, db):
        # Act – close twice
        db.close()
        db.close()

        # Assert – still None, no error
        assert db.conn is None
        assert db.cursor is None

    def test_close_after_failed_query(self, db):
        # Arrange – run a query that fails
        try:
            db.cursor.execute("SELECT * FROM nonexistent_table")
        except sqlite3.OperationalError:
            pass

        # Act / Assert – close should still work
        db.close()
        assert db.conn is None


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------
class TestThreadSafety:
    """Verify RLock protects concurrent access."""

    def test_sequential_access_across_threads(self, db):
        # Arrange – serialise access via the connection_lock
        db.cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, val TEXT)")
        db.commit()
        errors = []

        def worker(n):
            try:
                for i in range(5):
                    with db.connection_lock:
                        db.cursor.execute(
                            "INSERT INTO test (val) VALUES (?)",
                            (f"thread-{n}-{i}",),
                        )
                        db.commit()
            except Exception as e:
                errors.append(e)

        # Act – threads serialise on the lock
        threads = [threading.Thread(target=worker, args=(n,)) for n in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Assert – no errors when properly locked
        assert errors == []

        # Verify all 20 rows were inserted (4 threads x 5 inserts)
        db.cursor.execute("SELECT COUNT(*) FROM test")
        assert db.cursor.fetchone()[0] == 20

    def test_lock_is_reentrant(self, db):
        # Act – acquire the same lock twice from the same thread
        db.connection_lock.acquire()
        db.connection_lock.acquire()

        # Assert – no deadlock, release both
        db.connection_lock.release()
        db.connection_lock.release()
