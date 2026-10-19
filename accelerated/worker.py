#!/usr/bin/python3
"""One queued conversion; JSON progress on stdout, FFmpeg diagnostics in .log."""
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import fcntl
from pathlib import Path
import preview

child = None
cancelled = False

def emit(**data):
    print(json.dumps(data), flush=True)

def cancel(signum, frame):
    global cancelled
    cancelled = True
    if child is not None and child.poll() is None:
        child.terminate()

signal.signal(signal.SIGTERM, cancel)
signal.signal(signal.SIGINT, cancel)

def run(source):
    global child
    output = preview.destination(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(str(output) + '.lock', 'w') as lock:
        # Do not wait indefinitely behind a second application instance.
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Este arquivo já está sendo convertido em outra janela.')
        probe = subprocess.run([str(preview.FFMPEG), '-hide_banner', '-nostdin', '-i', str(source)], capture_output=True, text=True)
        match = re.search(r'Duration: (\d+):(\d+):(\d+(?:\.\d+)?)', probe.stderr)
        duration = sum(float(v) * factor for v, factor in zip(match.groups(), [3600, 60, 1])) if match else 0
        if cancelled:
            return 130
        fd, temp = tempfile.mkstemp(prefix='.' + output.stem, suffix='.mp4', dir=output.parent)
        os.close(fd)
        try:
            command = preview.command(source, temp)
            command[1:1] = ['-progress', 'pipe:1', '-nostats', '-stats_period', '0.25']
            emit(progress=0, output=str(output))
            with open(str(output) + '.log', 'w') as log:
                child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=log, text=True)
                if cancelled:
                    child.terminate()
                for line in child.stdout:
                    if line.startswith('out_time_us='):
                        try:
                            seconds = int(line.strip().split('=', 1)[1]) / 1e6
                            emit(progress=min(0.99, max(0, seconds / duration)) if duration else 0)
                        except ValueError:
                            pass
                code = child.wait()
            if cancelled:
                return 130
            if code:
                raise RuntimeError(f'Falha na conversão. Diagnóstico: {output}.log')
            os.replace(temp, output)
            emit(progress=1, output=str(output))
            return 0
        finally:
            Path(temp).unlink(missing_ok=True)

if __name__ == '__main__':
    try:
        sys.exit(run(Path(sys.argv[1])))
    except Exception as error:
        emit(error=str(error))
        sys.exit(1)
