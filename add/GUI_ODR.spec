# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['GUI_ODR.py'],
    pathex=['/home/rlh/Escritorio/Dist_ODR/V1.2 Linux'],
    binaries=[],
    datas=[
        ('odr_app_INTRO.png','.'),
        ('odr_app_logo16.png','.'),
        ('odr_app_logo24.png','.'),
        ('odr_app_logo32.png','.'),
        ('odr_app_logo48.png','.'),
        ('odr_app_logo64.png','.'),
        ('odr_app_logo72.png','.'),
        ('odr_app_logo96.png','.'),
        ('odr_app_logo128.png','.'),
        ('odr_app_logo256.png','.'),
        ('odr_app_logo.ico','.'),
    ],
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
    name='GUI_ODR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
