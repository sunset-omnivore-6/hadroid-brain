# Rules for any AI working on this repository

This repository holds the **Work tasks app** only: the Streamlit page, the checker it uses, and
the fonts. It is public.

**The task list itself is not here.** It lives in the private repository `hadroid-tasks`
(`data/tasks.json`), together with the full rulebook for changing tasks. When the user talks
about tasks, work in that repository and follow its `AGENTS.md`. Never add a task file to this
repository.

## Working on the app

- `app.py` is the page; `tasks_store.py` reads and writes the task file through GitHub;
  `check_tasks.py` is the same checker the task repository uses, kept here so the app can
  validate what it reads. Keep the two copies identical when the rules change.
- Follow the design notes at the top of `app.py`: dyslexia-friendly layout, plain English,
  no jargon in anything the reader sees.
- Commit messages start with `app:` or `docs:`. Land changes on `main` with
  `git push origin HEAD:main`; Streamlit redeploys from `main` on its own.
- Never put keys, passwords or task data in this repository. The app reads those from
  Streamlit's Secrets: `GITHUB_TOKEN`, `GITHUB_REPO` (the task repository), `APP_PASSWORD`.
