#!/usr/bin/env python3
"""Indefinite recording of 10-minute clips until MIN_FREE_GB or Ctrl-C.

Writes logs to /var/log/rpicam/rpicam.log when possible; otherwise falls back to
~/.local/state/rpicam/rpicam.log.
"""

import os
import shutil
import subprocess
import time
from datetime import datetime

MOUNT_POINT = "/media/user/disk"
VIDEO_DIR = f"{MOUNT_POINT}/videos"
FALLBACK_DIR = "/home/user/videos"
LOG_FILE = "/var/log/rpicam/rpicam.log"

# Camera settings
SEG_MS = "600000"  # 10 minutes (milliseconds)
FPS = "15"
BITRATE = "2000000"  # 2 Mbps

# Disk guard
MIN_FREE_GB = 100  # keep at least ~100GB free


def _open_log():
    """Open a binary, unbuffered log handle.

    Prefer LOG_FILE. If that path isn't writable, fall back to a user-writable
    location under ~/.local/state.
    """
    primary_dir = os.path.dirname(LOG_FILE)
    try:
        if primary_dir:
            os.makedirs(primary_dir, exist_ok=True)
        return open(LOG_FILE, "ab", buffering=0)
    except OSError:
        fallback = os.path.expanduser("~/.local/state/rpicam/rpicam.log")
        os.makedirs(os.path.dirname(fallback), exist_ok=True)
        return open(fallback, "ab", buffering=0)


def main():
    rpiVIDSec()


def rpiVIDSec():
    session_ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Choose output directory first. Do NOT create directories under the mount
    # point unless it is actually mounted (prevents writing to the root FS when
    # the external disk isn't mounted).
    out_dir = VIDEO_DIR if os.path.ismount(MOUNT_POINT) else FALLBACK_DIR
    os.makedirs(out_dir, exist_ok=True)

    seq = 0
    with _open_log() as log:
        log.write(f"\n=== Vid-Sec Started: {session_ts} ===\n".encode())
        log.write(f"OUT_DIR: {out_dir}\n".encode())

        try:
            while True:
                free_gb = shutil.disk_usage(out_dir).free / (1024**3)
                if free_gb < MIN_FREE_GB:
                    log.write(
                        f"\n=== STOP: low disk space ({free_gb:.2f} GB free < {MIN_FREE_GB} GB) ===\n".encode()
                    )
                    break

                clip_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                mp4 = f"{out_dir}/sec_{session_ts}_{seq:04d}_{clip_ts}.mp4"

                cmd = [
                    "rpicam-vid",
                    "--timeout",
                    SEG_MS,
                    "--nopreview",
                    "--codec",
                    "h264",
                    "--framerate",
                    FPS,
                    "--bitrate",
                    BITRATE,
                    "--intra",
                    FPS,
                    "--inline",
                    "-o",
                    mp4,
                ]

                log.write(f"\nCMD: {' '.join(cmd)}\n".encode())

                try:
                    subprocess.run(cmd, stdout=log, stderr=log, check=True)
                    seq += 1
                except FileNotFoundError:
                    log.write(
                        b"\n=== ERROR: rpicam-vid not found in PATH. Is it installed? Stopping. ===\n"
                    )
                    break
                except subprocess.CalledProcessError as e:
                    # Keep running on transient camera errors.
                    log.write(
                        f"\n=== WARN: rpicam-vid failed (exit {e.returncode}); retrying in 2s ===\n".encode()
                    )
                    time.sleep(2)

        except KeyboardInterrupt:
            log.write(b"=== Recording interrupted by user (Ctrl+C) ===\n")
            raise
        finally:
            end_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            log.write(
                f"=== Vid-Sec ended (session {session_ts}, ended {end_ts}) ===\n".encode()
            )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit(0)
