import json
import re
from datetime import datetime, timedelta


def safe_parse_json(text: str) -> dict | list | None:
    """Parse JSON from LLM response, handling markdown code blocks."""
    text = text.strip()
    # Remove markdown code block wrappers
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object/array in the text
        for pattern in [r'\{[\s\S]*\}', r'\[[\s\S]*\]']:
            match = re.search(pattern, text)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    continue
        return None


def format_number(n: int | float) -> str:
    """Format number with thousand separators: 1520 -> '1,520'."""
    if isinstance(n, float):
        return f"{n:,.2f}"
    return f"{n:,}"


def truncate(text: str, max_len: int = 200) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


def time_ago(dt: datetime) -> str:
    """Human-readable time difference."""
    diff = datetime.utcnow() - dt
    seconds = int(diff.total_seconds())

    if seconds < 60:
        return f"{seconds} сек. назад"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} мин. назад"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours} ч. назад"
    else:
        days = seconds // 86400
        return f"{days} дн. назад"


def format_duration(seconds: int) -> str:
    """Format seconds to human-readable duration."""
    if seconds < 60:
        return f"{seconds}с"
    elif seconds < 3600:
        return f"{seconds // 60}м {seconds % 60}с"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}ч {minutes}м"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}д {hours}ч"


def format_reactions(reactions: dict) -> str:
    """Format reactions dict to string: 👍 230 | 😂 180."""
    if not reactions:
        return "Нет реакций"
    parts = [f"{emoji} {count}" for emoji, count in reactions.items()]
    return " | ".join(parts)


DEFAULT_STRATEGY = {
    "content_mix": {
        "text_only": 0.30,
        "drake": 0.20,
        "distracted_bf": 0.10,
        "expanding_brain": 0.15,
        "two_buttons": 0.10,
        "this_is_fine": 0.15,
    },
    "posting_schedule": {
        "posts_per_day": 3,
        "best_times": ["09:00", "14:00", "20:00"],
        "avoid_times": ["02:00-06:00"],
    },
    "topic_weights": {
        "technology": 0.25,
        "daily_life": 0.25,
        "work": 0.20,
        "programming": 0.15,
        "relationships": 0.10,
        "absurd": 0.05,
    },
    "quality_thresholds": {
        "min_humor_score": 6.0,
        "min_relevance": 0.6,
        "min_originality": 0.7,
    },
}
