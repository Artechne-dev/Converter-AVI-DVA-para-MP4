# -*- mode: python ; coding: utf-8 -*-
import os
import customtkinter

spec_dir = os.path.dirname(os.path.abspath(spec_filename)) if 'spec_filename' in locals() else os.getcwd()
main_py_path = os.path.join(spec_dir, 'main.py')
customtkinter_path = os.path.dirname(customtkinter.__file__)

datas = [(customtkinter_path, 'customtkinter/')]
if os.path.exists(os.path.join(spec_dir, 'ffmpeg.exe')):
    datas.append(('ffmpeg.exe', '.'))

a = Analysis(
    [main_py_path],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
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
