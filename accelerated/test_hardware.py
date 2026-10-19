import sys
import preview, subprocess, time
from pathlib import Path
source=Path(sys.argv[1]).expanduser()
out=Path(__file__).with_name('hardware-scaled-sample.mp4')
start=time.monotonic()
r=subprocess.run(preview.command(source,out,20),capture_output=True,text=True)
Path(__file__).with_name('hardware-scaled.log').write_text(r.stderr)
print('Seconds:',round(time.monotonic()-start,2),'code:',r.returncode,'bytes:',out.stat().st_size)
if r.returncode: print(r.stderr[-3000:])
