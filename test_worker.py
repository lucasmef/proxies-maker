"""Integration checks using short synthetic media in an isolated source tree."""
import contextlib
import io
import tempfile
from pathlib import Path
import subprocess
import worker
import preview

with tempfile.TemporaryDirectory() as folder:
    root = Path(folder)
    preview.SOURCE = root/'Source'
    preview.DEST = root/'Preview'
    preview.STATE = root/'app-state'
    source = preview.SOURCE/'pasta com espaço'/'teste.mov'
    source.parent.mkdir(parents=True)
    subprocess.run([str(preview.FFMPEG), '-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=640x360:r=30', '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000', '-t', '2', '-c:v', 'libx264', '-c:a', 'aac', str(source)], check=True)
    stream=io.StringIO()
    with contextlib.redirect_stdout(stream):
        assert worker.run(source) == 0
    output=preview.destination(source)
    assert output.is_file()
    assert list(output.parent.iterdir()) == [output], 'Auxiliary files leaked into Preview'
    log_path, lock_path = preview.auxiliary_paths(output)
    assert log_path.is_file() and lock_path.is_file()
    # The CLI shares the same internal lock/log convention.
    assert preview.convert(source, output, replace=True) == 'criado'
    assert list(output.parent.iterdir()) == [output]
    assert '"progress": 1' in stream.getvalue()
    def audio_hash(path):
        return subprocess.check_output([str(preview.FFMPEG), '-v', 'error', '-i', str(path), '-map', '0:a:0', '-c:a', 'copy', '-f', 'hash', '-'])
    assert audio_hash(source)==audio_hash(output), 'AAC packets changed'
    subprocess.run([str(preview.FFMPEG), '-v', 'error', '-i', str(output), '-f', 'null', '-'], check=True)
    try:
        preview.destination(root/'outside.mov')
        raise AssertionError('Outside Source accepted')
    except ValueError:
        pass
    print('PASS: conversion, progress, nested paths, exact AAC packets, decoding and Source validation')
