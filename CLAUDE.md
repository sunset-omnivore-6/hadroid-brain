@AGENTS.md

# Notes for Claude Code

These add to the rulebook above; they do not replace it.

## Before you edit the task file

```
git fetch origin main
git reset --hard origin/main
```

Run this at the start of a task session, before touching `data/tasks.json`, so you start from
the newest copy. Then read the whole file.

## The exact time

Run `date -u +%Y-%m-%dT%H:%M:%SZ` immediately before writing and use that value. Do not reuse
a time from earlier in the session and never take a time from the conversation.

For due dates the user gives as a weekday, work out the date from today's date in UK time
(`TZ=Europe/London date +%A\ %d\ %B\ %Y`) and say the full date back in your reply.

## Landing a change on main

Tested from a cloud session on 22 September 2026: a plain push to `main` works.

```
python3 check_tasks.py          # must print OK
git add data/tasks.json
git commit -m "tasks: <what changed>"
git push origin HEAD:main
```

Then push your own session branch too (`git push -u origin <your branch>`), so the session's
diff view matches what is on `main`.

If the push to `main` is rejected because `main` moved while you were working: do not merge
by hand and never resolve conflict markers inside `data/tasks.json`. Instead run
`git fetch origin main && git reset --hard origin/main`, apply your change again on the fresh
copy, run the checker, commit and push again.

## The automatic check

`.claude/settings.json` runs `check_tasks.py` before any `git commit`, `git push` or GitHub
write tool. If the file fails its checks the save is refused and the reasons are shown. Fix
the file, run `python3 check_tasks.py` until it prints OK, then save again. Never work around
the check.

## Code changes

Changes to the app or the rules go in their own commits, never mixed with a task change.
Prefix those messages with `app:` or `docs:`. A message about tasks is never a request to
change the app.
