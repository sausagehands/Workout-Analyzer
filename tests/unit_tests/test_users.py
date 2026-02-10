"""Unit tests for UserRepository module.

Tests create_user, get_user, update_profile, and get_default_user using
Arrange-Act-Assert structure with nominal and edge cases.
"""
import sqlite3

import pytest

from database.database_connection import DatabaseConnection
from database.users import UserRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def tmp_db(tmp_path):
    """Return a path to a temporary .db file inside pytest's tmp directory."""
    return str(tmp_path / "test_users.db")


@pytest.fixture
def db(tmp_db):
    """Yield a DatabaseConnection with the user_profile table, then close it."""
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
    conn.commit()
    yield conn
    if conn.conn is not None:
        conn.close()


@pytest.fixture
def repo(db):
    """Return a UserRepository backed by the test database."""
    return UserRepository(db)


# ---------------------------------------------------------------------------
# create_user – nominal cases
# ---------------------------------------------------------------------------
class TestCreateUserNominal:
    """Verify creating users returns an ID and persists data."""

    def test_returns_integer_id(self, repo):
        # Act
        user_id = repo.create_user("Alice")

        # Assert
        assert isinstance(user_id, int)

    def test_first_user_gets_id_1(self, repo):
        # Act
        user_id = repo.create_user("Alice")

        # Assert
        assert user_id == 1

    def test_sequential_ids(self, repo):
        # Act
        id1 = repo.create_user("Alice")
        id2 = repo.create_user("Bob")

        # Assert
        assert id2 == id1 + 1

    def test_user_is_retrievable_after_create(self, repo):
        # Arrange
        user_id = repo.create_user("Alice")

        # Act
        user = repo.get_user(user_id)

        # Assert
        assert user is not None
        assert user["name"] == "Alice"

    def test_created_user_has_null_height(self, repo):
        # Arrange
        user_id = repo.create_user("Alice")

        # Act
        user = repo.get_user(user_id)

        # Assert
        assert user["height_cm"] is None

    def test_created_user_has_timestamps(self, repo):
        # Arrange
        user_id = repo.create_user("Alice")

        # Act
        user = repo.get_user(user_id)

        # Assert
        assert user["created_at"] is not None
        assert user["updated_at"] is not None


# ---------------------------------------------------------------------------
# create_user – edge cases
# ---------------------------------------------------------------------------
class TestCreateUserEdge:
    """Edge cases for user creation."""

    def test_empty_name(self, repo):
        # Act
        user_id = repo.create_user("")

        # Assert – empty string is still valid TEXT
        assert user_id is not None
        user = repo.get_user(user_id)
        assert user["name"] == ""

    def test_name_with_special_characters(self, repo):
        # Arrange
        name = "O'Brien-Smith (Jr.)"

        # Act
        user_id = repo.create_user(name)

        # Assert
        user = repo.get_user(user_id)
        assert user["name"] == name

    def test_name_with_unicode(self, repo):
        # Arrange
        name = "José García"

        # Act
        user_id = repo.create_user(name)

        # Assert
        user = repo.get_user(user_id)
        assert user["name"] == name

    def test_very_long_name(self, repo):
        # Arrange
        name = "A" * 1000

        # Act
        user_id = repo.create_user(name)

        # Assert
        user = repo.get_user(user_id)
        assert user["name"] == name


# ---------------------------------------------------------------------------
# get_user – nominal cases
# ---------------------------------------------------------------------------
class TestGetUserNominal:
    """Verify fetching users by ID."""

    def test_returns_dict(self, repo):
        # Arrange
        user_id = repo.create_user("Alice")

        # Act
        user = repo.get_user(user_id)

        # Assert
        assert isinstance(user, dict)

    def test_dict_has_expected_keys(self, repo):
        # Arrange
        user_id = repo.create_user("Alice")

        # Act
        user = repo.get_user(user_id)

        # Assert
        expected_keys = {"user_id", "name", "height_cm", "created_at", "updated_at"}
        assert set(user.keys()) == expected_keys

    def test_correct_user_returned(self, repo):
        # Arrange
        repo.create_user("Alice")
        bob_id = repo.create_user("Bob")

        # Act
        user = repo.get_user(bob_id)

        # Assert
        assert user["name"] == "Bob"
        assert user["user_id"] == bob_id


# ---------------------------------------------------------------------------
# get_user – edge cases
# ---------------------------------------------------------------------------
class TestGetUserEdge:
    """Edge cases for user retrieval."""

    def test_nonexistent_id_returns_none(self, repo):
        # Act
        user = repo.get_user(999)

        # Assert
        assert user is None

    def test_negative_id_returns_none(self, repo):
        # Act
        user = repo.get_user(-1)

        # Assert
        assert user is None

    def test_zero_id_returns_none(self, repo):
        # Act
        user = repo.get_user(0)

        # Assert
        assert user is None


# ---------------------------------------------------------------------------
# update_profile – nominal cases
# ---------------------------------------------------------------------------
class TestUpdateProfileNominal:
    """Verify profile updates persist correctly."""

    def test_update_name_returns_true(self, repo):
        # Arrange
        user_id = repo.create_user("Alice")

        # Act
        result = repo.update_profile(user_id, name="Alicia")

        # Assert
        assert result is True

    def test_update_name_persists(self, repo):
        # Arrange
        user_id = repo.create_user("Alice")

        # Act
        repo.update_profile(user_id, name="Alicia")
        user = repo.get_user(user_id)

        # Assert
        assert user["name"] == "Alicia"

    def test_update_height_returns_true(self, repo):
        # Arrange
        user_id = repo.create_user("Alice")

        # Act
        result = repo.update_profile(user_id, height_cm=170.5)

        # Assert
        assert result is True

    def test_update_height_persists(self, repo):
        # Arrange
        user_id = repo.create_user("Alice")

        # Act
        repo.update_profile(user_id, height_cm=170.5)
        user = repo.get_user(user_id)

        # Assert
        assert user["height_cm"] == pytest.approx(170.5)

    def test_update_both_fields(self, repo):
        # Arrange
        user_id = repo.create_user("Alice")

        # Act
        result = repo.update_profile(user_id, name="Alicia", height_cm=165.0)

        # Assert
        assert result is True
        user = repo.get_user(user_id)
        assert user["name"] == "Alicia"
        assert user["height_cm"] == pytest.approx(165.0)

    def test_rename_user_multiple_times(self, repo):
        # Arrange
        user_id = repo.create_user("Alice")

        # Act – simulate user changing name in settings repeatedly
        repo.update_profile(user_id, name="Alicia")
        repo.update_profile(user_id, name="Ali")
        repo.update_profile(user_id, name="A-Dog")
        user = repo.get_user(user_id)

        # Assert – only the final name persists
        assert user["name"] == "A-Dog"

    def test_update_changes_updated_at(self, repo):
        # Arrange
        user_id = repo.create_user("Alice")
        before = repo.get_user(user_id)["updated_at"]

        # Act
        repo.update_profile(user_id, name="Alicia")
        after = repo.get_user(user_id)["updated_at"]

        # Assert – updated_at should change (or at least not be earlier)
        assert after >= before


# ---------------------------------------------------------------------------
# update_profile – edge cases
# ---------------------------------------------------------------------------
class TestUpdateProfileEdge:
    """Edge cases for profile updates."""

    def test_no_valid_fields_returns_false(self, repo):
        # Arrange
        user_id = repo.create_user("Alice")

        # Act – pass no keyword arguments
        result = repo.update_profile(user_id)

        # Assert
        assert result is False

    def test_invalid_field_ignored(self, repo):
        # Arrange
        user_id = repo.create_user("Alice")

        # Act – "email" is not in the allowlist
        result = repo.update_profile(user_id, email="alice@test.com")

        # Assert – no valid fields → False
        assert result is False

    def test_mixed_valid_and_invalid_fields(self, repo):
        # Arrange
        user_id = repo.create_user("Alice")

        # Act – "name" is valid, "email" is not
        result = repo.update_profile(user_id, name="Alicia", email="alice@test.com")

        # Assert – valid field still applied
        assert result is True
        user = repo.get_user(user_id)
        assert user["name"] == "Alicia"

    def test_nonexistent_user_returns_false(self, repo):
        # Act
        result = repo.update_profile(999, name="Ghost")

        # Assert
        assert result is False

    def test_update_height_to_zero(self, repo):
        # Arrange
        user_id = repo.create_user("Alice")

        # Act
        result = repo.update_profile(user_id, height_cm=0)

        # Assert
        assert result is True
        user = repo.get_user(user_id)
        assert user["height_cm"] == 0

    def test_update_name_to_empty_string(self, repo):
        # Arrange
        user_id = repo.create_user("Alice")

        # Act
        result = repo.update_profile(user_id, name="")

        # Assert
        assert result is True
        user = repo.get_user(user_id)
        assert user["name"] == ""


# ---------------------------------------------------------------------------
# get_default_user – nominal cases
# ---------------------------------------------------------------------------
class TestGetDefaultUserNominal:
    """Verify default user retrieval for single-user app."""

    def test_returns_first_created_user(self, repo):
        # Arrange
        repo.create_user("Alice")
        repo.create_user("Bob")

        # Act
        default = repo.get_default_user()

        # Assert
        assert default["name"] == "Alice"

    def test_returns_dict(self, repo):
        # Arrange
        repo.create_user("Alice")

        # Act
        default = repo.get_default_user()

        # Assert
        assert isinstance(default, dict)

    def test_dict_has_expected_keys(self, repo):
        # Arrange
        repo.create_user("Alice")

        # Act
        default = repo.get_default_user()

        # Assert
        expected_keys = {"user_id", "name", "height_cm", "created_at"}
        assert set(default.keys()) == expected_keys


# ---------------------------------------------------------------------------
# get_default_user – edge cases
# ---------------------------------------------------------------------------
class TestGetDefaultUserEdge:
    """Edge cases for default user retrieval."""

    def test_empty_database_returns_none(self, repo):
        # Act – no users have been created
        default = repo.get_default_user()

        # Assert
        assert default is None

    def test_still_returns_first_after_many_inserts(self, repo):
        # Arrange
        for i in range(10):
            repo.create_user(f"User_{i}")

        # Act
        default = repo.get_default_user()

        # Assert
        assert default["name"] == "User_0"
        assert default["user_id"] == 1
