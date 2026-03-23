import uuid
import json
from datetime import date, datetime, timedelta


def new_id():
    return str(uuid.uuid4())


def today():
    return date.today().isoformat()


def current_week_monday():
    d = date.today()
    monday = d - timedelta(days=d.weekday())
    return monday.isoformat()


def week_range(monday_str):
    monday = date.fromisoformat(monday_str)
    sunday = monday + timedelta(days=6)
    return monday.isoformat(), sunday.isoformat()


def current_week_range():
    return week_range(current_week_monday())


def is_this_week(date_str):
    if not date_str:
        return False
    d = date.fromisoformat(date_str)
    monday = date.today() - timedelta(days=date.today().weekday())
    sunday = monday + timedelta(days=6)
    return monday <= d <= sunday


def get_default_data():
    return {
        "weekly_focuses": {
            "focus_1": "",
            "focus_2": "",
            "focus_3": "",
            "week_start": ""
        },
        "exercise": {
            "workout_plans": [],
            "logs": [],
            "custom_exercises": []
        },
        "projects": {
            "items": [],
            "goals": []
        },
        "reading": {
            "books": []
        },
        "work": {
            "tasks": [],
            "learning_log": [],
            "chartership": {
                "competencies": [
                    {"id": "comp_a", "name": "Knowledge and understanding", "progress_pct": 0, "evidence": [], "notes": ""},
                    {"id": "comp_b", "name": "Design, development and solving engineering problems", "progress_pct": 0, "evidence": [], "notes": ""},
                    {"id": "comp_c", "name": "Responsibility, management and leadership", "progress_pct": 0, "evidence": [], "notes": ""},
                    {"id": "comp_d", "name": "Communication and interpersonal skills", "progress_pct": 0, "evidence": [], "notes": ""},
                    {"id": "comp_e", "name": "Professional commitment", "progress_pct": 0, "evidence": [], "notes": ""}
                ]
            }
        },
        "custom_tiles": [],
        "tile_settings": {
            "order": ["exercise", "projects", "reading", "work"],
            "colours": {
                "exercise": "#00B4D8",
                "projects": "#FF6B35",
                "reading": "#7B2D8E",
                "work": "#00A86B"
            },
            "custom": []
        }
    }


def migrate_data(data):
    defaults = get_default_data()
    for key, value in defaults.items():
        if key not in data:
            data[key] = value
        elif isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if sub_key not in data[key]:
                    data[key][sub_key] = sub_value
    return data
