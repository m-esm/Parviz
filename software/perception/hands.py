"""Hand gesture recognition without mediapipe python (no cp313 wheel):
runs the gesture_recognizer.task's own tflite models via LiteRT.

Pipeline: palm detector (192x192 SSD, anchors decoded here) -> rotated
hand crop -> hand landmarks (224x224, 21 points) -> GEOMETRIC gesture
classification (finger-extension states; the bundled embedder+classifier
needs mediapipe's private graph plumbing, geometry covers the canned set).

Gestures: open_palm, fist, thumbs_up, thumbs_down, pointing, victory,
none. All coordinates work in the rotated crop space where fingers-up is
-y, so the rules are orientation-safe.
"""

import math

import cv2
import numpy as np

DET_IN = 192
LM_IN = 224


def _anchors():
    """SSD anchor centers for mediapipe palm detection (full/lite):
    strides [8,16,16,16], 2 anchors at stride 8, 6 at 16, fixed size."""
    out = []
    for stride, per_cell in ((8, 2), (16, 6)):
        grid = DET_IN // stride
        for gy in range(grid):
            for gx in range(grid):
                cx, cy = (gx + 0.5) / grid, (gy + 0.5) / grid
                out.extend([(cx, cy)] * per_cell)
    return np.array(out, dtype=np.float32)   # (2016, 2)


class HandGesture:
    def __init__(self, det_path, lm_path):
        from ai_edge_litert.interpreter import Interpreter
        self.det = Interpreter(model_path=det_path, num_threads=2)
        self.det.allocate_tensors()
        self.lmk = Interpreter(model_path=lm_path, num_threads=2)
        self.lmk.allocate_tensors()
        self.anchors = _anchors()

    @staticmethod
    def _io(it):
        return (it.get_input_details()[0]["index"],
                [d["index"] for d in it.get_output_details()])

    def _detect_palm(self, bgr):
        """Best palm in a full BGR frame -> (cx, cy, size, rot) in frame
        pixels, or None. rot rotates fingers to point up."""
        h, w = bgr.shape[:2]
        side = max(h, w)
        sq = np.zeros((side, side, 3), np.uint8)
        sq[:h, :w] = bgr
        rgb = cv2.cvtColor(cv2.resize(sq, (DET_IN, DET_IN)),
                           cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        i, outs = self._io(self.det)
        self.det.set_tensor(i, rgb[None])
        self.det.invoke()
        reg = self.det.get_tensor(outs[0])[0]     # (2016, 18)
        score = self.det.get_tensor(outs[1])[0, :, 0]
        best = int(np.argmax(score))
        p = 1.0 / (1.0 + math.exp(-float(np.clip(score[best], -20, 20))))
        if p < 0.6:
            return None
        r = reg[best]
        acx, acy = self.anchors[best]
        cx = (r[0] / DET_IN + acx) * side
        cy = (r[1] / DET_IN + acy) * side
        bw = r[2] / DET_IN * side
        # keypoints 0 = wrist center, 2 = middle finger mcp
        k0 = ((r[4] / DET_IN + acx) * side, (r[5] / DET_IN + acy) * side)
        k2 = ((r[8] / DET_IN + acx) * side, (r[9] / DET_IN + acy) * side)
        rot = math.degrees(math.atan2(k2[1] - k0[1], k2[0] - k0[0])) + 90
        # palm box -> hand box: grow and shift toward the fingers
        size = bw * 2.6
        dx, dy = k2[0] - k0[0], k2[1] - k0[1]
        n = math.hypot(dx, dy) or 1.0
        cx += dx / n * bw * 0.5
        cy += dy / n * bw * 0.5
        return cx, cy, size, rot

    def _landmarks(self, bgr, palm):
        cx, cy, size, rot = palm
        m = cv2.getRotationMatrix2D((cx, cy), rot, 1.0)
        m[0, 2] += size / 2 - cx
        m[1, 2] += size / 2 - cy
        crop = cv2.warpAffine(bgr, m, (int(size), int(size)))
        crop = cv2.resize(crop, (LM_IN, LM_IN), interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB).astype(
            np.float32) / 255.0
        i, outs = self._io(self.lmk)
        self.lmk.set_tensor(i, rgb[None])
        self.lmk.invoke()
        lm = self.lmk.get_tensor(outs[0]).reshape(21, 3)
        logit = float(self.lmk.get_tensor(outs[1]).ravel()[0])
        presence = 1.0 / (1.0 + math.exp(-np.clip(logit, -20, 20)))
        return lm, presence

    @staticmethod
    def _classify(lm):
        """Finger-extension rules in the aligned crop (fingers up = -y)."""
        wrist = lm[0][:2]

        def ext(tip, pip):
            return (np.linalg.norm(lm[tip][:2] - wrist)
                    > np.linalg.norm(lm[pip][:2] - wrist) * 1.15)
        fingers = [ext(t, p) for t, p in
                   ((8, 6), (12, 10), (16, 14), (20, 18))]
        thumb = (np.linalg.norm(lm[4][:2] - lm[17][:2])
                 > np.linalg.norm(lm[2][:2] - lm[17][:2]) * 1.15)
        n = sum(fingers)
        if n == 4:
            return "open_palm"
        if n == 0:
            if thumb:
                # thumb clearly above or below the wrist -> up/down
                dy = lm[4][1] - wrist[1]
                span = abs(lm[12][1] - wrist[1]) or 1.0
                if dy < -0.4 * span:
                    return "thumbs_up"
                if dy > 0.4 * span:
                    return "thumbs_down"
            return "fist"
        if n == 1 and fingers[0]:
            return "pointing"
        if n == 2 and fingers[0] and fingers[1]:
            return "victory"
        return "none"

    def run(self, bgr):
        """Full frame BGR -> (gesture, presence) or ('none', 0.0)."""
        palm = self._detect_palm(bgr)
        if palm is None:
            return "none", 0.0
        lm, presence = self._landmarks(bgr, palm)
        if presence < 0.5:
            return "none", presence
        return self._classify(lm), presence
