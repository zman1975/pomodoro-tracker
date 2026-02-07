"""Session data persistence for Pomodoro tracker."""

import json
import os
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
SESSIONS_FILE = DATA_DIR / "sessions.json"
CONFIG_FILE = Path(__file__).parent / "config.json"


def load_config() -> dict:
    """Load user configuration."""
    with open(CONFIG_FILE) as f:
        return json.load(f)


def save_config(config: dict) -> None:
    """Save user configuration."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)


def load_sessions() -> list[dict]:
    """Load all saved sessions."""
    if not SESSIONS_FILE.exists():
        return []
    with open(SESSIONS_FILE) as f:
        return json.load(f)


def save_session(task: str, category: str, duration_seconds: int, completed: bool) -> dict:
    """Save a pomodoro session and return the record."""
    sessions = load_sessions()
    record = {
        "id": len(sessions) + 1,
        "task": task,
        "category": category,
        "started_at": datetime.now().isoformat(),
        "duration_seconds": duration_seconds,
        "completed": completed,
    }
    sessions.append(record)
    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions, f, indent=2)
    return record


def update_session_category(session_id: int, new_category: str) -> bool:
    """Update the category of an existing session. Returns True if found and updated."""
    sessions = load_sessions()
    for session in sessions:
        if session["id"] == session_id:
            session["category"] = new_category
            with open(SESSIONS_FILE, "w") as f:
                json.dump(sessions, f, indent=2)
            return True
    return False
