# -*- mode: python ; coding: utf-8 -*-
import os
import customtkinter
from PyInstaller.utils.hooks import collect_all

spec_dir = os.path.dirname(os.path.abspath(spec_filename)) if 'spec_filename' in locals() else os.getcwd()
main_py_path = os.path.join(spec_dir, 'main.py')
customtkinter_path = os.path.dirname(customtkinter.__file__)

# Collect data, binaries, and hidden imports for tkinterdnd2
t_datas, t_binaries, t_hiddenimports = collect_all('tkinterdnd2')

# Collect winotify for Windows toast notifications
w_datas, w_binaries, w_hiddenimports = collect_all('winotify')

datas = [(customtkinter_path, 'customtkinter/')] + t_datas + w_datas
binaries = t_binaries + w_binaries
hiddenimports = t_hiddenimports + w_hiddenimports

if os.path.exists(os.path.join(spec_dir, 'ffmpeg.exe')):
    datas.append(('ffmpeg.exe', '.'))

a = Analysis(
    [main_py_path],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    a.binaries,
    a.datas,
    [],
    name='Converter-AVI-MP4',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)
