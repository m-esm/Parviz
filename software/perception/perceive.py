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
import math
import os
import statistics
import time

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "models", "face_detection_yunet_2023mar.onnx")
LM_MODEL = os.path.join(HERE, "models", "face_landmarks_detector.tflite")
VISION_JSON = "/dev/shm/parviz_vision.json"
PREVIEW_JPG = "/dev/shm/parviz_preview.jpg"
COOL_ENTER = float(os.environ.get("PARVIZ_COOL_ENTER", 80.0))
COOL_EXIT = float(os.environ.get("PARVIZ_COOL_EXIT", 70.0))


def cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return int(f.read()) / 1000
    except OSError:
        return None

CAP_W, CAP_H = 640, 480
DET_W, DET_H = 320, 240
LOOP_HZ = 1.0        # detection rate; 1 Hz per user
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


class Landmarker:
    """MediaPipe face-landmarks tflite run directly via LiteRT (no
    mediapipe python: no cp313/aarch64 wheel). 478 x/y/z points in the
    256x256 aligned-crop space + face confidence."""

    def __init__(self, path=LM_MODEL):
        from ai_edge_litert.interpreter import Interpreter
        self.it = Interpreter(model_path=path, num_threads=2)
        self.it.allocate_tensors()
        self._in = self.it.get_input_details()[0]["index"]
        outs = self.it.get_output_details()
        self._lm = outs[0]["index"]
        self._conf = outs[1]["index"]

    def run(self, bgr256):
        rgb = cv2.cvtColor(bgr256, cv2.COLOR_BGR2RGB).astype(
            np.float32) / 255.0
        self.it.set_tensor(self._in, rgb[None])
        self.it.invoke()
        lm = self.it.get_tensor(self._lm).reshape(-1, 3)
        logit = float(self.it.get_tensor(self._conf).ravel()[0])
        return lm, 1.0 / (1.0 + math.exp(-logit))   # logit -> probability


def crop_align(bgr_full, face, sx, sy, out=256):
    """Rotate so the YuNet eye landmarks are horizontal, crop the face
    box with margin, resize to the landmark model's input."""
    x, y, w, h = [float(v) for v in face[:4]]
    le = (face[4] * sx, face[5] * sy)
    re = (face[6] * sx, face[7] * sy)
    ang = math.degrees(math.atan2(re[1] - le[1], re[0] - le[0]))
    cx, cy = (x + w / 2) * sx, (y + h / 2) * sy
    size = max(w * sx, h * sy) * 1.7
    m = cv2.getRotationMatrix2D((cx, cy), ang, 1.0)
    m[0, 2] += size / 2 - cx
    m[1, 2] += size / 2 - cy
    crop = cv2.warpAffine(bgr_full, m, (int(size), int(size)))
    return cv2.resize(crop, (out, out), interpolation=cv2.INTER_AREA)


def face_signals(lm):
    """Measurable expression signals from canonical facemesh indices.
    Aligned crop -> y is upright, so vertical geometry is meaningful."""
    def d(a, b):
        return float(np.linalg.norm(lm[a][:2] - lm[b][:2]))
    face_h = d(10, 152) or 1.0
    ear_l = (d(160, 144) + d(158, 153)) / (2 * (d(33, 133) or 1))
    ear_r = (d(385, 380) + d(387, 373)) / (2 * (d(362, 263) or 1))
    mouth_open = d(13, 14) / face_h
    width_ratio = d(61, 291) / (d(234, 454) or 1)
    # + when the mouth corners sit ABOVE the inner-lip midpoint
    corner_lift = (((lm[13][1] + lm[14][1]) / 2
                    - (lm[61][1] + lm[291][1]) / 2) / face_h)
    smile = max(0.0, min(1.0, (width_ratio - 0.40) * 5 + corner_lift * 14))
    brow_gap = ((lm[159][1] - lm[105][1]) +
                (lm[386][1] - lm[334][1])) / 2 / face_h
    return {"ear": round(float(ear_l + ear_r) / 2, 3),
            "eyes_closed": bool(ear_l < 0.16 and ear_r < 0.16),
            "mouth_open": round(float(mouth_open), 3),
            "smile": round(float(smile), 2),
            "corner_lift": round(float(corner_lift), 3),
            "brow_gap": round(float(brow_gap), 3)}


def classify(sig):
    """Signals -> a VISIBLE expression label (not a claim about feelings)."""
    if sig["eyes_closed"]:
        return "eyes_closed"
    if sig["mouth_open"] > 0.11 and sig["brow_gap"] > 0.10:
        return "surprised"
    if sig["smile"] > 0.4:
        return "happy"
    if sig["corner_lift"] < -0.022:
        return "sad"
    return "neutral"


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
    try:
        lmk = Landmarker()
    except Exception as e:      # LiteRT missing -> detection-only mode
        print(f"landmarker unavailable ({e}); detection only", flush=True)
        lmk = None
    try:
        from hands import HandGesture
        hnd = HandGesture(os.path.join(HERE, "models",
                                       "hand_detector.tflite"),
                          os.path.join(HERE, "models",
                                       "hand_landmarks_detector.tflite"))
    except Exception as e:
        print(f"hand gestures unavailable ({e})", flush=True)
        hnd = None
    period = 1.0 / hz
    last_prev = 0.0
    loop_n = 0
    last_hand = None
    lat = []
    t_start = time.monotonic()
    fps_t0, fps_n, fps = t_start, 0, 0.0
    print(f"perceive: yunet {DET_W}x{DET_H}, loop {hz} Hz", flush=True)
    cooling = False
    while True:
        t0 = time.monotonic()
        # thermal circuit breaker: no inference while the SoC is hot
        tc = cpu_temp()
        if cooling and tc is not None and tc <= COOL_EXIT:
            cooling = False
            print(f"cooled to {tc:.0f}C, resuming", flush=True)
        elif not cooling and tc is not None and tc >= COOL_ENTER:
            cooling = True
            print(f"cooling down at {tc:.0f}C, vision paused", flush=True)
        if cooling:
            write_atomic(VISION_JSON, json.dumps(
                {"ts": round(time.time(), 2), "cooling": True,
                 "person_present": False, "n_faces": 0, "fps": 0,
                 "infer_ms": 0}))
            time.sleep(2)
            continue
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
        st = interaction_state(faces, fps, infer_ms)
        if lmk is not None and faces:
            # crop + align the largest face, then landmarks -> signals
            f = max(faces, key=lambda f: f[2] * f[3])
            t2 = time.monotonic()
            crop = crop_align(bgr, f, CAP_W / DET_W, CAP_H / DET_H)
            lm, lconf = lmk.run(crop)
            if lconf > 0.5:
                sig = face_signals(lm)
                sig["visible_expression"] = classify(sig)
                sig["lm_ms"] = round((time.monotonic() - t2) * 1000, 1)
                st.update(sig)
        if hnd is not None and faces:
            # hands every OTHER tick (85 ms, the heaviest stage); carry
            # the last result so the brain's event key doesn't flap
            if loop_n % 2 == 0:
                t3 = time.monotonic()
                try:
                    g, gc = hnd.run(bgr)
                    last_hand = (g, round(float(gc), 2),
                                 round((time.monotonic() - t3) * 1000, 1))
                except Exception:
                    last_hand = None
            if last_hand:
                st["gesture"], st["gesture_conf"], st["hand_ms"] = last_hand
        loop_n += 1
        write_atomic(VISION_JSON, json.dumps(st))
        if t0 - last_prev >= PREVIEW_EVERY_S:
            last_prev = t0
            prev = cv2.resize(bgr, (160, 120), interpolation=cv2.INTER_AREA)
            ok, buf = cv2.imencode(".jpg", prev,
                                   [cv2.IMWRITE_JPEG_QUALITY, 70])
            if ok:
                write_atomic(PREVIEW_JPG, buf.tobytes())
        if bench_s and time.monotonic() - t_start >= bench_s:
            break
        # adaptive rate: 2 Hz while someone is here (fresh expression /
        # gesture signals), 0.5 Hz when the desk is empty
        period = (0.5 if faces else 2.0) if hz == LOOP_HZ else 1.0 / hz
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
        st = interaction_state(faces, 0, 0)
        if faces:
            try:
                lmk = Landmarker()
                crop = crop_align(img, max(faces, key=lambda f: f[2] * f[3]),
                                  1.0, 1.0)
                lm, lconf = lmk.run(crop)
                sig = face_signals(lm)
                sig["visible_expression"] = classify(sig)
                sig["lm_conf"] = round(lconf, 2)
                st.update(sig)
            except Exception as e:
                print(f"landmarker skipped: {e}")
        print(json.dumps(st, indent=1))
        return
    run(bench_s=args.bench, hz=args.hz)


if __name__ == "__main__":
    main()
