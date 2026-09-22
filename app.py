"""Work tasks: a private tick list read from data/tasks.json on GitHub.

Everything about a task is changed by telling Claude (see AGENTS.md). The only thing this page
can change is a tick: mark a task done, or put a done task back on the list.

The layout follows the British Dyslexia Association style guide: a sans-serif font at 18px or
larger, line spacing of at least 1.5, extra letter and word spacing, dark grey text on a cream
background rather than black on white, left-aligned text, bold for emphasis and never italics,
short lines, and a Reading settings panel so the reader can change font, size, spacing and
background. Those choices are kept in the page address so a home-screen shortcut remembers them.
"""
import hmac
import json
import os
import time
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import streamlit as st
import streamlit.components.v1 as components

import check_tasks
import tasks_store

st.set_page_config(page_title="Work tasks", page_icon=":white_check_mark:", layout="centered",
                   initial_sidebar_state="collapsed")


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


# ---------- reading settings (font, size, spacing, background) ----------

FONTS = {
    "lexend": ("Lexend", "'Lexend', Verdana, sans-serif"),
    "atkinson": ("Atkinson Hyperlegible", "'Atkinson Hyperlegible', Verdana, sans-serif"),
    "verdana": ("Verdana", "Verdana, Geneva, Tahoma, sans-serif"),
    "opendyslexic": ("OpenDyslexic", "'OpenDyslexic', Verdana, sans-serif"),
}
SIZES = {"normal": ("Normal", 18), "large": ("Large", 21), "xlarge": ("Extra large", 24)}
SPACINGS = {
    "normal": ("Normal", {"letter": "0.05em", "word": "0.12em", "line": "1.6"}),
    "wide": ("Wide", {"letter": "0.12em", "word": "0.3em", "line": "1.9"}),
}
BACKGROUNDS = {
    "cream": ("Cream", "#FAF7F0", "#FFFFFF"),
    "yellow": ("Pale yellow", "#FBF3D0", "#FFFBE8"),
    "blue": ("Pale blue", "#E6F0F8", "#F6FAFD"),
    "grey": ("Pale grey", "#ECECEA", "#F8F8F7"),
    "white": ("White", "#FFFFFF", "#F4F4F2"),
}
TEXT = "#1F2430"      # dark grey-navy, softer than pure black
MUTED = "#4F5866"     # for captions and dates; still passes contrast on every background
ACCENT = "#0077A8"


def reading_settings():
    """The reader's choices, read from the page address, with sensible defaults."""
    q = st.query_params
    return {
        "font": q.get("font") if q.get("font") in FONTS else "lexend",
        "size": q.get("size") if q.get("size") in SIZES else "normal",
        "space": q.get("space") if q.get("space") in SPACINGS else "normal",
        "bg": q.get("bg") if q.get("bg") in BACKGROUNDS else "cream",
    }


def build_style(s):
    family = FONTS[s["font"]][1]
    px = SIZES[s["size"]][1]
    sp = SPACINGS[s["space"]][1]
    bg, card = BACKGROUNDS[s["bg"]][1], BACKGROUNDS[s["bg"]][2]
    return f"""
<style>
@font-face {{ font-family: 'Atkinson Hyperlegible'; font-weight: 400; src: url('app/static/fonts/AtkinsonHyperlegible-400.woff2') format('woff2'); }}
@font-face {{ font-family: 'Atkinson Hyperlegible'; font-weight: 700; src: url('app/static/fonts/AtkinsonHyperlegible-700.woff2') format('woff2'); }}
@font-face {{ font-family: 'OpenDyslexic'; font-weight: 400; src: url('app/static/fonts/OpenDyslexic-Regular.woff') format('woff'); }}
@font-face {{ font-family: 'OpenDyslexic'; font-weight: 700; src: url('app/static/fonts/OpenDyslexic-Bold.woff') format('woff'); }}

/* no banner at the top; the page starts with the title */
header[data-testid="stHeader"] {{ display: none; }}
.block-container {{ padding-top: 1.25rem; padding-bottom: 4rem; max-width: 46rem; }}

/* colours: dark grey text on a soft background, never black on white unless chosen */
.stApp, [data-testid="stAppViewContainer"] {{ background-color: {bg} !important; color: {TEXT}; }}
[data-testid="stExpander"] details {{ background-color: {card}; border-radius: 10px; }}
[data-testid="stForm"] {{ background-color: {card}; border-radius: 10px; }}

/* type: sans serif, {px}px, line spacing {sp['line']}, extra letter and word spacing, left aligned */
html, body, p, li, label, button, input, textarea, h1, h2, h3, summary,
[data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"] {{
    font-family: {family} !important;
    letter-spacing: {sp['letter']};
    word-spacing: {sp['word']};
}}
html, body {{ font-size: {px}px; line-height: {sp['line']}; }}
[data-testid="stAppViewContainer"] p, [data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] label, [data-testid="stAppViewContainer"] summary {{
    font-size: {px}px; line-height: {sp['line']}; text-align: left; color: {TEXT};
}}
[data-testid="stAppViewContainer"] p {{ margin-bottom: 0.6em; }}
h1 {{ font-size: {round(px * 1.7)}px !important; font-weight: 700 !important; line-height: 1.3 !important; }}
h2, h3 {{ font-size: {round(px * 1.25)}px !important; font-weight: 700 !important; line-height: 1.3 !important; }}
em, i {{ font-style: normal; font-weight: 700; }}   /* never italics */
[data-testid="stCaptionContainer"] p {{ font-size: {max(px - 2, 15)}px; color: {MUTED}; }}

/* controls: big targets, clear focus */
[data-testid="stCheckbox"] {{ min-height: 52px; display: flex; align-items: center; margin-top: 0.4em; }}
[data-testid="stCheckbox"] label {{ min-height: 52px; align-items: center; gap: 12px; }}
[data-testid="stCheckbox"] label > span:first-of-type {{ width: 28px; height: 28px; }}
[data-testid="stCheckbox"] p {{ font-size: {px}px; font-weight: 700; }}
[data-testid="stButton"] button {{ min-height: 52px; font-size: {max(px - 2, 16)}px; font-weight: 700; border-radius: 10px; }}
[data-testid="stExpander"] summary {{ min-height: 48px; font-size: {max(px - 2, 16)}px; }}
button[data-baseweb="tab"] {{ min-height: 52px; font-size: {max(px - 2, 16)}px; font-weight: 700; }}
*:focus-visible {{ outline: 3px solid {ACCENT} !important; outline-offset: 2px; }}
hr {{ margin: 1.2em 0; }}
#MainMenu, footer {{ visibility: hidden; }}
</style>
"""


SETTINGS = reading_settings()
st.html(build_style(SETTINGS))


def remember(param, options, key):
    """Writes a changed reading setting into the page address."""
    label = st.session_state[key]
    for code, spec in options.items():
        if spec[0] == label:
            st.query_params[param] = code
            return


def reading_settings_panel(s):
    with st.expander("Reading settings"):
        st.caption("Pick what is easiest for you to read. The choices are kept in the page address, "
                   "so add the app to your home screen after choosing.")
        st.selectbox("Font", [v[0] for v in FONTS.values()], index=list(FONTS).index(s["font"]),
                     key="set_font", on_change=remember, args=("font", FONTS, "set_font"))
        st.selectbox("Text size", [v[0] for v in SIZES.values()], index=list(SIZES).index(s["size"]),
                     key="set_size", on_change=remember, args=("size", SIZES, "set_size"))
        st.selectbox("Spacing between letters and lines", [v[0] for v in SPACINGS.values()],
                     index=list(SPACINGS).index(s["space"]),
                     key="set_space", on_change=remember, args=("space", SPACINGS, "set_space"))
        st.selectbox("Background", [v[0] for v in BACKGROUNDS.values()], index=list(BACKGROUNDS).index(s["bg"]),
                     key="set_bg", on_change=remember, args=("bg", BACKGROUNDS, "set_bg"))


def read_aloud(text, key):
    """A Read aloud button that uses the phone's or computer's own voice."""
    safe = json.dumps(text)
    components.html(f"""
<div style="font-family: Verdana, sans-serif; display: flex; gap: 10px;">
  <button id="go" style="min-height: 48px; padding: 0 18px; border: 2px solid {ACCENT}; border-radius: 10px; background: {ACCENT}; color: #fff; font-size: 16px; font-weight: 700; cursor: pointer;">Read aloud</button>
  <button id="stop" style="min-height: 48px; padding: 0 18px; border: 2px solid {ACCENT}; border-radius: 10px; background: #fff; color: {ACCENT}; font-size: 16px; font-weight: 700; cursor: pointer;">Stop</button>
</div>
<script>
  const text = {safe};
  document.getElementById("go").onclick = function () {{
    if (!window.speechSynthesis) {{ alert("This browser cannot read aloud."); return; }}
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "en-GB"; u.rate = 0.95;
    window.speechSynthesis.speak(u);
  }};
  document.getElementById("stop").onclick = function () {{ if (window.speechSynthesis) window.speechSynthesis.cancel(); }};
</script>
""", height=60)


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
    if d == today:
        return "Due today"
    if d == today + timedelta(days=1):
        return "Due tomorrow"
    if d < today:
        return f"Was due {day_words(d)}"
    return f"Due {day_words(d)}"


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
            st.markdown(f"<span style='color:{MUTED}; font-size: 0.9em'>{when_words(note['at'])}</span><br>{note['note']}",
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


def spoken(tasks, ticked):
    """The list as sentences for the Read aloud button."""
    lines = []
    for t in tasks:
        number = t["id"][1:]
        extra = closed_words(t) if ticked else (due_words(t) or "no due date")
        lines.append(f"Task {number}. {t['title']}. {extra}. {t['summary']}")
    return " ".join(lines) if lines else "Nothing to do."


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
    reading_settings_panel(SETTINGS)

    data, errors, _ = check_tasks.check_text(text)
    if errors:
        notice("The task file could not be read, so nothing is shown. Nothing is lost: every earlier version is kept on GitHub. "
               "Tell Claude: \"The task file is broken, restore it from the last good version.\"", "\n".join(errors))

    tasks = data["tasks"]
    open_tasks = sorted([t for t in tasks if t["status"] == "open"], key=open_order)
    done_tasks = sorted([t for t in tasks if t["status"] == "done"], key=lambda t: t["closed"], reverse=True)
    aside_tasks = sorted([t for t in tasks if t["status"] == "set aside"], key=lambda t: t["closed"], reverse=True)

    tab_open, tab_done = st.tabs([f"To do · {len(open_tasks)}", f"Done · {len(done_tasks) + len(aside_tasks)}"])

    with tab_open:
        read_aloud(spoken(open_tasks, ticked=False), key="say_open")
        if not open_tasks:
            st.info("Nothing to do. Tell Claude when something comes up.")
        for task in open_tasks:
            task_card(task, version, ticked=False)

    with tab_done:
        st.subheader("Done")
        read_aloud(spoken(done_tasks, ticked=True), key="say_done")
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
