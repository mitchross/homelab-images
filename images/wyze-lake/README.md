# Wyze Lake receiver

Receive Cam Pan v4 video with Agora's native Linux SDK. Publish H265 video through a local go2rtc RTSP server.

```mermaid
flowchart LR
  Bridge[Wyze Bridge login] -->|read-only auth state| Receiver[Linux Lake receiver]
  Web[Official Web View login] -->|session seed| Refresh[Cookie and token refresh]
  Refresh -->|private persistent state| Receiver
  Camera[Cam Pan v4] -->|encrypted Agora video| Receiver
  Receiver --> FFmpeg --> go2rtc --> RTSP[RTSP consumer]
```

This image receives video. Use Wyze Bridge's authentication file or an official Web View session.
Web View mode refreshes account tokens and persists the returned session cookie. It takes priority when configured.
Find deployment manifests in [talos-argocd-proxmox](https://github.com/mitchross/talos-argocd-proxmox/tree/main/my-apps/home-automation/wyze-bridge).

## Build and test

Run these commands from the repository root:

```sh
docker build --platform linux/amd64 -t wyze-lake:local images/wyze-lake
bash scripts/test-wyze-lake.sh wyze-lake:local
```

The test loads the native SDK without network access. It decodes generated H265 video through RTSP.
It checks session rotation, restart recovery, Secret updates, token rejection, and refresh backoff with simulated responses.
The test uses UID 1000, an empty home, and a read-only root filesystem.
It does not contact a camera or prove account authentication.

The workflow builds and tests before publishing an immutable revision tag.
Copy the published digest from its job summary for deployment review.

## Runtime contract

| Setting | Requirement |
| --- | --- |
| `WYZE_AUTH_STATE` | Path to Wyze Bridge's JSON state file, mounted read-only. Required unless Web View mode is configured. |
| `WYZE_WEB_SESSION_FILE` | Optional path to a read-only file containing the `services.wyze.com` cookie named `session`. |
| `WYZE_WEB_STATE` | Private JSON state path on writable persistent storage. Required with `WYZE_WEB_SESSION_FILE`. |
| `WYZE_CAMERA_NAME` | Required camera nickname. The name must identify exactly one Cam Pan v4. |
| `WYZE_STREAM_NAME` | RTSP stream name. Default: `camera`. Use letters, numbers, underscores, or hyphens. |
| `WYZE_RTSP_PORT` | RTSP TCP listen port. Default: `8554`. |
| `WYZE_RUNTIME_DIR` | Writable directory for SDK logs, config, and heartbeat. Default: `/tmp/wyze-lake`. |
| `WYZE_RENEW_SECONDS` | Viewer token renewal interval. Default: 1800 seconds. Allowed range: 30–1800. |

The authentication file contains account access and refresh tokens. Keep it outside the image and build context.
Mount its containing directory so atomic file replacements remain visible. UID 1000 must have read access.
The receiver discovers the camera through Wyze's API. It needs no HAR file or saved camera identifiers.
In Bridge mode, it reads the authentication file again for each API call. Wyze Bridge must keep that file current.

In Web View mode, obtain the seed from a successful login at [my.wyze.com](https://my.wyze.com).
The developer portal's OAuth token lacks camera permissions. Use the Web View service session cookie.
Mount the seed's directory read-only so projected Secret replacements remain visible.
The receiver detects changed seed content without restarting the pod.
It refreshes account authentication hourly, before token expiry, and after a camera API returns HTTP 401.
It saves the renewed cookie and token atomically with mode 0600 inside a mode 0700 directory.
Keep that directory across receiver and pod replacements. UID 1000 must own the state files.
Point `WYZE_WEB_STATE` into a private child directory of the persistent mount, such as `/session/web/state.json`.
The original seed stays unchanged; subsequent refreshes use the persisted cookie.
Failed refreshes retain a usable token during brief outages. Revoked sessions require a new browser login.
Refresh failures use persistent backoff, including across process restarts. Tokens and cookies never appear in application logs.
This refresh protocol is undocumented. A successful refresh does not establish indefinite session validity.

Mount writable temporary storage at `/tmp`. Mount an empty writable home at `/home/wyze` when using a read-only filesystem.
Keep SDK logs private. The receiver creates its runtime directory with mode 0700.
Allow outbound HTTPS and the Agora SDK's network traffic.
RTSP has no authentication in this image. Restrict access through the deployment's network policy.
The go2rtc API listens on loopback only. WebRTC is disabled.

Read video at `rtsp://<receiver>:<port>/<stream>` over TCP.
Run `python3 /opt/wyze-lake/receiver.py --health` for the encoded-video heartbeat check.
The health check reports recent writes to the publisher. It does not prove consumer decoding.

## Recovery and limits

The receiver renews the viewer token and sends camera authorization controls every ten seconds.
It starts a fresh viewer after disconnects, queue overflow, or stalled video.
Retries use a delay of up to 30 seconds. A parent watchdog stops a viewer that stops updating its heartbeat.

Initial support is video-only, at 640×360. Only Cam Pan v4 with model `HL_PAN4` has been tested.
H265 browser playback depends on the consumer. Consumers can report missing references until the next keyframe after joining.
FFmpeg can correct timestamps during publisher startup. Live decoding was verified after startup and reconnects.
The image currently supports Linux amd64 only. It uses Wyze's undocumented web protocol, which can change.
No Android device is required.

## Update

Update pinned versions, URLs, image digests, and SHA256 values in the Dockerfile.
Keep the native SDK URL aligned with the Python wrapper's expected version file.
Rebuild the image. Run the image test with fresh storage.
Verify live decoding, token renewal, and reconnects with an authorized camera before changing deployment manifests.

Protocol references: [Agora Python SDK](https://github.com/AgoraIO-Extensions/Agora-Python-Server-SDK),
[go2rtc](https://github.com/AlexxIT/go2rtc), and Wyze's public client at [my.wyze.com](https://my.wyze.com).
