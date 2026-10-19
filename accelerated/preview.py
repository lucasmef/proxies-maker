#!/usr/bin/python3
"""Finder Quick Action: small previews, preserving Source-relative folders."""
import argparse
import fcntl
import os
from pathlib import Path
import subprocess
import tempfile

BASE = Path(__file__).resolve().parent
SOURCE = (Path.home() / 'Movies/Vídeos/Source')
DEST = SOURCE.parent / 'Preview'
FFMPEG = BASE / 'bin/ffmpeg'


def destination(source):
    relative = source.resolve().relative_to(SOURCE.resolve())
    if not source.is_file() or source.suffix.lower() not in {'.mov', '.mp4', '.m4v'}:
        raise ValueError('Selecione um vídeo MOV, MP4 ou M4V dentro de Source.')
    return DEST / relative.parent / (relative.stem + '_preview.mp4')


def command(source, output, seconds=None):
    width, height, fps, rate = 320, 320, 8, '60k'
    # Bounding square accommodates portrait videos without stretching them.
    filters = f"fps={fps},scale_vt=w='trunc(iw*min({width}/iw,{height}/ih)/2)*2':h='trunc(ih*min({width}/iw,{height}/ih)/2)*2',setsar=1"
    args = [str(FFMPEG), '-hide_banner', '-nostdin', '-y', '-hwaccel', 'videotoolbox', '-hwaccel_output_format', 'videotoolbox_vld', '-i', str(source)]
    if seconds:
        args += ['-t', str(seconds)]
    return args + ['-map', '0:v:0', '-map', '0:a:0?', '-vf', filters,
                   '-c:v', 'h264_videotoolbox', '-allow_sw', '0', '-prio_speed', '1', '-b:v', rate,
                   '-maxrate', rate, '-bufsize', '280k',
                   '-c:a', 'copy', '-map_metadata', '-1', '-movflags', '+faststart', str(output)]


def convert(source, output, seconds=None, replace=False):
    output.parent.mkdir(parents=True, exist_ok=True)
    # Lock serializes simultaneous Finder actions on the same destination.
    with open(str(output) + '.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if output.exists() and not replace:
            return 'já existente'
        fd, temp = tempfile.mkstemp(prefix='.' + output.stem, suffix='.mp4', dir=output.parent)
        os.close(fd)
        try:
            with open(str(output) + '.log', 'w') as log:
                result = subprocess.run(command(source, temp, seconds), stdout=log, stderr=log)
            if result.returncode:
                raise RuntimeError(f'Falha na conversão. Veja {output}.log')
            os.replace(temp, output)
            return 'criado'
        finally:
            Path(temp).unlink(missing_ok=True)


def dialog(message):
    subprocess.run(['/usr/bin/osascript', '-e', 'on run argv', '-e',
                    'display dialog (item 1 of argv) with title "Criar Preview" buttons {"OK"} default button "OK"',
                    '-e', 'end run', message], check=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+', type=Path)
    parser.add_argument('--sample', type=float)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--tiny', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--replace', action='store_true')
    parser.add_argument('--gui', action='store_true')
    args = parser.parse_args()
    if args.output and len(args.files) != 1:
        parser.error('--output requer exatamente um arquivo')
    results, errors = [], []
    for source in args.files:
        try:
            output = args.output or destination(source)
            state = convert(source, output, args.sample, args.replace or args.gui)
            results.append(f'{output.name}: {state}')
        except Exception as error:
            errors.append(f'{source.name}: {error}')
    message = '\n'.join(results + errors)
    print(message)
    if args.gui:
        dialog(message)
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
