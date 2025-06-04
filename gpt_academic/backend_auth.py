from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Add se-backend to Python path
BACKEND_PATH = Path(__file__).resolve().parents[1] / "se-backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

try:
    from login.db import get_db_connection
    from login.auth import verify_token as _verify_token
except Exception as exc:  # pragma: no cover - import failure only occurs if deps missing
    raise RuntimeError(f"Failed to import backend DB module: {exc}")


def verify_user_credentials(useremail: str, password: str) -> bool:
    """Return True if the given credentials match a student or teacher."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            for table in ("student", "teacher"):
                cur.execute(f"SELECT password FROM {table} WHERE useremail=%s", (useremail,))
                row: Any | None = cur.fetchone()
                if row and row.get("password") == password:
                    return True
    except Exception:
        return False
    finally:
        conn.close()
    return False


def verify_user_token(useremail: str, token: str, role: str | None = None) -> bool:
    """Return True if the given token is valid for the user."""
    try:
        return _verify_token(useremail, token, role) is not None
    except Exception:
        return False
