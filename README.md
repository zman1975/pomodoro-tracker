# Pomodoro Tracker

A focus timer with AI-powered task categorization. Available as both a terminal CLI and a desktop GUI.

## Features

- **25-minute focus timer** with automatic short/long break cycling
- **AI categorization** — Claude automatically categorizes tasks (Deep Work, Learning, Creative, etc.)
- **Session history** — tracks all completed and stopped sessions
- **Statistics** — summary of focus time by category
- **Two interfaces** — Rich terminal TUI or tkinter desktop GUI

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `config.json`:

```json
{
    "pomodoro_minutes": 25,
    "short_break_minutes": 5,
    "long_break_minutes": 15,
    "sessions_before_long_break": 4,
    "anthropic_api_key": "your-api-key-here"
}
```

## Usage

### CLI

```bash
# Start a focus session
python pomodoro.py start "Write unit tests"

# Start with a manual category and custom duration
python pomodoro.py start "Team standup" -c Communication -m 15

# View session history
python pomodoro.py history

# View stats
python pomodoro.py stats

# Update config
python pomodoro.py config pomodoro_minutes 30
```

### Desktop GUI

```bash
python pomodoro.py gui
```

Enter a task, pick a category (or leave on "Auto-detect"), and click Start. The timer auto-transitions to a break when the focus session completes.

## Project Structure

```
pomodoro.py     — CLI entry point (Click commands)
gui.py          — Desktop GUI (tkinter)
timer.py        — Countdown timer with Rich TUI display
categorizer.py  — AI task categorization via Claude API
storage.py      — JSON-based session and config persistence
config.json     — User settings and API key
data/           — Session history (auto-created)
```
