"""AI-powered task categorization using Claude API."""

import anthropic
from storage import load_sessions, load_config


CATEGORIES = [
    "Deep Work",
    "Communication",
    "Planning",
    "Learning",
    "Administrative",
    "Creative",
    "Review",
    "Other",
]


def get_past_categorizations() -> str:
    """Build context from past sessions for the AI to learn from."""
    sessions = load_sessions()
    if not sessions:
        return "No past sessions yet."
    recent = sessions[-20:]
    lines = [f'- "{s["task"]}" -> {s["category"]}' for s in recent]
    return "\n".join(lines)


def categorize_task(task: str) -> str:
    """Use Claude to categorize a task based on its description and past patterns."""
    config = load_config()
    api_key = config.get("anthropic_api_key", "")
    if not api_key:
        return "Other"

    past = get_past_categorizations()
    prompt = (
        f"Categorize this pomodoro task into exactly one of these categories: "
        f"{', '.join(CATEGORIES)}.\n\n"
        f"Past categorizations for context:\n{past}\n\n"
        f'Task: "{task}"\n\n'
        f"Respond with ONLY the category name, nothing else."
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=20,
            messages=[{"role": "user", "content": prompt}],
        )
        result = message.content[0].text.strip()
        if result in CATEGORIES:
            return result
        return "Other"
    except Exception:
        return "Other"
