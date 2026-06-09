# code: language=python
# main.spec
# This file tells PyInstaller how to bundle your application
from PyInstaller.building.api import EXE, PYZ
from PyInstaller.building.build_main import Analysis, COLLECT, BUNDLE
import sys
import os
import site


site_packages_path = None
block_cipher = None

for site_path in site.getsitepackages():
  if 'site-packages' in site_path:
    site_packages_path = site_path
    break

if site_packages_path is None:
  raise RuntimeError("The site-packages directory could not be found. Please setup the python envrionment correctly and try again...")

a = Analysis(
    ['src/cibmangotree/__main__.py'],  # Main entry point
    pathex=['.', 'src'],    # Ensure all paths are correctly included
    binaries=[],
    datas=[
        # version file, if defined
        *(
            [('./VERSION', '.')]
            if os.path.exists('VERSION') else []
        ),

        # GUI icons (Simple Icons for footer links)
        ('src/cibmangotree/gui/icons', 'cibmangotree/gui/icons'),

        # Vue GUI components
        ('src/cibmangotree/gui/components/dist', 'cibmangotree/gui/components/dist'),

        # NiceGUI static files (required for GUI mode)
        (os.path.join(site_packages_path, 'nicegui'), 'nicegui'),
    ],
    hiddenimports=[
        'numpy',
        'asyncio',
        'polars',
        'linkify_it',
        'markdown_it',
        'mdurl',
        'pythonjsonlogger',
        'pythonjsonlogger.json',
        # NiceGUI (required for GUI mode)
        'nicegui',
        'nicegui.elements',
        'nicegui.events',
        'nicegui.ui',
        'fastapi',
    ],  # Include any imports that PyInstaller might miss
    excludes=[
        'pytest',
        'py',
        'setuptools',
        'pip',
        'wheel',
    ],
    runtime_hooks=[],
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if sys.platform == "darwin":
    # For onedir build: EXE only contains scripts
    exe = EXE(
        pyz,
        a.scripts,
        exclude_binaries=True,  # This makes it onedir, not onefile
        name='CIBMangoTree',
        debug=False,
        bootloader_ignore_signals=False,
        strip=True,
        upx=True,
        console=False,  # No console window for GUI app
        entitlements_file="./mango.entitlements",
        codesign_identity=os.getenv('APPLE_APP_CERT_ID'),
    )

    # Collect all files for the bundle (onedir structure)
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=True,
        upx=True,
        name='CIBMangoTree'
    )

    # Create macOS app bundle from the collected files
    app = BUNDLE(
        coll,
        name='CIBMangoTree.app',
        icon=None,  # Add icon path when available (e.g., 'icon.icns')
        bundle_identifier='org.civictechdc.cibmangotree',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': '0.9.0',
            'CFBundleName': 'CIB Mango Tree',  # Display name (can have spaces)
        },
    )
else:
    # Windows/Linux: onedir mode (avoids runtime temp extraction issues with antivirus)
    exe = EXE(
        pyz,
        a.scripts,
        exclude_binaries=True,  # onedir structure
        name='CIBMangoTree',
        debug=True,
        strip=False,
        upx=True,
        console=True,  # No console window for GUI app
        icon=None,  # Add icon path when available (e.g., 'icon.ico' for Windows)
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        name='CIBMangoTree',
    )
