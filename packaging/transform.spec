# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — one-file, cross-platform.

Build from the repo root:  python -m PyInstaller packaging/transform.spec
Produces a single self-contained executable in dist/ that launches the offline
web app. The same spec builds a Linux/macOS binary or a Windows .exe depending
on the OS you run it on (PyInstaller does not cross-compile).
"""

import os
from PyInstaller.utils.hooks import collect_submodules

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))

datas = [
    (os.path.join(ROOT, "app", "web", "static"), os.path.join("app", "web", "static")),
    (os.path.join(ROOT, "app", "configs", "presets.yaml"), os.path.join("app", "configs")),
    (os.path.join(ROOT, "app", "configs", "rules.yaml"), os.path.join("app", "configs")),
]

# uvicorn loads its loop/protocol implementations dynamically.
hiddenimports = collect_submodules("uvicorn")

a = Analysis(
    [os.path.join(ROOT, "app", "launcher.py")],
    pathex=[ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="TextTransform",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
