import plistlib
from pathlib import Path
import uuid
base = Path(__file__).resolve().parent
original = base / 'Criar Preview mínimo.workflow/Contents'
out = base / 'Criar Preview mínimo.workflow/Contents'
out.mkdir(parents=True, exist_ok=True)
with open(original / 'document.wflow', 'rb') as f:
    doc = plistlib.load(f)
action = doc['actions'][0]['action']
action['ActionParameters']['COMMAND_STRING'] = '/usr/bin/open -a "$HOME/Applications/Preview mínimo.app" "$@"'
for key in ['InputUUID', 'OutputUUID', 'UUID']:
    action[key] = str(uuid.uuid4()).upper()
for key in ['inputTypeIdentifier', 'serviceInputTypeIdentifier']:
    doc['workflowMetaData'][key] = 'com.apple.Automator.fileSystemObject.movie'
with open(out / 'document.wflow', 'wb') as f:
    plistlib.dump(doc, f)
info = {'CFBundleIdentifier': 'local.lucas.criar-preview-minimo', 'CFBundleName': 'Criar Preview mínimo',
        'NSServices': [{'NSMenuItem': {'default': 'Criar Preview mínimo'},
                        'NSMessage': 'runWorkflowAsService',
                        'NSSendFileTypes': ['public.movie'],
                        'NSRequiredContext': {'NSApplicationIdentifier': 'com.apple.finder'}}]}
with open(out / 'Info.plist', 'wb') as f:
    plistlib.dump(info, f)
