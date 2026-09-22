# Rules for any AI working on this project

This file is the rulebook. Claude Code, Codex and any other assistant with access to this
repository must follow it. It is written in plain English on purpose. If anything here is
unclear, ask the user rather than guess.

## What this project is

A private to-do list for one person. The list lives in one file, `data/tasks.json`, on the
`main` branch of this repository. A small Streamlit app (`app.py`) shows that file as a tick
list on the user's phone. The user adds and updates tasks by talking to an AI, which edits the
file and saves it to `main`. The file is also the long-term memory: nothing is ever deleted
from it, so the history of what was done and when is always there for reviews.

The only things the app itself can change are ticks (mark done, or put a done task back).
Everything else is changed by an AI following this rulebook.

## The task file

`data/tasks.json` is one object with one key, `"tasks"`, holding a list of tasks in number
order. Every task has exactly these nine fields, in this order:

| Field | Meaning |
|---|---|
| `id` | The letter T and a number, like `"T7"`. Said out loud as "task 7". Never reused or changed. |
| `title` | A short plain-English line. Change it only when the user asks to rename the task. |
| `status` | Exactly one of `"open"`, `"done"`, `"set aside"`. |
| `progress` | `null`, or a whole number 0 to 100. Only when the user gives a percentage. |
| `due` | `null` (no deadline, unlimited time), or a date like `"2026-09-25"`. |
| `summary` | One or two sentences saying where the task stands right now. The app shows this under the title. |
| `created` | When the task was added, UTC, like `"2026-09-21T21:51:16Z"`. Never changed. |
| `closed` | `null` while open. The UTC time the task was marked done or set aside. Back to `null` if reopened. |
| `notes` | A list, oldest first, of `{"at": <UTC time>, "note": <text>}`. At least one entry. Never edited or removed. |

What the statuses mean:

- `open`: still to do. It stays on the live list however old or overdue it is.
- `done`: finished.
- `set aside`: the user asked for it to be dropped or parked. It leaves the live list, stays in
  the file, and can be reopened later. Only an AI sets this, never the app.

One task, as an example:

```json
{
  "id": "T7",
  "title": "Chase the supplier about the invoice",
  "status": "open",
  "progress": null,
  "due": "2026-09-25",
  "summary": "Not started. Waiting on the revised quote first.",
  "created": "2026-09-21T21:51:16Z",
  "closed": null,
  "notes": [
    {"at": "2026-09-21T21:51:16Z", "note": "Added. Chase once the revised quote is in, due Friday."}
  ]
}
```

## The rules

1. **Only the task file changes when the user talks about tasks.** Do not touch the app or
   any other file unless the user clearly asks for a change to the app. Talking about tasks
   is never a request to change the app.
2. **Start from the newest copy.** Before editing, bring your copy of `main` up to date, then
   read the whole of `data/tasks.json`.
3. **Take the time from the clock, never from the conversation.** Run
   `date -u +%Y-%m-%dT%H:%M:%SZ` right before you write, and use that value for `created`,
   `closed` and note times. Due dates are dates only. When the user says a weekday like
   "Friday", work out the real date from today's date in UK time and say the full date back
   to them in your reply.
4. **Never delete anything.** Never remove a task or a note. Never change an `id`, a
   `created` time or an existing note. To retire a task, set its status to `"set aside"`.
   To bring it back, set the status to `"open"` and `closed` to `null`.
5. **Every change adds one note and refreshes the summary.** Append one note at the end of
   the task's list: the user's words made short and plain, one to three sentences. Then
   rewrite `summary` so it says where the task stands now, on its own.
6. **Status changes set `closed`.** Setting `"done"` or `"set aside"` sets `closed` to now.
   Setting `"open"` sets `closed` back to `null`.
7. **Percentages only when the user gives one.** If they say "40 percent", set `progress` to
   40. If they say "about half done" with no number, leave `progress` as it is and let the
   summary carry the words.
8. **A new task** gets the next number (highest existing number plus one), status `"open"`,
   `progress` `null`, `due` only if given, `created` = now, `closed` `null`, a summary of
   where it stands, and one note recording what the user said.
9. **Find tasks by number first.** "Task 3" means `T3`. Otherwise match by the meaning of the
   title. If two tasks could match, ask; do not guess.
10. **Keep the file valid and tidy.** UTF-8, two-space indent, the nine fields in order, tasks
    in number order. Run `python3 check_tasks.py` before saving and never save while it
    reports a problem. `python3 check_tasks.py --tidy` fixes layout without changing content.
11. **One saved version per request.** Commit once with a message in the form
    `tasks: <what changed>`, for example `tasks: T3 done; add T7`. Then land it on `main`
    the way your tool's section below says. Never force-push and never rewrite history.
12. **One session at a time.** Do not start a second task session while one is still
    running; wait for the reply first.
13. **If the file will not open**, do not guess a repair. Restore the last good version from
    the git history, tell the user, then apply their change on top of it.
14. **Reply in plain English** with exactly what changed: ids, titles, new statuses, due
    dates as full dates, and anything you were unsure about. No jargon.

## Landing a change on main

- **Claude Code:** see `CLAUDE.md`. In short: commit once, then `git push origin HEAD:main`.
- **Codex or another tool:** commit to `main` and push if you are allowed to; otherwise open
  a pull request and tell the user it needs one tap to merge.

`main` has no protection rules on purpose. Do not add any: they would block both the app's
ticks and the AI's saves.

## The first import, and repeating it later

The user keeps a list of objectives in ChatGPT. To bring it in:

1. The user asks ChatGPT for the list as a checklist: one line per objective, ticked if
   finished, with a one-line note on where it stands and any due date. They paste it to you.
2. Read `data/tasks.json` in full. Compare each pasted line with the existing tasks by
   meaning, not exact words.
3. Show a table with three columns before writing anything: **Added** (new tasks you will
   create), **Already there** (matched an existing task, which you will not touch), and
   **Unsure** (could be either; ask). Wait for the user to say go.
4. Create the new tasks: `created` = now, status `"open"` for unticked lines or `"done"` for
   ticked ones (with `closed` = now and a note saying the real finish date is not known),
   `summary` from the status note, `due` if given, and a first note
   `"Imported from the ChatGPT list on <date>: <the original line>"`. Sub-points under a line
   go into that task's summary, not into separate tasks.
5. Save once: `tasks: import <N> objectives from ChatGPT`.

Repeating this later adds only the gaps. Nothing already in the file is touched.

Before the very first real import, the user will ask for a one-off reset of the test tasks to
an empty list. That is the only time the file is ever emptied.

## Where things are

- `data/tasks.json`: the task file.
- `check_tasks.py`: the checker. `python3 check_tasks.py` must print OK before any save.
- `app.py`, `tasks_store.py`: the Streamlit app and how it reads and writes the file.
- `README.md`: instructions for the person using this, including setup.
- `CLAUDE.md`: this rulebook plus notes specific to Claude Code.
