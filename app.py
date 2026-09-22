"""Work tasks: a private tick list read from data/tasks.json on GitHub.

Everything about a task is changed by telling Claude (see AGENTS.md). The only thing this page
can change is a tick: mark a task done, or put a done task back on the list.
"""
import hmac
import os
import time
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import streamlit as st

import check_tasks
import tasks_store

st.set_page_config(page_title="Work tasks", page_icon=":white_check_mark:", layout="centered",
                   initial_sidebar_state="collapsed")

STYLE = """
<style>
html, body, p, li, label, button, input, textarea, h1, h2, h3,
[data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"] {
    font-family: 'Lexend', sans-serif;
}
html, body { font-size: 18px; line-height: 1.5; }
[data-testid="stAppViewContainer"] p, [data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] label { font-size: 18px; line-height: 1.5; text-align: left; }
[data-testid="stCaptionContainer"] p { font-size: 16px; }
.block-container { padding-top: 1.5rem; }
[data-testid="stCheckbox"] { min-height: 48px; display: flex; align-items: center; }
[data-testid="stCheckbox"] label { min-height: 48px; align-items: center; gap: 10px; }
[data-testid="stCheckbox"] label > span:first-of-type { width: 26px; height: 26px; }
[data-testid="stCheckbox"] p { font-size: 18px; font-weight: 500; }
[data-testid="stButton"] button { min-height: 48px; font-size: 16px; font-weight: 600; border-radius: 10px; }
[data-testid="stExpander"] summary { min-height: 44px; font-size: 16px; }
button[data-baseweb="tab"] { min-height: 48px; font-size: 16px; font-weight: 600; }
#MainMenu, footer { visibility: hidden; }
</style>
"""
st.html(STYLE)


# ---------- settings ----------

def setting(name, default=None):
    """A value from the environment or from Streamlit's secrets, or the default."""
    value = os.environ.get(name)
    if value:
        return value
    try:
        return st.secrets.get(name, default)
    except Exception:  # no secrets file at all
        return default


TIMEZONE = ZoneInfo(setting("TIMEZONE", "Europe/London"))
TZ_LABEL = "UK time" if str(TIMEZONE) == "Europe/London" else str(TIMEZONE)


def get_store():
    local = setting("TASKS_LOCAL_FILE")
    if local:
        return tasks_store.LocalStore(local)
    token = setting("GITHUB_TOKEN")
    repo = setting("GITHUB_REPO")
    if not token or not repo:
        return None
    return tasks_store.GitHubStore(token, repo, branch=setting("GITHUB_BRANCH", "main"))


# ---------- words for dates and times ----------

def day_words(d):
    """25 Sep 2026 -> 'Fri 25 Sep'."""
    return f"{d.strftime('%a')} {d.day} {d.strftime('%b')}"


def local_time(timestamp):
    return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(TIMEZONE)


def when_words(timestamp):
    t = local_time(timestamp)
    return f"{day_words(t)}, {t.strftime('%H:%M')}"


def due_words(task):
    if not task["due"]:
        return None
    d = date.fromisoformat(task["due"])
    today = datetime.now(TIMEZONE).date()
    return f"{'Was due' if d < today else 'Due'} {day_words(d)}"


def closed_words(task):
    if not task["closed"]:
        return ""
    label = "Done" if task["status"] == "done" else "Set aside"
    return f"{label} {day_words(local_time(task['closed']))}"


def now_stamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------- the one thing the app can change: a tick ----------

def flash(message):
    st.session_state["flash"] = message


def on_tick(task_id, make_done):
    """Runs when a box is ticked or unticked. Reads the newest file, changes that one task, saves."""
    store = get_store()
    for attempt in (1, 2):
        try:
            text, version = store.read()
        except tasks_store.StoreError:
            flash("GitHub did not answer, so nothing was changed. Tap Refresh and try again.")
            return
        data, errors, _ = check_tasks.check_text(text)
        if errors:
            flash("The task file could not be read, so nothing was changed.")
            return
        task = next((t for t in data["tasks"] if t["id"] == task_id), None)
        if task is None:
            flash(f"{task_id} is no longer in the file. List refreshed.")
            return
        wanted = "done" if make_done else "open"
        if task["status"] == wanted:
            flash(f"{task_id} is already {'done' if make_done else 'on the list'}. List refreshed.")
            return
        stamp = now_stamp()
        task["status"] = wanted
        task["closed"] = stamp if make_done else None
        task["notes"].append({"at": stamp, "note": "Ticked done in the app." if make_done else "Unticked in the app."})
        new_text = check_tasks.dump(data)
        _, new_errors, _ = check_tasks.check_text(new_text)
        new_errors += check_tasks.check_history(text, new_text)
        if new_errors:
            flash("Something went wrong preparing the change, so nothing was saved.")
            return
        message = f"app: tick {task_id} done" if make_done else f"app: untick {task_id}"
        try:
            store.write(new_text, version, message)
            flash(f"{task_id} marked done" if make_done else f"{task_id} is back on the list")
            return
        except tasks_store.ConflictError:
            continue  # someone saved first: read again and try once more
        except tasks_store.ProtectedError:
            flash("A protection rule on the main branch blocked the save. Remove the rule on GitHub.")
            return
        except tasks_store.StoreError:
            flash("GitHub did not answer, so nothing was changed. Tap Refresh and try again.")
            return
    flash("GitHub was busy, so nothing was changed. Tap Refresh and tick again.")


# ---------- the password screen ----------

def unlocked():
    """True once the right password has been typed in this browser tab.

    Nothing is read from GitHub until then. A new tab or page load asks again.
    """
    if st.session_state.get("unlocked"):
        return True
    st.title("Work tasks")
    password = setting("APP_PASSWORD")
    if not password:
        st.warning("No password has been set for the app yet, so nothing is shown. "
                   "Add APP_PASSWORD under Manage app, Settings, Secrets on Streamlit, then Reboot app.")
        return False
    with st.form("unlock"):
        typed = st.text_input("Password", type="password")
        opened = st.form_submit_button("Open", width="stretch")
    if opened:
        tries = st.session_state.get("tries", 0)
        if tries >= 5:
            time.sleep(3)  # slow down guessing
        if hmac.compare_digest(typed.strip().encode("utf-8"), str(password).encode("utf-8")):
            st.session_state["unlocked"] = True
            st.rerun()
        st.session_state["tries"] = tries + 1
        st.error("That password is not right.")
    return False


# ---------- drawing the page ----------

def history(task):
    with st.expander("History"):
        for note in reversed(task["notes"]):
            st.markdown(f"<span style='font-size:15px;opacity:0.75'>{when_words(note['at'])}</span><br>{note['note']}",
                        unsafe_allow_html=True)


def task_card(task, version, ticked):
    st.checkbox(f"{task['id']} {task['title']}", value=ticked, key=f"tick_{task['id']}_{version}",
                on_change=on_tick, args=(task["id"], not ticked))
    if ticked:
        st.markdown(f"**{closed_words(task)}**")
    else:
        due = due_words(task)
        if due:
            st.markdown(f"**{due}**")
    st.write(task["summary"])
    if not ticked and task["progress"] is not None:
        st.caption(f"{task['progress']}% done")
    history(task)
    st.divider()


def aside_card(task):
    st.markdown(f"**{task['id']} {task['title']}**")
    st.markdown(f"**{closed_words(task)}**")
    st.write(task["summary"])
    history(task)
    st.divider()


def notice(text, details=None):
    st.warning(text)
    if details:
        with st.expander("Details for Claude"):
            st.code(details, language=None)
    st.stop()


def open_order(task):
    return (0, task["due"]) if task["due"] else (1, check_tasks.id_number(task["id"]))


def main():
    if not unlocked():
        st.stop()

    store = get_store()
    if store is None:
        notice("The app is not set up yet. Add GITHUB_TOKEN and GITHUB_REPO under Manage app, Settings, Secrets on Streamlit, then Reboot app.")

    if "flash" in st.session_state:
        st.toast(st.session_state.pop("flash"))

    left, right = st.columns([3, 1], vertical_alignment="center")
    with left:
        st.title("Work tasks")
    with right:
        if st.button("Refresh", width="stretch"):
            st.rerun()

    try:
        text, version = store.read()
    except tasks_store.AuthError:
        notice("The app cannot reach GitHub. Nothing is lost. Your tasks are safe on GitHub. Tell Claude: \"The app cannot reach GitHub.\"",
               "GitHub refused the app's key. Usually the key has expired or was pasted wrongly. Fix: make a new key on GitHub, "
               "paste it under Manage app, Settings, Secrets on Streamlit as GITHUB_TOKEN, then Reboot app.")
    except tasks_store.NotFoundError:
        notice("The app cannot find the task file. Nothing is lost. Tell Claude: \"The app cannot find the task file.\"",
               "GitHub answered 404. Check GITHUB_REPO in the app's Secrets on Streamlit (it should look like owner/repo), "
               "and that data/tasks.json exists on the main branch.")
    except tasks_store.StoreError as e:
        notice("GitHub did not answer. Tap Refresh in a minute.", str(e))

    read_at = datetime.now(TIMEZONE).strftime("%H:%M")
    st.caption(f"Read from GitHub at {read_at}, {TZ_LABEL}")
    st.caption("To add or change a task, tell Claude.")

    data, errors, _ = check_tasks.check_text(text)
    if errors:
        notice("The task file could not be read, so nothing is shown. Nothing is lost: every earlier version is kept on GitHub. "
               "Tell Claude: \"The task file is broken, restore it from the last good version.\"", "\n".join(errors))

    tasks = data["tasks"]
    open_tasks = sorted([t for t in tasks if t["status"] == "open"], key=open_order)
    done_tasks = sorted([t for t in tasks if t["status"] == "done"], key=lambda t: t["closed"], reverse=True)
    aside_tasks = sorted([t for t in tasks if t["status"] == "set aside"], key=lambda t: t["closed"], reverse=True)

    tab_open, tab_done = st.tabs([f"To do · {len(open_tasks)}", f"Done and set aside · {len(done_tasks) + len(aside_tasks)}"])

    with tab_open:
        if not open_tasks:
            st.info("Nothing to do. Tell Claude when something comes up.")
        for task in open_tasks:
            task_card(task, version, ticked=False)

    with tab_done:
        st.subheader("Done")
        if not done_tasks:
            st.info("Nothing finished yet.")
        for task in done_tasks:
            task_card(task, version, ticked=True)
        st.subheader("Set aside")
        st.caption("Only Claude can set a task aside or bring it back.")
        if not aside_tasks:
            st.info("Nothing set aside.")
        for task in aside_tasks:
            aside_card(task)


main()
