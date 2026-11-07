# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:/isamac/isama-mac-build/main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:/isamac/isama-mac-build/assets', 'assets'), ('C:/isamac/isama-mac-build/ui', 'ui'), ('C:/isamac/isama-mac-build/firebase', 'firebase'), ('C:/isamac/isama-mac-build/.env', '.'), ('C:/isamac/isama-mac-build/firebase/service_key.json', 'firebase')],
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
    name='IsamaManagement',
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
    icon=['C:/isamac/isama-mac-build/assets/favicon.ico'],
)
