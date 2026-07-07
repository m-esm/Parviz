"""desk-pi camera check: grab ONE frame, report resolution, exit.

Camera: Raspberry Pi Camera Module 3 (imx708, 4608x2592) on CSI.
Prefers Picamera2 (python3-picamera2, preinstalled on Raspberry Pi OS);
falls back to the rpicam-still CLI. No deps beyond the OS packages,
JPEG dimensions are parsed from the SOF marker, no PIL needed.

Run on the Pi:   python3 preview.py [--out /tmp/desk_pi_cam.jpg]
Exit codes: 0 = frame captured + resolution printed, 1 = no camera stack,
2 = capture failed.
"""

import argparse
import os
import shutil
import struct
import subprocess
import sys

DEFAULT_OUT = "/tmp/desk_pi_cam.jpg"


def jpeg_dimensions(path):
    """(width, height) from a JPEG's SOF0/SOF2 marker. None if unparseable."""
    with open(path, "rb") as f:
        if f.read(2) != b"\xff\xd8":
            return None
        while True:
            b = f.read(1)
            if not b:
                return None
            if b != b"\xff":
                continue
            marker = f.read(1)
            if not marker or marker in (b"\xff", b"\x00"):
                continue
            m = marker[0]
            if 0xD0 <= m <= 0xD9:  # RST/SOI/EOI: no length field
                continue
            (seg_len,) = struct.unpack(">H", f.read(2))
            if m in (0xC0, 0xC1, 0xC2, 0xC3):  # SOF: baseline/progressive
                data = f.read(5)
                h, w = struct.unpack(">HH", data[1:5])
                return (w, h)
            f.seek(seg_len - 2, os.SEEK_CUR)


def capture_picamera2(out):
    from picamera2 import Picamera2  # noqa: import inside, Pi-only
    cam = Picamera2()
    try:
        cfg = cam.create_still_configuration()
        cam.configure(cfg)
        cam.start()
        cam.capture_file(out)
    finally:
        cam.close()
    return "picamera2"


def capture_rpicam(out):
    exe = shutil.which("rpicam-still") or shutil.which("libcamera-still")
    if not exe:
        raise FileNotFoundError("neither rpicam-still nor libcamera-still")
    subprocess.run(
        [exe, "-o", out, "-n", "--immediate", "-t", "1"],
        check=True, capture_output=True, timeout=30,
    )
    return os.path.basename(exe)


def main(argv=None):
    ap = argparse.ArgumentParser(description="single-frame camera check")
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    backend = None
    try:
        backend = capture_picamera2(args.out)
    except ImportError:
        try:
            backend = capture_rpicam(args.out)
        except FileNotFoundError:
            print("FAIL: no camera stack (picamera2 missing, no rpicam-still)",
                  file=sys.stderr)
            return 1
        except subprocess.CalledProcessError as e:
            print(f"FAIL: rpicam-still exited {e.returncode}: "
                  f"{e.stderr.decode(errors='replace')[-400:]}",
                  file=sys.stderr)
            return 2
    except Exception as e:
        print(f"FAIL: picamera2 capture error: {e}", file=sys.stderr)
        return 2

    if not os.path.exists(args.out) or os.path.getsize(args.out) == 0:
        print("FAIL: capture produced no file", file=sys.stderr)
        return 2
    dims = jpeg_dimensions(args.out)
    size_kb = os.path.getsize(args.out) // 1024
    res = f"{dims[0]}x{dims[1]}" if dims else "unknown (SOF not found)"
    print(f"OK: {args.out} ({size_kb} KB) via {backend}, resolution {res}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
