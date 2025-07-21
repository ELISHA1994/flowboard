"""
Unit tests for authentication utilities.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest
from jose import JWTError, jwt

from app.core.middleware.jwt_auth_backend import (ALGORITHM, SECRET_KEY,
                                                  create_access_token,
                                                  get_password_hash,
                                                  verify_password,
                                                  verify_token)


@pytest.mark.unit
class TestPasswordHashing:
    """Test cases for password hashing functions."""

    def test_get_password_hash(self):
        """Test password hashing."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        # Hash should be different from original
        assert hashed != password
        # Hash should be a non-empty string
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        # BCrypt hashes typically start with $2b$
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "correctpassword"
        hashed = get_password_hash(password)

        result = verify_password(password, hashed)
        assert result is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "correctpassword"
        hashed = get_password_hash(password)

        result = verify_password("wrongpassword", hashed)
        assert result is False

    def test_different_hashes_same_password(self):
        """Test that same password generates different hashes."""
        password = "testpassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different (due to salt)
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


@pytest.mark.unit
class TestJWTTokens:
    """Test cases for JWT token functions."""

    def test_create_access_token_basic(self):
        """Test creating access token with basic data."""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify token
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "testuser"
        assert "exp" in decoded

    def test_create_access_token_with_expires_delta(self):
        """Test creating access token with custom expiration."""
        data = {"sub": "testuser", "role": "admin"}
        expires_delta = timedelta(hours=1)

        with patch("app.core.middleware.jwt_auth_backend.datetime") as mock_datetime:
            # Mock current time
            current_time = datetime(2024, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = current_time

            token = create_access_token(data, expires_delta)

        # Decode and verify (skip expiration check since we're using a mock date)
        decoded = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False}
        )
        assert decoded["sub"] == "testuser"
        assert decoded["role"] == "admin"

        # Check expiration time
        exp_timestamp = decoded["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, timezone.utc).replace(
            tzinfo=None
        )
        expected_exp = current_time + expires_delta

        # Allow small time difference due to processing
        assert abs((exp_datetime - expected_exp).total_seconds()) < 1

    def test_create_access_token_default_expiration(self):
        """Test creating access token with default expiration."""
        data = {"sub": "testuser"}

        with patch("app.core.middleware.jwt_auth_backend.datetime") as mock_datetime:
            # Mock current time
            current_time = datetime(2024, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = current_time

            token = create_access_token(data)

        # Decode and check default expiration (15 minutes)
        decoded = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False}
        )
        exp_timestamp = decoded["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, timezone.utc).replace(
            tzinfo=None
        )
        expected_exp = current_time + timedelta(minutes=15)

        assert abs((exp_datetime - expected_exp).total_seconds()) < 1

    def test_verify_token_valid(self):
        """Test verifying a valid token."""
        # Create a valid token
        data = {"sub": "validuser"}
        token = create_access_token(data, timedelta(hours=1))

        # Verify it
        username = verify_token(token)
        assert username == "validuser"

    def test_verify_token_invalid_signature(self):
        """Test verifying token with invalid signature."""
        # Create token with different secret
        data = {"sub": "testuser"}
        fake_token = jwt.encode(data, "wrong-secret", algorithm=ALGORITHM)

        # Verification should fail
        result = verify_token(fake_token)
        assert result is None

    def test_verify_token_expired(self):
        """Test verifying an expired token."""
        # Create an already expired token
        data = {"sub": "testuser"}
        expired_token = create_access_token(data, timedelta(seconds=-1))

        # Verification should fail
        result = verify_token(expired_token)
        assert result is None

    def test_verify_token_missing_sub(self):
        """Test verifying token without 'sub' claim."""
        # Create token without 'sub'
        data = {
            "user_id": "123",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

        # Verification should fail
        result = verify_token(token)
        assert result is None

    def test_verify_token_malformed(self):
        """Test verifying a malformed token."""
        malformed_tokens = [
            "not.a.token",
            "invalid-jwt-format",
            "",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",  # Incomplete JWT
        ]

        for token in malformed_tokens:
            result = verify_token(token)
            assert result is None
