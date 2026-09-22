# Work tasks

A private to-do list that you update by talking to an AI, and read on your phone.

- **The list** is one file, `data/tasks.json`, in a separate private repository,
  `hadroid-tasks`. It keeps every task ever added, with dated notes, so nothing is lost and
  old work can be reviewed. This repository holds only the app and can be public.
- **The app** (Streamlit) shows the list as a tick list. You can tick a task done or untick
  it. Everything else is changed by telling Claude.
- **The rules** an AI follows are in the `hadroid-tasks` repository's `AGENTS.md`.

## Day to day

1. Open the Claude app on your phone, go to the **Code** tab, pick the `hadroid-tasks`
   repository and the `main` branch, and type what happened, for example:
   *"Task 3 is done. Add a task to chase the supplier about the invoice, due Friday."*
2. Claude reads the rules, updates the file, checks it, saves it to `main`, and replies with
   exactly what changed. Expect one to three minutes; it starts a fresh session each time.
3. Open the app, type the password, and tap **Refresh**. The list matches the file.

The app asks for the password every time it opens in a new tab. Nothing is shown, and nothing
is read from GitHub, until the right password is typed.

You can also tick a box in the app. That saves straight to the file with a note
"Ticked done in the app", and Claude sees it next time.

Each task shows its number (T7), its title, "Due Fri 25 Sep" or "Was due Fri 18 Sep" in words,
a one-line summary of where it stands, a percentage only if you gave one, and a fold-out
**History** of dated notes. Tasks with a due date come first, soonest first. Overdue tasks
stay on the list; a task with no date has unlimited time.

The second tab shows finished tasks, newest first, and tasks you asked Claude to set aside.

## Reading settings

The layout follows the British Dyslexia Association style guide: a clear sans-serif font at
18px or larger, line spacing of 1.6, extra space between letters and words, dark grey text on
a cream background rather than black on white, everything left-aligned, bold for emphasis and
never italics, short lines, and big buttons.

Open **Reading settings** under the title to change:

- **Font:** Lexend, Atkinson Hyperlegible, Verdana or OpenDyslexic. Research finds no single
  "dyslexia font" that helps everyone, so pick the one you read most easily.
- **Text size:** Normal, Large or Extra large.
- **Spacing:** Normal or Wide (wider letter, word and line spacing).
- **Background:** Cream, Pale yellow, Pale blue, Pale grey or White.

The choices are kept in the page address, so add the app to your home screen after choosing
and it opens that way every time. Each tab also has a **Read aloud** button that uses your
phone's or computer's own voice.

## Setting it up (once)

You need: this repository, the private `hadroid-tasks` repository, a free Streamlit
Community Cloud account, and the Claude app on your phone with `hadroid-tasks` connected.

1. **GitHub key for the app.** On GitHub: your profile photo, **Settings**, **Developer
   settings**, **Personal access tokens**, **Fine-grained tokens**, **Generate new token**.
   Name: `work-tasks-app`. Expiration: **No expiration**. Repository access: **Only select
   repositories**, choose `hadroid-tasks` (the task repository, not this one). Permissions, Repository permissions, **Contents: Read and
   write**. Generate, then copy the key once; GitHub will not show it again.
2. **Streamlit.** Go to share.streamlit.io and sign in with GitHub (say yes to the permission
   it asks for; it needs it to see a private repository). **Create app**, **Deploy a public
   app from GitHub** (the same button is used for private ones). Repository: this one. Branch:
   `main`. Main file path: `app.py`. Open **Advanced settings** and paste into **Secrets**:

   ```toml
   GITHUB_TOKEN = "paste the key here"
   GITHUB_REPO = "owner/hadroid-tasks"
   APP_PASSWORD = "a password of your choice"
   ```

   Then **Deploy**. This uses your one free private app. Do not add any viewers.
3. **Check it is private.** Open the app's link in a private browser window. A stranger should
   see a sign-in page, not your tasks.
4. **Phone.** Add the app link to your home screen. Free Streamlit apps go to sleep after
   about 12 hours without a visit; the first open of the day shows a wake-up button and takes
   about a minute.

Do not add any protection rules to the `main` branch of `hadroid-tasks`. They would block
both the app's ticks and Claude's saves.

## When something goes wrong

The app never shows a wall of code. It shows one plain message, and where useful a fold-out
called **Details for Claude**. Copy the message to Claude and it will sort it out:

- **"The app cannot reach GitHub."** The key has probably expired or was pasted wrongly. Make
  a new key (step 1 above), then on Streamlit open the app's menu, **Settings**, **Secrets**,
  replace the value, save, and **Reboot app**.
- **"The task file could not be read."** Nothing is lost; every earlier version is kept in
  the file's history on GitHub. Tell Claude: *"The task file is broken, restore it from the
  last good version."*
- **"GitHub was busy, nothing was changed."** Tap Refresh and tick again.
- **"No password has been set for the app yet."** Add `APP_PASSWORD` to the app's Secrets on
  Streamlit, then Reboot app.

## Privacy

The repository is private, and the app only shows the list to you after sign-in. Two other
parties handle the data: GitHub stores it, and Anthropic's servers run the Claude sessions
that edit it, as well as Streamlit's servers that run the app. Anything you type to Claude or
ChatGPT is seen by that company, so keep truly confidential details out of the notes. The
app's GitHub key is stored only in Streamlit's Secrets, never in the repository.

## Trying it on your own computer (optional)

```
pip install -r requirements.txt
APP_PASSWORD=test TASKS_LOCAL_FILE=../hadroid-tasks/data/tasks.json streamlit run app.py
```

With `TASKS_LOCAL_FILE` set, the app reads and writes that local file instead of GitHub.
