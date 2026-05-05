# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

project_dir = Path.cwd()
datas = [
    (str(project_dir / 'templates'), 'templates'),
    (str(project_dir / 'static'), 'static'),
    (str(project_dir / 'media'), 'media'),
    (str(project_dir / 'db.sqlite3'), '.'),
]
webview_datas, webview_binaries, webview_hiddenimports = collect_all('webview')
cryptography_datas, cryptography_binaries, cryptography_hiddenimports = collect_all('cryptography')

datas += webview_datas + cryptography_datas

a = Analysis(
    ['run.py'],
    pathex=[str(project_dir)],
    binaries=webview_binaries + cryptography_binaries,
    datas=datas,
    hiddenimports=(
        collect_submodules('webview')
        + webview_hiddenimports
        + cryptography_hiddenimports
    ),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EduFlow by Nuvana',
    icon=str(project_dir / 'logo edu.ico'),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EduFlow by Nuvana',
)
