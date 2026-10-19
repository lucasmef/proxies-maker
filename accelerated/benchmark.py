import sys, time, subprocess, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import preview
source=Path(sys.argv[1]).expanduser()
results=[]
for kind in ['cpu','hardware']:
 out=Path(__file__).resolve().parent / (kind+'-sample.mp4')
 cmd=preview.command(source,out,20)
 if kind=='cpu':
  i=cmd.index('-hwaccel'); del cmd[i:i+2]
  i=cmd.index('-c:v'); cmd[i:i+6]=['-c:v','libx264','-preset','slow']
 start=time.monotonic()
 result=subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
 (out.with_suffix('.log')).write_text(result.stderr)
 results.append(dict(mode=kind,seconds=round(time.monotonic()-start,2),code=result.returncode,bytes=out.stat().st_size if out.exists() else 0))
 print(json.dumps(results[-1]),flush=True)
 if result.returncode: print(result.stderr[-2000:])
Path(__file__).with_name('benchmark-results.json').write_text(json.dumps(results,indent=2))
