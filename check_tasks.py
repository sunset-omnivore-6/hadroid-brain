#!/usr/bin/env python3
"""Checks the task file (data/tasks.json) against the rules in AGENTS.md.

How to use it:
  python3 check_tasks.py           check the file and compare it with the last saved version
  python3 check_tasks.py --tidy    put the file into the standard layout (same content), then check it
  python3 check_tasks.py --hook    used automatically by Claude Code before a save

It prints OK, or plain sentences saying what is wrong.
Exit code 0 means OK. Exit code 1 means something is wrong (2 in hook mode, which blocks the save).
The app uses the same checks when it reads the file, so a file that passes here will display.
"""
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone

TASKS_PATH = "data/tasks.json"
FIELDS = ["id", "title", "status", "progress", "due", "tags", "summary", "created", "closed", "notes"]
STATUSES = ["open", "done", "set aside"]
ID_RE = re.compile(r"^T[1-9][0-9]*$")
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CLOCK_SLACK = timedelta(minutes=10)  # how far in the future a time may be before we call it a wrong clock


# ---------- small helpers ----------

def parse_timestamp(value):
    """Turns '2026-09-21T21:51:16Z' into a datetime, or returns None if it is not in that form."""
    if not isinstance(value, str) or not TIMESTAMP_RE.match(value):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def parse_date(value):
    """Turns '2026-09-25' into a date, or returns None if it is not in that form."""
    if not isinstance(value, str) or not DATE_RE.match(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def id_number(task_id):
    return int(task_id[1:])


def dump(data):
    """Writes the task list in the standard layout: fields in order, tasks in number order, two-space indent."""
    tasks = []
    for task in data["tasks"]:
        tidy_task = {field: task.get(field) for field in FIELDS}
        tidy_task["tags"] = tidy_task["tags"] or []
        tidy_task["notes"] = [{"at": n.get("at"), "note": n.get("note")} for n in (task.get("notes") or [])]
        tasks.append(tidy_task)
    tasks.sort(key=lambda t: id_number(t["id"]) if isinstance(t["id"], str) and ID_RE.match(t["id"]) else 10**9)
    return json.dumps({"tasks": tasks}, indent=2, ensure_ascii=False) + "\n"


# ---------- the checks ----------

def check_text(text, now=None):
    """Checks one version of the file.

    Returns (data, errors, warnings). data is None when the file cannot be read at all.
    errors are plain sentences; an empty list means the file is fine.
    """
    now = now or datetime.now(timezone.utc)
    latest_allowed = now + CLOCK_SLACK
    errors, warnings = [], []

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return None, [f"The file is not valid JSON: {e.msg} at line {e.lineno}, column {e.colno}."], []

    if not isinstance(data, dict) or list(data.keys()) != ["tasks"]:
        return None, ['The file must be one object with a single key called "tasks".'], []
    tasks = data["tasks"]
    if not isinstance(tasks, list):
        return None, ['"tasks" must be a list of tasks.'], []

    seen_ids = set()
    last_number = 0
    open_titles = {}

    for position, task in enumerate(tasks, start=1):
        if isinstance(task, dict) and isinstance(task.get("id"), str) and task["id"]:
            where = f"Task {task['id']}"
        else:
            where = f"Task number {position} in the list"

        if not isinstance(task, dict):
            errors.append(f"{where}: must be an object with the ten fields {', '.join(FIELDS)}.")
            continue

        keys = list(task.keys())
        missing = [f for f in FIELDS if f not in keys]
        extra = [k for k in keys if k not in FIELDS]
        if missing:
            errors.append(f"{where}: missing field(s): {', '.join(missing)}.")
        if extra:
            errors.append(f"{where}: unexpected field(s): {', '.join(extra)}. Only the ten fields are allowed.")
        if not missing and not extra and keys != FIELDS:
            errors.append(f"{where}: the fields are in the wrong order. The order is {', '.join(FIELDS)}.")
        if missing or extra:
            continue

        # id
        task_id = task["id"]
        if not isinstance(task_id, str) or not ID_RE.match(task_id):
            errors.append(f'{where}: the id must be the letter T followed by a number, like "T7".')
            continue
        if task_id in seen_ids:
            errors.append(f"{where}: this id is used twice. Ids are never reused.")
        seen_ids.add(task_id)
        if id_number(task_id) <= last_number:
            errors.append(f"{where}: tasks must be listed in number order (T1, T2, T3 ...).")
        last_number = max(last_number, id_number(task_id))

        # title
        if not isinstance(task["title"], str) or not task["title"].strip():
            errors.append(f"{where}: the title must be a short line of text, not empty.")

        # status
        status = task["status"]
        if status not in STATUSES:
            errors.append(f"{where}: the status is {status!r}; it must be one of: open, done, set aside.")

        # progress
        progress = task["progress"]
        if progress is not None and (isinstance(progress, bool) or not isinstance(progress, int) or not 0 <= progress <= 100):
            errors.append(f"{where}: progress must be blank (null) or a whole number from 0 to 100.")

        # due
        if task["due"] is not None and parse_date(task["due"]) is None:
            errors.append(f'{where}: due must be blank (null) or a date written like "2026-09-25".')

        # tags
        tags = task["tags"]
        if not isinstance(tags, list) or any(not isinstance(x, str) or not x.strip() for x in tags):
            errors.append(f"{where}: tags must be a list of short words, like [\"research\", \"admin\"]. It may be empty.")
        else:
            if any(x != x.strip().lower() for x in tags):
                errors.append(f"{where}: tags are written in lower case with no spaces around them.")
            if len(set(tags)) != len(tags):
                errors.append(f"{where}: the same tag appears twice.")

        # summary
        if not isinstance(task["summary"], str) or not task["summary"].strip():
            errors.append(f"{where}: the summary must say in a sentence where the task stands.")

        # created
        created = parse_timestamp(task["created"])
        if created is None:
            errors.append(f'{where}: created must be a UTC time written like "2026-09-21T21:51:16Z".')
        elif created > latest_allowed:
            errors.append(f"{where}: created is in the future ({task['created']}). Check the clock: take the time from `date -u`, never from the conversation.")

        # closed
        closed_value = task["closed"]
        if status == "open":
            if closed_value is not None:
                errors.append(f"{where}: an open task must have closed set to blank (null).")
        elif status in STATUSES:
            closed = parse_timestamp(closed_value)
            if closed is None:
                errors.append(f'{where}: a task that is {status} must have closed set to the UTC time it was {status}, like "2026-09-21T21:51:16Z".')
            else:
                if created is not None and closed < created:
                    errors.append(f"{where}: closed is earlier than created.")
                if closed > latest_allowed:
                    errors.append(f"{where}: closed is in the future ({closed_value}). Check the clock.")

        # notes
        notes = task["notes"]
        if not isinstance(notes, list) or not notes:
            errors.append(f"{where}: notes must be a list with at least one entry.")
        else:
            previous = None
            for n_pos, note in enumerate(notes, start=1):
                if not isinstance(note, dict) or list(note.keys()) != ["at", "note"]:
                    errors.append(f'{where}: note {n_pos} must have exactly two fields, "at" and "note", in that order.')
                    continue
                at = parse_timestamp(note["at"])
                if at is None:
                    errors.append(f'{where}: note {n_pos} has a bad time; it must be written like "2026-09-21T21:51:16Z".')
                else:
                    if previous is not None and at < previous:
                        errors.append(f"{where}: note {n_pos} is earlier than the note before it. Notes go oldest first.")
                    if at > latest_allowed:
                        errors.append(f"{where}: note {n_pos} is in the future ({note['at']}). Check the clock.")
                    previous = at
                if not isinstance(note["note"], str) or not note["note"].strip():
                    errors.append(f"{where}: note {n_pos} has no text.")
            first_at = notes[0].get("at") if isinstance(notes[0], dict) else None
            if created is not None and first_at != task["created"]:
                errors.append(f"{where}: the first note's time must be the same as created.")

        # gentle warning: two live tasks with the same title
        if status == "open" and isinstance(task["title"], str):
            key = re.sub(r"\s+", " ", task["title"]).strip().lower()
            if key in open_titles:
                warnings.append(f"{where} has the same title as {open_titles[key]}. Fine if they really are two tasks; otherwise one may be a duplicate.")
            else:
                open_titles[key] = task_id

    return data, errors, warnings


def check_history(old_text, new_text):
    """Compares the new version with the previous one. Nothing may disappear."""
    errors = []
    try:
        old = json.loads(old_text)
        new = json.loads(new_text)
        old_tasks = {t["id"]: t for t in old["tasks"] if isinstance(t, dict) and isinstance(t.get("id"), str)}
        new_tasks = {t["id"]: t for t in new["tasks"] if isinstance(t, dict) and isinstance(t.get("id"), str)}
    except (ValueError, KeyError, TypeError):
        return errors  # one of the versions cannot be read; check_text reports that

    for task_id, old_task in old_tasks.items():
        new_task = new_tasks.get(task_id)
        if new_task is None:
            errors.append(f"Task {task_id} has been removed. Tasks are never deleted; set its status to \"set aside\" instead.")
            continue
        if new_task.get("created") != old_task.get("created"):
            errors.append(f"Task {task_id}: created has been changed. It is never changed after the task is added.")
        old_notes = old_task.get("notes") or []
        new_notes = new_task.get("notes") or []
        if new_notes[:len(old_notes)] != old_notes:
            errors.append(f"Task {task_id}: an earlier note was changed or removed. Notes are never edited; add a new note at the end instead.")
    return errors


# ---------- running it ----------

def git_head_text(path):
    """The version of the file in the last saved commit, or None if there is none."""
    try:
        result = subprocess.run(["git", "show", f"HEAD:{path}"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout if result.returncode == 0 else None


def run_checks(path, tidy=False):
    """Returns (ok, lines). lines are the sentences to print."""
    if not os.path.exists(path):
        return False, [f"There is no file at {path}."]
    with open(path, encoding="utf-8") as f:
        text = f.read()

    if tidy:
        data, errors, _ = check_text(text)
        if data is not None:
            tidied = dump(data)
            if tidied != text:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(tidied)
                text = tidied

    data, errors, warnings = check_text(text)
    previous = git_head_text(path)
    if data is not None and previous is not None:
        errors += check_history(previous, text)

    lines = []
    if errors:
        lines.append(f"{len(errors)} problem(s) in {path}:")
        lines += [f"  - {e}" for e in errors]
    for w in warnings:
        lines.append(f"  (warning) {w}")
    if not errors:
        count = len(data["tasks"])
        lines.append(f"OK: {path} is valid ({count} task{'s' if count != 1 else ''}).")
    return not errors, lines


def hook_mode():
    """Claude Code runs this before certain tool calls. It only checks when a save is about to happen."""
    try:
        call = json.load(sys.stdin)
    except ValueError:
        return 0
    tool = call.get("tool_name", "")
    relevant = False
    if tool == "Bash":
        command = str(call.get("tool_input", {}).get("command", ""))
        relevant = re.search(r"\bgit\s+(commit|push)\b", command) is not None
    elif tool.startswith("mcp__github__"):
        relevant = True
    if not relevant or not os.path.exists(TASKS_PATH):
        return 0
    ok, lines = run_checks(TASKS_PATH)
    if ok:
        return 0
    sys.stderr.write("Save blocked: the task file fails its checks. Fix these first, then run `python3 check_tasks.py` until it says OK.\n")
    sys.stderr.write("\n".join(lines) + "\n")
    return 2


def main(argv):
    if "--hook" in argv:
        return hook_mode()
    path = next((a for a in argv if not a.startswith("--")), TASKS_PATH)
    ok, lines = run_checks(path, tidy="--tidy" in argv)
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
