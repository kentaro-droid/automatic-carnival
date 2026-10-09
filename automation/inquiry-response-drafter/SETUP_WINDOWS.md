# Windows Setup Guide

## Purpose

This guide starts the desktop Inquiry Response Drafter on a Windows PC.

## Security first

The GitHub repository is currently Public. Until it is changed to Private, use only fictional or fully anonymized test data.

Do not enter real customer names, email addresses, phone numbers, application details, contracts, IDs, passwords, API keys, or other confidential information.

## 1. Install Python

1. Open https://www.python.org/downloads/windows/
2. Download a current Python 3 release.
3. Start the installer.
4. Enable **Add Python to PATH** if the installer shows that option.
5. Complete installation.

No external Python packages are required for the current prototype. It uses Python's standard Tkinter GUI library.

## 2. Download the repository

For a simple test:

1. Open the `kentaro-droid/automatic-carnival` repository on GitHub.
2. Select **Code**.
3. Select **Download ZIP**.
4. Extract the ZIP to a local folder.
5. Open `automation/inquiry-response-drafter`.

## 3. Start the application

Double-click:

`run_windows.bat`

The launcher looks for `py` first and then `python`.

If Python is installed correctly, the desktop input window will open.

## 4. Test with fictional data

The initial screen contains fictional sample values.

1. Keep the sample data as-is.
2. Select `en` as the reply language.
3. Click **Generate Draft**.
4. Confirm that the customer reply and internal checklist appear in separate panels.
5. Enter a fictional internal note such as `INTERNAL TEST ONLY` and generate again.
6. Click **Copy to Clipboard** and paste into a blank text editor. Only the customer reply (including its subject) should appear; no checklist, `Notes:`, or `INTERNAL TEST ONLY`.
7. Edit the customer reply, then copy again and confirm that the edit is included.
8. Repeat steps 3–7 with reply language `ja`, and again with empty internal notes.
9. Click **Clear**. Both output panels should be empty; copying should prompt to generate a draft first.

## Pass criteria

The prototype passes the local test when all of the following are true:

- The window opens without an error.
- English draft generation works.
- Japanese draft generation works after changing the language to `ja`.
- The internal verification checklist appears.
- Copy to Clipboard includes only the editable customer reply in both languages.
- Internal checklist and notes remain visible in the separate read-only panel.
- No real personal or confidential data is used during the test.

## Troubleshooting

### Python was not found

Reinstall Python and ensure Python is available on PATH, then restart Windows or open a new session and try again.

### Tkinter error

Use the standard Python installer from python.org. Some custom/minimal Python installations may not include Tkinter.

### The window closes immediately

Open Command Prompt in the project folder and run:

`py app.py`

or:

`python app.py`

Read the displayed error message before making changes.

## Recommended next step

After the local fictional-data test succeeds, change the repository to Private before considering any workflow involving real business data.

