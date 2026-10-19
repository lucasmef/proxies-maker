import sys
import importlib.util, json, subprocess, time
from pathlib import Path
base=Path(__file__).resolve().parent
results=[]
for mode,path in [('cpu',base.parent/'preview.py'),('hardware',base/'preview.py')]:
 spec=importlib.util.spec_from_file_location(mode,path); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
 out=base/(mode+'-60s.mp4')
 start=time.monotonic()
 result=subprocess.run(module.command(Path(sys.argv[1]).expanduser(),out,60),capture_output=True,text=True)
 out.with_suffix('.log').write_text(result.stderr)
 row=dict(mode=mode,seconds=round(time.monotonic()-start,2),returncode=result.returncode,bytes=out.stat().st_size)
 results.append(row); print(json.dumps(row),flush=True)
(base/'comparison.json').write_text(json.dumps(results,indent=2))
