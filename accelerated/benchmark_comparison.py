import sys
import importlib.util
import json
import statistics
import subprocess
import time
from datetime import datetime
from pathlib import Path

root=Path(__file__).resolve().parent/'benchmark-idle'
root.mkdir(exist_ok=True)
modules={}
for label,app in [('antigo','Preview mínimo.app'),('novo','Preview mínimo acelerado.app')]:
    path=(Path.home() / 'Applications')/app/'Contents/Resources/preview.py'
    spec=importlib.util.spec_from_file_location(label,path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    modules[label]=module
sources=[Path(item).expanduser() for item in sys.argv[1:]]
if not sources:
    raise SystemExit('Informe um ou mais vídeos para comparar.')
rows=json.loads((root/'results.json').read_text()) if (root/'results.json').exists() else []
def other_ffmpeg():
    data=subprocess.check_output(['ps','-axo','pid,comm'],text=True)
    return [line.strip() for line in data.splitlines() if 'ffmpeg' in line.lower()]
for source in sources:
    for repeat,order in enumerate([['antigo','novo'],['novo','antigo']],1):
        for label in order:
            if any(r['source']==source.name and r['version']==label and r['repeat']==repeat for r in rows):
                continue
            out=root/f'{source.stem}-{label}-{repeat}.mp4'
            before=other_ffmpeg()
            start=time.perf_counter()
            with out.with_suffix('.log').open('w') as log:
                result=subprocess.run(modules[label].command(source,out,60),stdout=log,stderr=log)
            elapsed=time.perf_counter()-start
            row=dict(source=source.name,version=label,repeat=repeat,seconds=round(elapsed,3),bytes=out.stat().st_size if out.exists() else 0,exit_code=result.returncode,other_ffmpeg_before=before,other_ffmpeg_after=other_ffmpeg())
            rows.append(row)
            (root/'results.json').write_text(json.dumps(rows,indent=2))
            print(json.dumps(row),flush=True)
            if result.returncode: raise RuntimeError(f'Conversion failed: {out}')
summary={}
for source in sources:
    group={label:statistics.mean(r['seconds'] for r in rows if r['source']==source.name and r['version']==label) for label in modules}
    group['time_reduction_percent']=round((1-group['novo']/group['antigo'])*100,1)
    summary[source.name]=group
(root/'summary.json').write_text(json.dumps(summary,indent=2))
print('SUMMARY '+json.dumps(summary),flush=True)
