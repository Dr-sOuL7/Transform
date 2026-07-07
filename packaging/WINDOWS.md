# Building the Windows `.exe`

You'll produce a single file, `dist\TextTransform.exe`, that anyone on Windows
can double-click — no Python needed to *run* it. Python is only needed once, on
the machine that *builds* it.

> Why build on Windows? PyInstaller bundles the Python interpreter for the OS it
> runs on; it can't cross-compile. So the Windows `.exe` must be built on
> Windows. The build is fully automated by `build.bat`.

## One-time prerequisites

1. **Install Python 3.10 or newer** from <https://www.python.org/downloads/>.
   - On the first installer screen, **tick "Add python.exe to PATH"**, then
     click *Install Now*.
2. **Get the project onto the machine** — either `git clone` it, or download the
   repo as a ZIP from GitHub and extract it.

## Build it

1. Open the project folder in File Explorer.
2. Go into the `packaging` folder.
3. **Double-click `build.bat`.**

A console window opens and does everything automatically:

- creates an isolated build environment (`.venv`),
- installs the dependencies,
- runs PyInstaller.

The first run takes a few minutes (it downloads packages). When it finishes you'll
see:

```
Done!  Your app is:   dist\TextTransform.exe
```

> Prefer a terminal? Open **PowerShell** or **Command Prompt** in the project
> root and run:
> ```
> packaging\build.bat
> ```

## Run it

- Double-click **`dist\TextTransform.exe`**.
- A small black console window appears ("Running at http://127.0.0.1:800X") and
  your browser opens the app automatically.
- Use the app: drop a `.docx`, pick a preset, **Transform**, review, **Export**.
- **To stop:** close that black console window.

You can copy `TextTransform.exe` anywhere (Desktop, USB stick, another PC) and it
will just run — it's self-contained.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Python was not found` | Re-run the Python installer and tick **Add python.exe to PATH**, then reopen the folder and try again. |
| SmartScreen: "Windows protected your PC" | The `.exe` is unsigned. Click **More info -> Run anyway** (it's your own local build). |
| Antivirus flags the `.exe` | A known false positive for PyInstaller one-file apps. Allow it, or build/run from source. |
| Browser didn't open | Open <http://127.0.0.1:8000> manually (or the port shown in the console). |
| Port already in use | The launcher auto-tries 8000–8009; the console shows the actual URL. You can also set `TT_PORT` before launching. |

## Notes

- **Everything stays local.** The app runs a tiny web server on `127.0.0.1`
  (your own machine) and never sends your documents anywhere.
- To change presets or rules in the packaged app, edit `app/configs/presets.yaml`
  / `app/configs/rules.yaml` **before** building — they're bundled at build time.
