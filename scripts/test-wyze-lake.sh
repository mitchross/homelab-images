#!/usr/bin/env bash
set -euo pipefail
image=${1:?image required}
runtime=(--rm --user 1000:1000 --read-only --network none
  --tmpfs /tmp:uid=1000,gid=1000 --tmpfs /home/wyze:uid=1000,gid=1000)
# SDK loading must work without a writable installation or network downloads.
docker run "${runtime[@]}" "$image" --smoke
if docker run "${runtime[@]}" "$image"; then
  echo 'Receiver unexpectedly started without authentication configuration' >&2
  exit 1
fi
if docker run "${runtime[@]}" "$image" --health; then
  echo 'Empty runtime unexpectedly reported healthy' >&2
  exit 1
fi
docker run -i "${runtime[@]}" --entrypoint python3 "$image" - <<'PY'
import os
import subprocess
import time
from pathlib import Path
from receiver import RUNTIME, publisher, rtsp_server, stop_process, write_frame

assert os.getuid() == 1000
RUNTIME.mkdir(mode=0o700)
server = rtsp_server('smoke', 8554)
publish = None
consumer = None
producer = None
try:
    # Generated frames exercise the same publisher and RTSP server without account secrets.
    producer = subprocess.Popen([
        'ffmpeg', '-v', 'error', '-re', '-f', 'lavfi', '-i', 'testsrc2=size=640x360:rate=15',
        '-t', '25', '-c:v', 'libx265', '-preset', 'ultrafast',
        '-x265-params', 'keyint=15:bframes=0:repeat-headers=1:pools=1:frame-threads=1:log-level=error',
        '-f', 'hevc', 'pipe:1',
    ], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    url = 'rtsp://127.0.0.1:8554/smoke'
    publish = publisher(url)
    os.set_blocking(producer.stdout.fileno(), False)
    started = time.monotonic()
    deadline = started + 35
    while time.monotonic() < deadline:
        try:
            data = os.read(producer.stdout.fileno(), 65536)
        except BlockingIOError:
            data = None
        if data:
            write_frame(publish, data)
        if consumer is None and time.monotonic() - started > 8:
            consumer = subprocess.Popen([
                'ffmpeg', '-v', 'error', '-rtsp_transport', 'tcp', '-i', url,
                '-frames:v', '75', '-progress', 'pipe:1', '-f', 'null', '-',
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if consumer is not None and consumer.poll() is not None:
            output, errors = consumer.communicate()
            counts = [int(s.split('=')[1]) for s in output.splitlines() if s.startswith('frame=')]
            assert consumer.returncode == 0 and counts and max(counts) >= 60, (output, errors)
            print('Generated H265 RTSP decode passed:', max(counts), 'frames')
            break
        time.sleep(0.01)
    else:
        raise RuntimeError('RTSP decode timed out')
finally:
    for process in (consumer, publish, producer, server):
        stop_process(process)
PY
echo 'Non-root fresh-home SDK loading, configuration validation, health gate, and RTSP decode passed.'
