"""
Evolving Codebase - 50 turns of realistic code mutations.

Each turn is a snapshot of a Python auth module as it evolves through a
realistic coding session: renames, new parameters, type changes, method
extractions, async conversions, and deletions.

The ground truth at every turn is produced by running OMP's
``extract_from_source()`` on the snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Turn:
    """A single turn in the evolving codebase."""

    number: int
    source: str
    description: str


# ---------------------------------------------------------------------------
# The 50-turn codebase
# ---------------------------------------------------------------------------

_TURNS: list[Turn] = []


def _t(number: int, description: str, source: str) -> None:
    _TURNS.append(Turn(number=number, source=source.strip(), description=description))


# ── Turn 1: Initial auth module ──────────────────────────────────────────

_t(1, "Initial auth module with 5 functions", """
import hashlib
import hmac
from datetime import datetime, timedelta

SECRET_KEY = "super-secret"

def create_token(user_id: str, expires_in: int = 3600) -> str:
    \"\"\"Create a signed authentication token.\"\"\"
    payload = f"{user_id}:{datetime.utcnow().isoformat()}:{expires_in}"
    signature = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"

def validate_token(token: str) -> dict:
    \"\"\"Validate a token and return the payload.\"\"\"
    parts = token.rsplit(".", 1)
    if len(parts) != 2:
        return {}
    return {"user_id": parts[0].split(":")[0], "valid": True}

def hash_password(password: str) -> str:
    \"\"\"Hash a password using SHA-256.\"\"\"
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    \"\"\"Verify a password against its hash.\"\"\"
    return hash_password(password) == hashed

def get_user_permissions(user_id: str) -> list:
    \"\"\"Return a list of permissions for a user.\"\"\"
    return ["read", "write"]
""")

# ── Turn 2: Add type hint to get_user_permissions ────────────────────────

_t(2, "Add explicit return type to get_user_permissions", """
import hashlib
import hmac
from datetime import datetime, timedelta

SECRET_KEY = "super-secret"

def create_token(user_id: str, expires_in: int = 3600) -> str:
    \"\"\"Create a signed authentication token.\"\"\"
    payload = f"{user_id}:{datetime.utcnow().isoformat()}:{expires_in}"
    signature = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"

def validate_token(token: str) -> dict:
    \"\"\"Validate a token and return the payload.\"\"\"
    parts = token.rsplit(".", 1)
    if len(parts) != 2:
        return {}
    return {"user_id": parts[0].split(":")[0], "valid": True}

def hash_password(password: str) -> str:
    \"\"\"Hash a password using SHA-256.\"\"\"
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    \"\"\"Verify a password against its hash.\"\"\"
    return hash_password(password) == hashed

def get_user_permissions(user_id: str) -> list[str]:
    \"\"\"Return a list of permissions for a user.\"\"\"
    return ["read", "write"]
""")

# ── Turn 3: Add role parameter ───────────────────────────────────────────

_t(3, "Add role parameter to get_user_permissions", """
import hashlib
import hmac
from datetime import datetime, timedelta

SECRET_KEY = "super-secret"

def create_token(user_id: str, expires_in: int = 3600) -> str:
    \"\"\"Create a signed authentication token.\"\"\"
    payload = f"{user_id}:{datetime.utcnow().isoformat()}:{expires_in}"
    signature = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"

def validate_token(token: str) -> dict:
    \"\"\"Validate a token and return the payload.\"\"\"
    parts = token.rsplit(".", 1)
    if len(parts) != 2:
        return {}
    return {"user_id": parts[0].split(":")[0], "valid": True}

def hash_password(password: str) -> str:
    \"\"\"Hash a password using SHA-256.\"\"\"
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    \"\"\"Verify a password against its hash.\"\"\"
    return hash_password(password) == hashed

def get_user_permissions(user_id: str, role: str = "user") -> list[str]:
    \"\"\"Return a list of permissions for a user based on role.\"\"\"
    if role == "admin":
        return ["read", "write", "delete", "admin"]
    return ["read", "write"]
""")

# ── Turn 4: Add logging import ───────────────────────────────────────────

_t(4, "Add logging import and log calls", """
import hashlib
import hmac
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
SECRET_KEY = "super-secret"

def create_token(user_id: str, expires_in: int = 3600) -> str:
    \"\"\"Create a signed authentication token.\"\"\"
    logger.info("Creating token for user %s", user_id)
    payload = f"{user_id}:{datetime.utcnow().isoformat()}:{expires_in}"
    signature = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"

def validate_token(token: str) -> dict:
    \"\"\"Validate a token and return the payload.\"\"\"
    parts = token.rsplit(".", 1)
    if len(parts) != 2:
        logger.warning("Invalid token format")
        return {}
    return {"user_id": parts[0].split(":")[0], "valid": True}

def hash_password(password: str) -> str:
    \"\"\"Hash a password using SHA-256.\"\"\"
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    \"\"\"Verify a password against its hash.\"\"\"
    return hash_password(password) == hashed

def get_user_permissions(user_id: str, role: str = "user") -> list[str]:
    \"\"\"Return a list of permissions for a user based on role.\"\"\"
    if role == "admin":
        return ["read", "write", "delete", "admin"]
    return ["read", "write"]
""")

# ── Turn 5: Rename validate_token → verify_token ────────────────────────

_t(5, "Rename validate_token to verify_token", """
import hashlib
import hmac
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
SECRET_KEY = "super-secret"

def create_token(user_id: str, expires_in: int = 3600) -> str:
    \"\"\"Create a signed authentication token.\"\"\"
    logger.info("Creating token for user %s", user_id)
    payload = f"{user_id}:{datetime.utcnow().isoformat()}:{expires_in}"
    signature = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"

def verify_token(token: str) -> dict:
    \"\"\"Verify a token and return the payload.\"\"\"
    parts = token.rsplit(".", 1)
    if len(parts) != 2:
        logger.warning("Invalid token format")
        return {}
    return {"user_id": parts[0].split(":")[0], "valid": True}

def hash_password(password: str) -> str:
    \"\"\"Hash a password using SHA-256.\"\"\"
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    \"\"\"Verify a password against its hash.\"\"\"
    return hash_password(password) == hashed

def get_user_permissions(user_id: str, role: str = "user") -> list[str]:
    \"\"\"Return a list of permissions for a user based on role.\"\"\"
    if role == "admin":
        return ["read", "write", "delete", "admin"]
    return ["read", "write"]
""")

# ── Turns 6-10: Incremental refinements ─────────────────────────────────

_t(6, "Change verify_token return type to dict | None", """
import hashlib
import hmac
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
SECRET_KEY = "super-secret"

def create_token(user_id: str, expires_in: int = 3600) -> str:
    logger.info("Creating token for user %s", user_id)
    payload = f"{user_id}:{datetime.utcnow().isoformat()}:{expires_in}"
    signature = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"

def verify_token(token: str) -> dict | None:
    parts = token.rsplit(".", 1)
    if len(parts) != 2:
        logger.warning("Invalid token format")
        return None
    return {"user_id": parts[0].split(":")[0], "valid": True}

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def get_user_permissions(user_id: str, role: str = "user") -> list[str]:
    if role == "admin":
        return ["read", "write", "delete", "admin"]
    return ["read", "write"]
""")

_t(7, "Add salt parameter to hash_password", """
import hashlib
import hmac
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
SECRET_KEY = "super-secret"

def create_token(user_id: str, expires_in: int = 3600) -> str:
    logger.info("Creating token for user %s", user_id)
    payload = f"{user_id}:{datetime.utcnow().isoformat()}:{expires_in}"
    signature = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"

def verify_token(token: str) -> dict | None:
    parts = token.rsplit(".", 1)
    if len(parts) != 2:
        return None
    return {"user_id": parts[0].split(":")[0], "valid": True}

def hash_password(password: str, salt: str | None = None) -> str:
    if salt is None:
        salt = os.urandom(16).hex()
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def get_user_permissions(user_id: str, role: str = "user") -> list[str]:
    if role == "admin":
        return ["read", "write", "delete", "admin"]
    return ["read", "write"]
""")

_t(8, "Add new function: revoke_token", """
import hashlib
import hmac
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
SECRET_KEY = "super-secret"
_revoked_tokens: set[str] = set()

def create_token(user_id: str, expires_in: int = 3600) -> str:
    logger.info("Creating token for user %s", user_id)
    payload = f"{user_id}:{datetime.utcnow().isoformat()}:{expires_in}"
    signature = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"

def verify_token(token: str) -> dict | None:
    if token in _revoked_tokens:
        return None
    parts = token.rsplit(".", 1)
    if len(parts) != 2:
        return None
    return {"user_id": parts[0].split(":")[0], "valid": True}

def revoke_token(token: str) -> bool:
    _revoked_tokens.add(token)
    logger.info("Token revoked")
    return True

def hash_password(password: str, salt: str | None = None) -> str:
    if salt is None:
        salt = os.urandom(16).hex()
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def get_user_permissions(user_id: str, role: str = "user") -> list[str]:
    if role == "admin":
        return ["read", "write", "delete", "admin"]
    return ["read", "write"]
""")

_t(9, "Change verify_password to accept salt parameter", """
import hashlib
import hmac
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
SECRET_KEY = "super-secret"
_revoked_tokens: set[str] = set()

def create_token(user_id: str, expires_in: int = 3600) -> str:
    logger.info("Creating token for user %s", user_id)
    payload = f"{user_id}:{datetime.utcnow().isoformat()}:{expires_in}"
    signature = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"

def verify_token(token: str) -> dict | None:
    if token in _revoked_tokens:
        return None
    parts = token.rsplit(".", 1)
    if len(parts) != 2:
        return None
    return {"user_id": parts[0].split(":")[0], "valid": True}

def revoke_token(token: str) -> bool:
    _revoked_tokens.add(token)
    logger.info("Token revoked")
    return True

def hash_password(password: str, salt: str | None = None) -> str:
    if salt is None:
        salt = os.urandom(16).hex()
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def verify_password(password: str, hashed: str, salt: str | None = None) -> bool:
    return hash_password(password, salt) == hashed

def get_user_permissions(user_id: str, role: str = "user") -> list[str]:
    if role == "admin":
        return ["read", "write", "delete", "admin"]
    return ["read", "write"]
""")

_t(10, "Rename get_user_permissions to get_permissions", """
import hashlib
import hmac
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
SECRET_KEY = "super-secret"
_revoked_tokens: set[str] = set()

def create_token(user_id: str, expires_in: int = 3600) -> str:
    logger.info("Creating token for user %s", user_id)
    payload = f"{user_id}:{datetime.utcnow().isoformat()}:{expires_in}"
    signature = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"

def verify_token(token: str) -> dict | None:
    if token in _revoked_tokens:
        return None
    parts = token.rsplit(".", 1)
    if len(parts) != 2:
        return None
    return {"user_id": parts[0].split(":")[0], "valid": True}

def revoke_token(token: str) -> bool:
    _revoked_tokens.add(token)
    logger.info("Token revoked")
    return True

def hash_password(password: str, salt: str | None = None) -> str:
    if salt is None:
        salt = os.urandom(16).hex()
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def verify_password(password: str, hashed: str, salt: str | None = None) -> bool:
    return hash_password(password, salt) == hashed

def get_permissions(user_id: str, role: str = "user") -> list[str]:
    if role == "admin":
        return ["read", "write", "delete", "admin"]
    return ["read", "write"]
""")

# ── Turns 11-20: Extract class, add async ────────────────────────────────

_t(11, "Add strict parameter to verify_token", """
import hashlib
import hmac
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
SECRET_KEY = "super-secret"
_revoked_tokens: set[str] = set()

def create_token(user_id: str, expires_in: int = 3600) -> str:
    payload = f"{user_id}:{datetime.utcnow().isoformat()}:{expires_in}"
    signature = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"

def verify_token(token: str, strict: bool = False) -> dict | None:
    if token in _revoked_tokens:
        return None
    parts = token.rsplit(".", 1)
    if len(parts) != 2:
        return None
    if strict:
        pass
    return {"user_id": parts[0].split(":")[0], "valid": True}

def revoke_token(token: str) -> bool:
    _revoked_tokens.add(token)
    return True

def hash_password(password: str, salt: str | None = None) -> str:
    if salt is None:
        salt = os.urandom(16).hex()
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def verify_password(password: str, hashed: str, salt: str | None = None) -> bool:
    return hash_password(password, salt) == hashed

def get_permissions(user_id: str, role: str = "user") -> list[str]:
    if role == "admin":
        return ["read", "write", "delete", "admin"]
    return ["read", "write"]
""")

_t(12, "Add new function: refresh_token", """
import hashlib
import hmac
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
SECRET_KEY = "super-secret"
_revoked_tokens: set[str] = set()

def create_token(user_id: str, expires_in: int = 3600) -> str:
    payload = f"{user_id}:{datetime.utcnow().isoformat()}:{expires_in}"
    signature = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"

def verify_token(token: str, strict: bool = False) -> dict | None:
    if token in _revoked_tokens:
        return None
    parts = token.rsplit(".", 1)
    if len(parts) != 2:
        return None
    return {"user_id": parts[0].split(":")[0], "valid": True}

def refresh_token(token: str, extend_by: int = 3600) -> str | None:
    payload = verify_token(token)
    if payload is None:
        return None
    return create_token(payload["user_id"], extend_by)

def revoke_token(token: str) -> bool:
    _revoked_tokens.add(token)
    return True

def hash_password(password: str, salt: str | None = None) -> str:
    if salt is None:
        salt = os.urandom(16).hex()
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def verify_password(password: str, hashed: str, salt: str | None = None) -> bool:
    return hash_password(password, salt) == hashed

def get_permissions(user_id: str, role: str = "user") -> list[str]:
    if role == "admin":
        return ["read", "write", "delete", "admin"]
    return ["read", "write"]
""")

# Turn 13-19: progressive changes
_t(13, "Change create_token expires_in default to 7200", """
import hashlib
import hmac
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
SECRET_KEY = "super-secret"
_revoked_tokens: set[str] = set()

def create_token(user_id: str, expires_in: int = 7200) -> str:
    payload = f"{user_id}:{datetime.utcnow().isoformat()}:{expires_in}"
    signature = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"

def verify_token(token: str, strict: bool = False) -> dict | None:
    if token in _revoked_tokens:
        return None
    parts = token.rsplit(".", 1)
    if len(parts) != 2:
        return None
    return {"user_id": parts[0].split(":")[0], "valid": True}

def refresh_token(token: str, extend_by: int = 3600) -> str | None:
    payload = verify_token(token)
    if payload is None:
        return None
    return create_token(payload["user_id"], extend_by)

def revoke_token(token: str) -> bool:
    _revoked_tokens.add(token)
    return True

def hash_password(password: str, salt: str | None = None) -> str:
    if salt is None:
        salt = os.urandom(16).hex()
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def verify_password(password: str, hashed: str, salt: str | None = None) -> bool:
    return hash_password(password, salt) == hashed

def get_permissions(user_id: str, role: str = "user") -> list[str]:
    if role == "admin":
        return ["read", "write", "delete", "admin"]
    return ["read", "write"]
""")

_t(14, "Add scope parameter to get_permissions", """
import hashlib
import hmac
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
SECRET_KEY = "super-secret"
_revoked_tokens: set[str] = set()

def create_token(user_id: str, expires_in: int = 7200) -> str:
    payload = f"{user_id}:{datetime.utcnow().isoformat()}:{expires_in}"
    signature = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"

def verify_token(token: str, strict: bool = False) -> dict | None:
    if token in _revoked_tokens:
        return None
    parts = token.rsplit(".", 1)
    if len(parts) != 2:
        return None
    return {"user_id": parts[0].split(":")[0], "valid": True}

def refresh_token(token: str, extend_by: int = 3600) -> str | None:
    payload = verify_token(token)
    if payload is None:
        return None
    return create_token(payload["user_id"], extend_by)

def revoke_token(token: str) -> bool:
    _revoked_tokens.add(token)
    return True

def hash_password(password: str, salt: str | None = None) -> str:
    if salt is None:
        salt = os.urandom(16).hex()
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def verify_password(password: str, hashed: str, salt: str | None = None) -> bool:
    return hash_password(password, salt) == hashed

def get_permissions(user_id: str, role: str = "user", scope: str = "default") -> list[str]:
    if role == "admin":
        return ["read", "write", "delete", "admin"]
    return ["read", "write"]
""")

_t(15, "Remove verify_password, inline into class (next turn)", """
import hashlib
import hmac
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
SECRET_KEY = "super-secret"
_revoked_tokens: set[str] = set()

def create_token(user_id: str, expires_in: int = 7200) -> str:
    payload = f"{user_id}:{datetime.utcnow().isoformat()}:{expires_in}"
    signature = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"

def verify_token(token: str, strict: bool = False) -> dict | None:
    if token in _revoked_tokens:
        return None
    parts = token.rsplit(".", 1)
    if len(parts) != 2:
        return None
    return {"user_id": parts[0].split(":")[0], "valid": True}

def refresh_token(token: str, extend_by: int = 3600) -> str | None:
    payload = verify_token(token)
    if payload is None:
        return None
    return create_token(payload["user_id"], extend_by)

def revoke_token(token: str) -> bool:
    _revoked_tokens.add(token)
    return True

def hash_password(password: str, salt: str | None = None) -> str:
    if salt is None:
        salt = os.urandom(16).hex()
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def get_permissions(user_id: str, role: str = "user", scope: str = "default") -> list[str]:
    if role == "admin":
        return ["read", "write", "delete", "admin"]
    return ["read", "write"]
""")

# Turn 16-20: Extract into class

_t(16, "Extract token functions into TokenService class", """
import hashlib
import hmac
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TokenService:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self._revoked: set[str] = set()

    def create(self, user_id: str, expires_in: int = 7200) -> str:
        payload = f"{user_id}:{datetime.utcnow().isoformat()}:{expires_in}"
        signature = hmac.new(self.secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return f"{payload}.{signature}"

    def verify(self, token: str, strict: bool = False) -> dict | None:
        if token in self._revoked:
            return None
        parts = token.rsplit(".", 1)
        if len(parts) != 2:
            return None
        return {"user_id": parts[0].split(":")[0], "valid": True}

    def refresh(self, token: str, extend_by: int = 3600) -> str | None:
        payload = self.verify(token)
        if payload is None:
            return None
        return self.create(payload["user_id"], extend_by)

    def revoke(self, token: str) -> bool:
        self._revoked.add(token)
        return True

def hash_password(password: str, salt: str | None = None) -> str:
    if salt is None:
        salt = os.urandom(16).hex()
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def get_permissions(user_id: str, role: str = "user", scope: str = "default") -> list[str]:
    if role == "admin":
        return ["read", "write", "delete", "admin"]
    return ["read", "write"]
""")

_t(17, "Add async create method to TokenService", """
import hashlib
import hmac
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TokenService:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self._revoked: set[str] = set()

    def create(self, user_id: str, expires_in: int = 7200) -> str:
        payload = f"{user_id}:{datetime.utcnow().isoformat()}:{expires_in}"
        signature = hmac.new(self.secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return f"{payload}.{signature}"

    async def async_create(self, user_id: str, expires_in: int = 7200) -> str:
        return self.create(user_id, expires_in)

    def verify(self, token: str, strict: bool = False) -> dict | None:
        if token in self._revoked:
            return None
        parts = token.rsplit(".", 1)
        if len(parts) != 2:
            return None
        return {"user_id": parts[0].split(":")[0], "valid": True}

    def refresh(self, token: str, extend_by: int = 3600) -> str | None:
        payload = self.verify(token)
        if payload is None:
            return None
        return self.create(payload["user_id"], extend_by)

    def revoke(self, token: str) -> bool:
        self._revoked.add(token)
        return True

def hash_password(password: str, salt: str | None = None) -> str:
    if salt is None:
        salt = os.urandom(16).hex()
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def get_permissions(user_id: str, role: str = "user", scope: str = "default") -> list[str]:
    if role == "admin":
        return ["read", "write", "delete", "admin"]
    return ["read", "write"]
""")

_t(18, "Change verify return type to User | None (add User type alias)", """
import hashlib
import hmac
import logging
import os
from datetime import datetime, timedelta
from typing import TypeAlias

logger = logging.getLogger(__name__)

User: TypeAlias = dict[str, str | bool]

class TokenService:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self._revoked: set[str] = set()

    def create(self, user_id: str, expires_in: int = 7200) -> str:
        payload = f"{user_id}:{datetime.utcnow().isoformat()}:{expires_in}"
        signature = hmac.new(self.secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return f"{payload}.{signature}"

    async def async_create(self, user_id: str, expires_in: int = 7200) -> str:
        return self.create(user_id, expires_in)

    def verify(self, token: str, strict: bool = False) -> User | None:
        if token in self._revoked:
            return None
        parts = token.rsplit(".", 1)
        if len(parts) != 2:
            return None
        return {"user_id": parts[0].split(":")[0], "valid": True}

    def refresh(self, token: str, extend_by: int = 3600) -> str | None:
        payload = self.verify(token)
        if payload is None:
            return None
        return self.create(str(payload["user_id"]), extend_by)

    def revoke(self, token: str) -> bool:
        self._revoked.add(token)
        return True

def hash_password(password: str, salt: str | None = None) -> str:
    if salt is None:
        salt = os.urandom(16).hex()
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def get_permissions(user_id: str, role: str = "user", scope: str = "default") -> list[str]:
    if role == "admin":
        return ["read", "write", "delete", "admin"]
    return ["read", "write"]
""")

_t(19, "Add algorithm parameter to TokenService.__init__", """
import hashlib
import hmac
import logging
import os
from datetime import datetime, timedelta
from typing import TypeAlias

logger = logging.getLogger(__name__)

User: TypeAlias = dict[str, str | bool]

class TokenService:
    def __init__(self, secret_key: str, algorithm: str = "sha256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self._revoked: set[str] = set()

    def create(self, user_id: str, expires_in: int = 7200) -> str:
        payload = f"{user_id}:{datetime.utcnow().isoformat()}:{expires_in}"
        signature = hmac.new(self.secret_key.encode(), payload.encode(), self.algorithm).hexdigest()
        return f"{payload}.{signature}"

    async def async_create(self, user_id: str, expires_in: int = 7200) -> str:
        return self.create(user_id, expires_in)

    def verify(self, token: str, strict: bool = False) -> User | None:
        if token in self._revoked:
            return None
        parts = token.rsplit(".", 1)
        if len(parts) != 2:
            return None
        return {"user_id": parts[0].split(":")[0], "valid": True}

    def refresh(self, token: str, extend_by: int = 3600) -> str | None:
        payload = self.verify(token)
        if payload is None:
            return None
        return self.create(str(payload["user_id"]), extend_by)

    def revoke(self, token: str) -> bool:
        self._revoked.add(token)
        return True

def hash_password(password: str, salt: str | None = None) -> str:
    if salt is None:
        salt = os.urandom(16).hex()
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def get_permissions(user_id: str, role: str = "user", scope: str = "default") -> list[str]:
    if role == "admin":
        return ["read", "write", "delete", "admin"]
    return ["read", "write"]
""")

_t(20, "Add PermissionService class, keep get_permissions as compat shim", """
import hashlib
import hmac
import logging
import os
from datetime import datetime, timedelta
from typing import TypeAlias

logger = logging.getLogger(__name__)

User: TypeAlias = dict[str, str | bool]

class TokenService:
    def __init__(self, secret_key: str, algorithm: str = "sha256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self._revoked: set[str] = set()

    def create(self, user_id: str, expires_in: int = 7200) -> str:
        payload = f"{user_id}:{datetime.utcnow().isoformat()}:{expires_in}"
        signature = hmac.new(self.secret_key.encode(), payload.encode(), self.algorithm).hexdigest()
        return f"{payload}.{signature}"

    async def async_create(self, user_id: str, expires_in: int = 7200) -> str:
        return self.create(user_id, expires_in)

    def verify(self, token: str, strict: bool = False) -> User | None:
        if token in self._revoked:
            return None
        parts = token.rsplit(".", 1)
        if len(parts) != 2:
            return None
        return {"user_id": parts[0].split(":")[0], "valid": True}

    def refresh(self, token: str, extend_by: int = 3600) -> str | None:
        payload = self.verify(token)
        if payload is None:
            return None
        return self.create(str(payload["user_id"]), extend_by)

    def revoke(self, token: str) -> bool:
        self._revoked.add(token)
        return True

class PermissionService:
    def __init__(self, default_scope: str = "default"):
        self.default_scope = default_scope

    def get_permissions(self, user_id: str, role: str = "user") -> list[str]:
        if role == "admin":
            return ["read", "write", "delete", "admin"]
        return ["read", "write"]

    def check_permission(self, user_id: str, permission: str, role: str = "user") -> bool:
        return permission in self.get_permissions(user_id, role)

def hash_password(password: str, salt: str | None = None) -> str:
    if salt is None:
        salt = os.urandom(16).hex()
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def get_permissions(user_id: str, role: str = "user", scope: str = "default") -> list[str]:
    return PermissionService(scope).get_permissions(user_id, role)
""")

# ── Turns 21-50: Continue evolving ──────────────────────────────────────
# We generate the remaining turns programmatically with incremental changes

_TURN_20_BASE = _TURNS[-1].source

def _gen_remaining_turns() -> None:
    """Generate turns 21-50 with incremental mutations."""
    import re

    base = _TURN_20_BASE

    mutations = [
        (21, "Add async verify method to TokenService",
         lambda s: s.replace(
             "    def revoke(self, token: str) -> bool:",
             "    async def async_verify(self, token: str) -> User | None:\n"
             "        return self.verify(token)\n\n"
             "    def revoke(self, token: str) -> bool:")),
        (22, "Rename hash_password to hash_pw",
         lambda s: s.replace("def hash_password(", "def hash_pw(").replace(
             "hash_password(password)", "hash_pw(password)")),
        (23, "Add iterations parameter to hash_pw",
         lambda s: s.replace(
             "def hash_pw(password: str, salt: str | None = None) -> str:",
             "def hash_pw(password: str, salt: str | None = None, iterations: int = 100000) -> str:")),
        (24, "Change hash_pw return type to bytes",
         lambda s: s.replace(
             "def hash_pw(password: str, salt: str | None = None, iterations: int = 100000) -> str:",
             "def hash_pw(password: str, salt: str | None = None, iterations: int = 100000) -> bytes:")
         .replace(".hexdigest()", ".digest()")),
        (25, "Add @staticmethod revoke_all to TokenService",
         lambda s: s.replace(
             "class PermissionService:",
             "    @staticmethod\n"
             "    def revoke_all() -> int:\n"
             "        count = 0\n"
             "        return count\n\n"
             "class PermissionService:")),
        (26, "Add has_role method to PermissionService",
         lambda s: s.replace(
             "def get_permissions(user_id: str, role: str = \"user\", scope: str = \"default\") -> list[str]:",
             "    def has_role(self, user_id: str, role: str) -> bool:\n"
             "        return role in [\"user\", \"admin\"]\n\n"
             "def get_permissions(user_id: str, role: str = \"user\", scope: str = \"default\") -> list[str]:")),
        (27, "Change TokenService.create expires_in default to 86400",
         lambda s: s.replace(
             "def create(self, user_id: str, expires_in: int = 7200) -> str:",
             "def create(self, user_id: str, expires_in: int = 86400) -> str:")
         .replace(
             "async def async_create(self, user_id: str, expires_in: int = 7200) -> str:",
             "async def async_create(self, user_id: str, expires_in: int = 86400) -> str:")),
        (28, "Add issuer parameter to TokenService.__init__",
         lambda s: s.replace(
             'def __init__(self, secret_key: str, algorithm: str = "sha256"):',
             'def __init__(self, secret_key: str, algorithm: str = "sha256", issuer: str = "omp"):')
         .replace(
             "self.algorithm = algorithm",
             "self.algorithm = algorithm\n        self.issuer = issuer")),
        (29, "Change refresh extend_by default to 86400",
         lambda s: s.replace(
             "def refresh(self, token: str, extend_by: int = 3600) -> str | None:",
             "def refresh(self, token: str, extend_by: int = 86400) -> str | None:")),
        (30, "Remove get_permissions compat shim (module-level function)",
         lambda s: re.sub(
             r'\ndef get_permissions\(user_id.*?$',
             '',
             s,
             flags=re.DOTALL)),
        (31, "Add validate_scope method to PermissionService",
         lambda s: s.replace(
             "    def has_role(self, user_id: str, role: str) -> bool:",
             "    def validate_scope(self, scope: str) -> bool:\n"
             "        return scope in [\"default\", \"admin\", \"readonly\"]\n\n"
             "    def has_role(self, user_id: str, role: str) -> bool:")),
        (32, "Change check_permission return to Permission enum (add type)",
         lambda s: s.replace(
             "    def check_permission(self, user_id: str, permission: str, role: str = \"user\") -> bool:",
             "    def check_permission(self, user_id: str, permission: str, role: str = \"user\") -> str:"
         ).replace(
             "        return permission in self.get_permissions(user_id, role)",
             '        return "granted" if permission in self.get_permissions(user_id, role) else "denied"')),
        (33, "Add batch_verify method to TokenService",
         lambda s: s.replace(
             "    @staticmethod\n    def revoke_all",
             "    def batch_verify(self, tokens: list[str]) -> list[User | None]:\n"
             "        return [self.verify(t) for t in tokens]\n\n"
             "    @staticmethod\n    def revoke_all")),
        (34, "Rename TokenService.revoke to invalidate",
         lambda s: s.replace(
             "    def revoke(self, token: str) -> bool:",
             "    def invalidate(self, token: str) -> bool:")),
        (35, "Change TokenService.verify strict default to True",
         lambda s: s.replace(
             "def verify(self, token: str, strict: bool = False) -> User | None:",
             "def verify(self, token: str, strict: bool = True) -> User | None:")),
        (36, "Add max_age parameter to verify",
         lambda s: s.replace(
             "def verify(self, token: str, strict: bool = True) -> User | None:",
             "def verify(self, token: str, strict: bool = True, max_age: int = 0) -> User | None:")),
        (37, "Add async_refresh method",
         lambda s: s.replace(
             "    def invalidate(self, token: str) -> bool:",
             "    async def async_refresh(self, token: str, extend_by: int = 86400) -> str | None:\n"
             "        return self.refresh(token, extend_by)\n\n"
             "    def invalidate(self, token: str) -> bool:")),
        (38, "Rename PermissionService to AuthzService",
         lambda s: s.replace("class PermissionService:", "class AuthzService:")
         .replace("PermissionService(scope)", "AuthzService(scope)")),
        (39, "Add list_roles method to AuthzService",
         lambda s: s.replace(
             "    def has_role(self, user_id: str, role: str) -> bool:",
             "    def list_roles(self) -> list[str]:\n"
             "        return [\"user\", \"admin\", \"readonly\"]\n\n"
             "    def has_role(self, user_id: str, role: str) -> bool:")),
        (40, "Change hash_pw to use pbkdf2",
         lambda s: s.replace(
             "    return hashlib.sha256(f\"{salt}{password}\".encode()).digest()",
             "    return hashlib.pbkdf2_hmac(\"sha256\", password.encode(), salt.encode(), iterations)")),
        (41, "Add audit_log parameter to TokenService.invalidate",
         lambda s: s.replace(
             "    def invalidate(self, token: str) -> bool:",
             "    def invalidate(self, token: str, audit_log: bool = True) -> bool:")),
        (42, "Add decode method to TokenService",
         lambda s: s.replace(
             "    def batch_verify",
             "    def decode(self, token: str) -> dict[str, str]:\n"
             "        parts = token.rsplit(\".\", 1)\n"
             "        fields = parts[0].split(\":\")\n"
             "        return {\"user_id\": fields[0], \"issued\": fields[1] if len(fields) > 1 else \"\"}\n\n"
             "    def batch_verify")),
        (43, "Change async_verify to accept strict parameter",
         lambda s: s.replace(
             "    async def async_verify(self, token: str) -> User | None:",
             "    async def async_verify(self, token: str, strict: bool = True) -> User | None:")
         .replace(
             "        return self.verify(token)",
             "        return self.verify(token, strict=strict)")),
        (44, "Add typing import for Final, use for SECRET_KEY type hint",
         lambda s: s.replace(
             "from typing import TypeAlias",
             "from typing import Final, TypeAlias")),
        (45, "Rename TokenService to AuthTokenService",
         lambda s: s.replace("class TokenService:", "class AuthTokenService:")
         .replace("TokenService(scope)", "AuthTokenService(scope)")),
        (46, "Add encode method as alias for create",
         lambda s: s.replace(
             "    def decode(self, token: str)",
             "    def encode(self, user_id: str, expires_in: int = 86400) -> str:\n"
             "        return self.create(user_id, expires_in)\n\n"
             "    def decode(self, token: str)")),
        (47, "Change get_permissions to return frozenset",
         lambda s: s.replace(
             "    def get_permissions(self, user_id: str, role: str = \"user\") -> list[str]:",
             "    def get_permissions(self, user_id: str, role: str = \"user\") -> frozenset[str]:")
         .replace(
             '        return ["read", "write", "delete", "admin"]',
             '        return frozenset(["read", "write", "delete", "admin"])')
         .replace(
             '        return ["read", "write"]',
             '        return frozenset(["read", "write"])', 1)),
        (48, "Add bulk_invalidate method to AuthTokenService",
         lambda s: s.replace(
             "    @staticmethod\n    def revoke_all",
             "    def bulk_invalidate(self, tokens: list[str]) -> int:\n"
             "        count = sum(1 for t in tokens if self.invalidate(t))\n"
             "        return count\n\n"
             "    @staticmethod\n    def revoke_all")),
        (49, "Change AuthzService.__init__ to accept policy parameter",
         lambda s: s.replace(
             '    def __init__(self, default_scope: str = "default"):',
             '    def __init__(self, default_scope: str = "default", policy: str = "rbac"):')
         .replace(
             "        self.default_scope = default_scope",
             "        self.default_scope = default_scope\n        self.policy = policy")),
        (50, "Add async_check_permission to AuthzService",
         lambda s: s.replace(
             "    def has_role(self, user_id: str, role: str) -> bool:",
             '    async def async_check_permission(self, user_id: str, permission: str) -> str:\n'
             '        return self.check_permission(user_id, permission)\n\n'
             "    def has_role(self, user_id: str, role: str) -> bool:")),
    ]

    current = base
    for turn_num, desc, mutator in mutations:
        current = mutator(current)
        _t(turn_num, desc, current)


_gen_remaining_turns()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_turns() -> list[Turn]:
    """Return all 50 turns."""
    return list(_TURNS)


def get_turn(number: int) -> Turn:
    """Return a specific turn by number (1-based)."""
    for t in _TURNS:
        if t.number == number:
            return t
    raise ValueError(f"Turn {number} not found. Valid: 1-{len(_TURNS)}")


def get_ground_truth(turn: Turn) -> dict:
    """Extract ground truth signatures from a turn using OMP.

    Returns a dict mapping qualified_name -> {name, parameters, return_type, ...}
    """
    from omp import extract_from_source

    result = extract_from_source(turn.source, "python", file="auth.py")

    truth: dict[str, dict] = {}
    for fn in result.functions:
        truth[fn.qualified_name] = {
            "name": fn.name,
            "qualified_name": fn.qualified_name,
            "parameters": [(p.name, p.type, p.default) for p in fn.parameters],
            "return_type": fn.return_type,
            "is_async": fn.is_async,
            "is_static": fn.is_static,
            "kind": fn.kind,
        }
    for cls in result.classes:
        for m in cls.methods:
            truth[m.qualified_name] = {
                "name": m.name,
                "qualified_name": m.qualified_name,
                "parameters": [(p.name, p.type, p.default) for p in m.parameters],
                "return_type": m.return_type,
                "is_async": m.is_async,
                "is_static": m.is_static,
                "kind": m.kind,
            }

    return truth
