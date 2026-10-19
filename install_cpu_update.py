from pathlib import Path
import fcntl
import json
import shutil
import subprocess
import unicodedata
import uuid
import preview

base=Path(__file__).resolve().parent
apps=Path.home()/'Applications'
old=apps/'Preview mínimo.app'
accelerated=apps/'Preview mínimo acelerado.app'
register='/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister'
processes=subprocess.check_output(['ps','-axo','comm'],text=True)
if any('PreviewMinimo' in line or line.strip().endswith('/ffmpeg') for line in processes.splitlines()):
    raise RuntimeError('App ou conversão em andamento. Nenhuma mudança aplicada.')
files=[p for p in preview.DEST.rglob('*') if p.is_file() and not p.is_symlink() and (p.name.endswith('_preview.mp4.log') or p.name.endswith('_preview.mp4.lock'))]
handles=[]
try:
    for p in files:
        if p.suffix=='.lock':
            handle=p.open('a')
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            handles.append(handle)
    migrated=[]
    for p in files:
        output=Path(str(p)[:-len(p.suffix)])
        log, lock=preview.auxiliary_paths(output)
        target=log if p.suffix=='.log' else lock
        if target.exists():
            target=target.with_name(target.stem+'-migrated-'+uuid.uuid4().hex+target.suffix)
        shutil.move(str(p),str(target))
        migrated.append({'from':str(p),'to':str(target)})
    preview.STATE.mkdir(parents=True,exist_ok=True)
    (preview.STATE/('migration-'+uuid.uuid4().hex+'.json')).write_text(json.dumps(migrated,ensure_ascii=False,indent=2))
    subprocess.run(['ditto',str(base/'Preview mínimo.app'),str(old)],check=True)
    subprocess.run(['codesign','--verify','--deep','--strict',str(old)],check=True)
    if accelerated.exists():
        subprocess.run([register,'-u',str(accelerated)],check=True)
        shutil.rmtree(accelerated)
    subprocess.run([register,'-f',str(old)],check=True)
    subprocess.run([register,'-u',str(base/'Preview mínimo.app')],check=True)
    print(json.dumps({'moved_auxiliary_files':len(migrated),'cpu_app_installed':old.exists(),'accelerated_app_removed':not accelerated.exists()},ensure_ascii=False))
finally:
    for handle in handles:
        handle.close()
