"""Supervise one Wyze Lake viewer and a local RTSP publisher."""

import argparse
import json
import os
import queue
import random
import re
import select
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

from protocol import WyzeAPI
from web_auth import WebSessionAuth

RUNTIME = Path(os.environ.get("WYZE_RUNTIME_DIR", "/tmp/wyze-lake"))
STOP = threading.Event()


def report(event, **fields):
    print(json.dumps(dict(event=event, **fields)), flush=True)


def stop_process(process):
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def checked(result):
    if result != 0:
        raise RuntimeError("SDK operation failed: " + str(result))


def sdk_service(app_id):
    from agora.rtc.agora_service import AgoraService
    from agora.rtc.agora_base import AgoraServiceConfig, AudioScenarioType

    service = AgoraService()
    checked(
        service.initialize(
            AgoraServiceConfig(
                appid=app_id,
                enable_video=1,
                enable_audio_device=0,
                audio_scenario=AudioScenarioType.AUDIO_SCENARIO_DEFAULT,
                log_path=str(RUNTIME / "agora.log"),
                data_dir=str(RUNTIME),
                config_dir=str(RUNTIME),
                log_file_size_kb=256,
            )
        )
    )
    return service


def publisher(url):
    # The SDK can report zero fps; arrival timestamps preserve variable frame rates.
    return subprocess.Popen(
        [
            "ffmpeg",
            "-hide_banner",
            "-v",
            "warning",
            "-probesize",
            "32768",
            "-analyzeduration",
            "1000000",
            "-use_wallclock_as_timestamps",
            "1",
            "-f",
            "hevc",
            "-i",
            "pipe:0",
            "-c:v",
            "copy",
            "-f",
            "rtsp",
            "-rtsp_transport",
            "tcp",
            url,
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
    )


def write_frame(process, frame):
    fd = process.stdin.fileno()
    os.set_blocking(fd, False)
    data = memoryview(frame)
    deadline = time.monotonic() + 5
    while data:
        if STOP.is_set() or process.poll() is not None or time.monotonic() > deadline:
            raise RuntimeError("RTSP publisher stopped or stalled")
        if select.select([], [fd], [], 0.25)[1]:
            try:
                data = data[os.write(fd, data) :]
            except BlockingIOError:
                continue


def viewer(url):
    from agora.rtc.agora_base import (
        RTCConnConfig,
        RtcConnectionPublishConfig,
        EncryptionConfig,
        VideoSubscriptionOptions,
        AudioScenarioType,
    )
    from agora.rtc.rtc_connection_observer import IRTCConnectionObserver
    from agora.rtc.video_encoded_frame_observer import IVideoEncodedFrameObserver

    web_auth = None
    if os.environ.get("WYZE_WEB_SESSION_FILE"):
        web_auth = WebSessionAuth(
            os.environ["WYZE_WEB_SESSION_FILE"], os.environ["WYZE_WEB_STATE"]
        )
    api = WyzeAPI(os.environ.get("WYZE_AUTH_STATE", "/tmp/unused"), web_auth)
    camera = api.camera(os.environ["WYZE_CAMERA_NAME"])
    uid = random.randint(30000, 60000)
    session, params, key, salt = api.session(camera, uid)
    service = sdk_service(session["app_id"])
    connection = None
    process = None
    frames = queue.Queue(maxsize=120)
    connected = threading.Event()
    failed = threading.Event()
    renew_needed = threading.Event()
    publishers = queue.Queue()

    class Observer(IRTCConnectionObserver):
        def on_connected(self, conn, info, reason):
            connected.set()

        def on_user_joined(self, conn, user_id):
            publishers.put(user_id)

        def on_connection_failure(self, conn, info, reason):
            failed.set()

        def on_disconnected(self, conn, info, reason):
            failed.set()

        def on_encryption_error(self, conn, error_type):
            failed.set()

        def on_token_privilege_will_expire(self, conn, token):
            renew_needed.set()

        def on_token_privilege_did_expire(self, conn):
            failed.set()

        def on_error(self, conn, error_code, error_msg):
            report("sdk_error", code=error_code)
            failed.set()

    class VideoObserver(IVideoEncodedFrameObserver):
        def on_encoded_video_frame(self, user_id, buffer, length, info):
            try:
                frames.put_nowait(
                    (
                        bytes(buffer[:length]),
                        int(info.codec_type),
                        info.width,
                        info.height,
                        info.frames_per_second,
                    )
                )
            except queue.Full:
                failed.set()
            return 1

    observer = Observer()
    video_observer = VideoObserver()
    try:
        connection = service.create_rtc_connection(
            RTCConnConfig(auto_subscribe_audio=0, auto_subscribe_video=0),
            RtcConnectionPublishConfig(
                is_publish_audio=False,
                is_publish_video=False,
                audio_scenario=AudioScenarioType.AUDIO_SCENARIO_DEFAULT,
            ),
        )
        checked(connection.register_observer(observer))
        checked(
            connection.enable_encryption(
                1,
                EncryptionConfig(
                    encryption_mode=7,
                    encryption_key=key,
                    encryption_kdf_salt=bytearray(salt),
                    datastream_encryption_enabled=False,
                ),
            )
        )
        checked(connection.register_video_encoded_frame_observer(video_observer))
        checked(
            connection.get_local_user().subscribe_all_video(
                VideoSubscriptionOptions(encodedFrameOnly=True)
            )
        )
        checked(
            connection.connect(
                session["rtc_token"], params["channel"], str(session["uid"])
            )
        )
        last_frame = time.monotonic()
        last_control = 0
        renewal_seconds = int(os.environ.get("WYZE_RENEW_SECONDS", "1800"))
        if not 30 <= renewal_seconds <= 1800:
            raise ValueError(
                "Token renewal interval must be between 30 and 1800 seconds"
            )
        next_renewal = last_frame + renewal_seconds
        last_report = last_frame
        count = 0
        while not STOP.is_set():
            now = time.monotonic()
            if failed.is_set() or now - last_frame > 30:
                raise RuntimeError("Viewer disconnected or video stalled")
            if connected.is_set() and now - last_control >= 10:
                controls = [
                    {
                        "cmd": "run_action",
                        "action": "sight-safe::check-user",
                        "params": {"userId": api.auth()["user_id"]},
                    },
                    {"cmd": "set_property", "props": {"camera::resolution": "360p"}},
                ]
                for control in controls:
                    checked(
                        connection.send_stream_message(
                            json.dumps(control, separators=(",", ":"))
                        )
                    )
                last_control = now
            while not publishers.empty():
                connection.send_intra_request(publishers.get_nowait())
            if renew_needed.is_set() or now >= next_renewal:
                checked(connection.renew_token(api.renew(camera, uid)))
                report("token_renewed")
                next_renewal = time.monotonic() + renewal_seconds
                renew_needed.clear()
            try:
                frame, codec, width, height, fps = frames.get(timeout=0.25)
            except queue.Empty:
                continue
            if codec != 3:
                raise RuntimeError("Expected H265 video")
            if process is None:
                process = publisher(url)
                report("video_started", width=width, height=height, fps=fps)
            write_frame(process, frame)
            last_frame = time.monotonic()
            (RUNTIME / "healthy").touch(mode=0o600)
            count += 1
            if now - last_report >= 30:
                report("video_progress", frames=count)
                last_report = now
    finally:
        (RUNTIME / "healthy").unlink(missing_ok=True)
        stop_process(process)
        if connection:
            connection.disconnect()
            connection.release()
        service.release()


def rtsp_server(stream, port):
    config = RUNTIME / "go2rtc.json"
    config.write_text(
        json.dumps(
            {
                "api": {"listen": "127.0.0.1:1984"},
                "rtsp": {"listen": ":" + str(port)},
                "webrtc": {"listen": ""},
                "streams": {stream: None},
                "log": {"level": "warn"},
            }
        )
    )
    process = subprocess.Popen(["go2rtc", "-config", str(config)])
    for _ in range(50):
        if process.poll() is not None:
            raise RuntimeError("RTSP server exited")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return process
        except OSError:
            STOP.wait(0.1)
    stop_process(process)
    raise RuntimeError("RTSP server did not start")


def supervise():
    auth_keys = (
        ("WYZE_WEB_SESSION_FILE", "WYZE_WEB_STATE")
        if os.environ.get("WYZE_WEB_SESSION_FILE")
        else ("WYZE_AUTH_STATE",)
    )
    for key in (*auth_keys, "WYZE_CAMERA_NAME"):
        if not os.environ.get(key):
            raise ValueError(key + " is required")
    stream = os.environ.get("WYZE_STREAM_NAME", "camera")
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", stream):
        raise ValueError("Invalid stream name")
    port = int(os.environ.get("WYZE_RTSP_PORT", "8554"))
    server = rtsp_server(stream, port)
    child = None
    url = f"rtsp://127.0.0.1:{port}/{stream}"
    delay = 1
    try:
        while not STOP.is_set():
            if server.poll() is not None:
                raise RuntimeError("RTSP server exited")
            (RUNTIME / "healthy").unlink(missing_ok=True)
            child = subprocess.Popen([sys.executable, __file__, "--viewer", url])
            started = time.monotonic()
            while not STOP.wait(1):
                if server.poll() is not None:
                    raise RuntimeError("RTSP server exited")
                if child.poll() is not None:
                    break
                health = RUNTIME / "healthy"
                heartbeat = health.stat().st_mtime if health.exists() else started
                elapsed = (
                    time.time() - heartbeat
                    if health.exists()
                    else time.monotonic() - started
                )
                if elapsed > 60:
                    report("viewer_watchdog")
                    stop_process(child)
                    break
            stop_process(child)
            if STOP.is_set():
                break
            report("viewer_retry", delay=delay)
            STOP.wait(delay)
            delay = 1 if time.monotonic() - started > 60 else min(delay * 2, 30)
    finally:
        stop_process(child)
        stop_process(server)
        (RUNTIME / "healthy").unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--viewer")
    parser.add_argument("--health", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if args.health:
        health = RUNTIME / "healthy"
        return 0 if health.exists() and time.time() - health.stat().st_mtime < 45 else 1
    RUNTIME.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(RUNTIME, 0o700)
    signal.signal(signal.SIGTERM, lambda *_: STOP.set())
    signal.signal(signal.SIGINT, lambda *_: STOP.set())
    if args.smoke:
        service = sdk_service("0" * 32)
        service.release()
        report("native_sdk_ready")
    elif args.viewer:
        viewer(args.viewer)
    else:
        supervise()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        # Exception text from HTTP/SDK libraries may contain account data.
        report("receiver_failed", error_type=type(error).__name__)
        sys.exit(1)
