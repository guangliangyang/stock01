# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect akshare data files
akshare_datas = collect_data_files('akshare')

# Collect all akshare submodules
akshare_hiddenimports = collect_submodules('akshare')

# Collect yfinance submodules
yfinance_hiddenimports = collect_submodules('yfinance')

a = Analysis(
    ['src/main.py'],
    pathex=['D:\\workspace\\repos\\stock01'],
    binaries=[],
    datas=[
        ('config/default_settings.json', 'config'),
        ('src/i18n/locales/en.json', 'src/i18n/locales'),
        ('src/i18n/locales/zh.json', 'src/i18n/locales'),
    ] + akshare_datas,
    hiddenimports=[
        'akshare',
        'baostock',
        'yfinance',
        'pandas',
        'numpy',
        'pydantic',
        'loguru',
        'winotify',
        'PyQt5',
        'PyQt5.QtWidgets',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'curl_cffi',
        'tqdm',
        'requests',
        'beautifulsoup4',
        'lxml',
        'html5lib',
        'frozendict',
        'peewee',
        'websockets',
        'multitasking',
    ] + akshare_hiddenimports + yfinance_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DividendStockScreener',
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
)
