# Skeleton of src/db.py: structure only. The implementation is private.
# PostgreSQL helpers (psycopg2). Each stub has a one-line description.

from typing import Optional


def persist_user_data_enabled() -> bool:
    """Feature flag PERSIST_USER_DATA_IN_DB. Off by default: no sessions or email addresses are stored."""
    ...

def _get_pool():
    """Create the connection pool from DATABASE_URL."""
    ...

def _get_conn():
    """Borrow a connection from the pool."""
    ...

def _put_conn(conn):
    """Return a connection to the pool."""
    ...

def init_db():
    """Create the tables if they do not exist."""
    ...


# ---- Sessions (only active when the flag is on) ----------------------------

def create_session(state: dict) -> str:
    """Store a new session and return its id (flag off: returns an id and stores nothing)."""
    ...

def get_session(session_id: str) -> Optional[dict]:
    """Load a session by id (flag off: always None, so the browser copy is used)."""
    ...

def update_session(session_id: str, state: dict) -> None:
    """Save session state and reset the inactivity clock (flag off: does nothing)."""
    ...

def delete_session(session_id: str) -> None:
    """Delete a session."""
    ...

def ping_session(session_id: str) -> bool:
    """Reset the inactivity clock (flag off: reports success)."""
    ...

def cleanup_expired_sessions() -> int:
    """Delete sessions inactive for more than 2 hours and return how many."""
    ...


# ---- Usage and email logging -----------------------------------------------

def log_tokens(agent: str, model: str, input_tokens: int, output_tokens: int) -> None:
    """Record token usage and estimated cost per agent call."""
    ...

def log_email(status: str = "sent", recipient: Optional[str] = None) -> None:
    """Record a send for the monthly count; the address is stored only when the flag is on."""
    ...


# ---- Admin services table --------------------------------------------------

def init_services_table(conn) -> None:
    """Create and seed the services reference table."""
    ...

def get_services() -> list:
    """List services for the admin dashboard."""
    ...

def create_service(data: dict) -> dict:
    """Add a service."""
    ...

def update_service(service_id: int, data: dict) -> bool:
    """Edit a service."""
    ...

def delete_service(service_id: int) -> bool:
    """Remove a service."""
    ...
