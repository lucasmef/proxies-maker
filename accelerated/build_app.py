from pathlib import Path
import plistlib
import shutil
import subprocess

base = Path(__file__).resolve().parent
app = base / 'Preview mínimo acelerado.app'
contents = app / 'Contents'
resources = contents / 'Resources'
(contents / 'MacOS').mkdir(parents=True, exist_ok=True)
(resources / 'bin').mkdir(parents=True, exist_ok=True)
for name in ['preview.py', 'worker.py']:
    shutil.copy2(base / name, resources / name)
shutil.copy2(base / 'bin/ffmpeg', resources / 'bin/ffmpeg')
info = {
    'CFBundleIdentifier': 'local.lucas.preview-minimo-acelerado',
    'CFBundleName': 'Preview mínimo acelerado',
    'CFBundleDisplayName': 'Preview mínimo acelerado',
    'CFBundleExecutable': 'PreviewMinimo',
    'CFBundlePackageType': 'APPL',
    'CFBundleShortVersionString': '1.0',
    'CFBundleVersion': '1',
    'LSMinimumSystemVersion': '13.0',
    'NSHighResolutionCapable': True,
    'CFBundleDocumentTypes': [{'CFBundleTypeName': 'Vídeos', 'CFBundleTypeRole': 'Viewer',
                             'LSHandlerRank': 'Alternate', 'LSItemContentTypes': ['public.movie'],
                             'CFBundleTypeExtensions': ['mov', 'mp4', 'm4v']}],
}
(contents / 'Info.plist').write_bytes(plistlib.dumps(info))
subprocess.run(['swiftc', '-swift-version', '5', '-module-cache-path', '/private/tmp/preview-swift-cache',
                str(base/'Sources/PreviewMinimo.swift'), '-o', str(contents/'MacOS/PreviewMinimo'),
                '-framework', 'Cocoa', '-framework', 'SwiftUI'], check=True)
subprocess.run(['codesign', '--force', '--deep', '--sign', '-', str(app)], check=True)
print(app)
