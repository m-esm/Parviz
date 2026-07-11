"""Parviz perception daemon: YuNet face detection -> interaction state.

Tier-1 vision (docs/AWARENESS.md): owns the camera (the ONLY process that
does), runs OpenCV's YuNet face detector continuously, and publishes:

  /dev/shm/parviz_vision.json   interaction state for the brain digest +
                                the face's person-following gaze, atomic
                                (tmp+rename), every loop (~15 Hz)
  /dev/shm/parviz_preview.jpg   160x120 preview for the face's CAM window
                                (~3 Hz; the face process must NOT open the
                                camera itself)

State format (user's vision research, interaction state over raw labels):
  {"ts": ..., "person_present": true, "n_faces": 1, "conf": 0.93,
   "cx": -0.31, "cy": 0.05,        # face center, -1..1, +x = frame right
   "size": 0.18,                    # face width / frame width
   "facing_camera": true,           # eye-to-nose symmetry heuristic
   "pan_deg": -19.0, "tilt_deg": 2.0,  # where the HEAD would aim
   "fps": 14.8, "infer_ms": 9.2}

Camera x is MIRRORED into robot frame: the imx708 sees the world, the
face's pan is defined viewer-right-positive (steppers.py), so a person on
the robot's left (frame right) gets negative cx/pan.

Run:    python3 perceive.py            # daemon loop
Bench:  python3 perceive.py --bench 30 # research-format numbers, then exit
Test:   python3 perceive.py --image f.jpg   # one-shot detector check
"""

import argparse
import json
import os
import statistics
import time

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "models", "face_detection_yunet_2023mar.onnx")
VISION_JSON = "/dev/shm/parviz_vision.json"
PREVIEW_JPG = "/dev/shm/parviz_preview.jpg"

CAP_W, CAP_H = 640, 480
DET_W, DET_H = 320, 240
LOOP_HZ = 2.0        # detection rate; 2 Hz is plenty for desk presence
PREVIEW_EVERY_S = 0.5
# imx708 video-mode FOV, approximate; refine when the head is mounted.
FOV_X_DEG, FOV_Y_DEG = 62.0, 48.0


def make_detector():
    det = cv2.FaceDetectorYN_create(MODEL, "", (DET_W, DET_H),
                                    score_threshold=0.6, nms_threshold=0.3,
                                    top_k=8)
    return det


def detect(det, bgr_det):
    """Run YuNet on a DET_WxDET_H BGR frame -> list of faces
    [x,y,w,h, ...5 landmark pairs..., score] in detector pixels."""
    _, faces = det.detect(bgr_det)
    return [] if faces is None else list(faces)


def interaction_state(faces, fps, infer_ms):
    st = {"ts": round(time.time(), 2), "person_present": False,
          "n_faces": len(faces), "fps": round(fps, 1),
          "infer_ms": round(infer_ms, 1)}
    if not faces:
        return st
    f = max(faces, key=lambda f: f[2] * f[3])   # largest face
    x, y, w, h = f[:4]
    conf = float(f[14])
    # normalized center, robot frame: +x = robot right = frame LEFT
    cx = -((x + w / 2) / DET_W * 2 - 1)
    cy = (y + h / 2) / DET_H * 2 - 1
    # facing heuristic: nose x between the eyes, roughly centered
    le_x, re_x, nose_x = f[4], f[6], f[8]
    span = abs(re_x - le_x)
    facing = bool(span > 4 and
                  abs(nose_x - (le_x + re_x) / 2) < span * 0.45)
    st.update(person_present=True, conf=round(conf, 2),
              cx=round(float(cx), 3), cy=round(float(cy), 3),
              size=round(float(w / DET_W), 3), facing_camera=facing,
              pan_deg=round(float(cx * FOV_X_DEG / 2), 1),
              tilt_deg=round(float(-cy * FOV_Y_DEG / 2), 1),
              box=[int(x), int(y), int(w), int(h)])   # raw, det pixels
    return st


def write_atomic(path, data):
    tmp = path + ".tmp"
    mode = "wb" if isinstance(data, bytes) else "w"
    with open(tmp, mode) as f:
        f.write(data)
    os.replace(tmp, path)


def run(bench_s=None, hz=LOOP_HZ):
    from picamera2 import Picamera2
    cam = Picamera2()
    cam.configure(cam.create_video_configuration(
        main={"size": (CAP_W, CAP_H), "format": "BGR888"}))
    cam.start()
    det = make_detector()
    period = 1.0 / hz
    last_prev = 0.0
    lat = []
    t_start = time.monotonic()
    fps_t0, fps_n, fps = t_start, 0, 0.0
    print(f"perceive: yunet {DET_W}x{DET_H}, loop {hz} Hz", flush=True)
    while True:
        t0 = time.monotonic()
        frame = cam.capture_array()                    # RGB-ordered
        bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        small = cv2.resize(bgr, (DET_W, DET_H), interpolation=cv2.INTER_AREA)
        t1 = time.monotonic()
        faces = detect(det, small)
        infer_ms = (time.monotonic() - t1) * 1000
        lat.append(infer_ms)
        if len(lat) > 600:
            del lat[:300]
        fps_n += 1
        if t0 - fps_t0 >= 2.0:
            fps = fps_n / (t0 - fps_t0)
            fps_t0, fps_n = t0, 0
        write_atomic(VISION_JSON,
                     json.dumps(interaction_state(faces, fps, infer_ms)))
        if t0 - last_prev >= PREVIEW_EVERY_S:
            last_prev = t0
            prev = cv2.resize(bgr, (160, 120), interpolation=cv2.INTER_AREA)
            ok, buf = cv2.imencode(".jpg", prev,
                                   [cv2.IMWRITE_JPEG_QUALITY, 70])
            if ok:
                write_atomic(PREVIEW_JPG, buf.tobytes())
        if bench_s and time.monotonic() - t_start >= bench_s:
            break
        time.sleep(max(0.0, period - (time.monotonic() - t0)))
    if bench_s:
        rss = 0
        try:
            with open("/proc/self/status") as f:
                for line in f:
                    if line.startswith("VmRSS"):
                        rss = int(line.split()[1]) // 1024
        except OSError:
            pass
        temp = "--"
        try:
            with open("/sys/class/thermal/thermal_zone0/temp") as f:
                temp = int(f.read()) // 1000
        except OSError:
            pass
        med = statistics.median(lat)
        p95 = sorted(lat)[int(len(lat) * 0.95)]
        print("model,resolution,fps,med_ms,p95_ms,ram_mb,cpu_temp")
        print(f"yunet,{DET_W}x{DET_H},{fps:.1f},{med:.1f},{p95:.1f},"
              f"{rss},{temp}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", type=float, default=None, metavar="SECONDS")
    ap.add_argument("--hz", type=float, default=LOOP_HZ,
                    help=f"detection rate (default {LOOP_HZ})")
    ap.add_argument("--image", default=None,
                    help="one-shot: detect faces in an image file, print")
    args = ap.parse_args()
    if args.image:
        det = make_detector()
        img = cv2.imread(args.image)
        img = cv2.resize(img, (DET_W, DET_H))
        faces = detect(det, img)
        print(f"{len(faces)} face(s)")
        for f in faces:
            print(f"  box=({f[0]:.0f},{f[1]:.0f},{f[2]:.0f},{f[3]:.0f}) "
                  f"score={f[14]:.2f}")
        print(json.dumps(interaction_state(faces, 0, 0), indent=1))
        return
    run(bench_s=args.bench, hz=args.hz)


if __name__ == "__main__":
    main()
