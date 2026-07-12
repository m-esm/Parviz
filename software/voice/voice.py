"""Parviz voice daemon, stage 1: EARS with live captions.

Owns the microphone (currently the AirPods HFP source via pipewire's
pulse layer; the CM108 gooseneck ear mics slot in later), runs a
STREAMING local ASR (sherpa-onnx zipformer 20M int8; raw audio never
leaves the robot, docs/AWARENESS.md) and publishes what it hears to

  /dev/shm/parviz_speech.json   {"ts": ..., "partial": "as-you-speak",
                                 "final": "last finished utterance",
                                 "final_ts": ..., "level_db": ...}

CONTINUOUSLY: the mic is always open, there is no wake word (user:
Parviz stays engaged; attention is contextual, never command-gated).
The face renders partial as a live caption; the brain (next stage)
will treat a fresh final as an event that forces an immediate tick.

Run:   python3 voice.py            (daemon; also parviz-voice.service)
Test:  python3 voice.py --wav f.wav   decode a 16 kHz mono wav, print
"""

import argparse
import json
import math
import os
import queue
import subprocess
import threading
import time
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(
    HERE, "models", "sherpa-onnx-streaming-zipformer-en-20M-2023-02-17")
PIPER_MODEL = os.path.join(HERE, "models", "piper",
                           "en_US-lessac-medium.onnx")
SPEECH_JSON = "/dev/shm/parviz_speech.json"
DECISION_FILE = "/tmp/parviz_decision.json"
TTS_WAV = "/dev/shm/parviz_tts.wav"
RATE = 16000
CHUNK_S = 0.1


def make_recognizer():
    import sherpa_onnx
    return sherpa_onnx.OnlineRecognizer.from_transducer(
        tokens=os.path.join(MODEL_DIR, "tokens.txt"),
        encoder=os.path.join(MODEL_DIR, "encoder-epoch-99-avg-1.int8.onnx"),
        decoder=os.path.join(MODEL_DIR, "decoder-epoch-99-avg-1.onnx"),
        joiner=os.path.join(MODEL_DIR, "joiner-epoch-99-avg-1.int8.onnx"),
        num_threads=2,
        sample_rate=RATE,
        feature_dim=80,
        enable_endpoint_detection=True,
        # endpoint rules: trailing silence after speech (s) for rule2 is
        # the conversational one; 0.8 s feels responsive without cutting
        # slow speakers mid-sentence
        rule1_min_trailing_silence=2.4,
        rule2_min_trailing_silence=0.8,
        rule3_min_utterance_length=20.0,
        decoding_method="greedy_search",
    )


def write_atomic(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f)
    os.replace(tmp, path)


class Speaker:
    """Parviz's mouth: watches the brain's decision file and speaks NEW
    say actions through Piper into the default sink (the AirPods).
    While audio plays `speaking` is True and the capture loop keeps the
    ASR shut, so the robot never transcribes its own voice (half-duplex
    v0; webrtc AEC barge-in is the v2 upgrade). Cached decision replays
    never speak -- same rule as the face."""

    def __init__(self):
        self.speaking = False
        self.q = queue.Queue()
        self._voice = None
        self._last_say = time.time()
        try:   # only decisions NEWER than daemon start get a voice
            self._mt = os.path.getmtime(DECISION_FILE)
        except OSError:
            self._mt = 0.0
        threading.Thread(target=self._watch, daemon=True).start()
        threading.Thread(target=self._speak_loop, daemon=True).start()

    IDLE_UNLOAD_S = 600     # drop the ~160 MB piper model between
                            # conversations; reload costs ~2 s

    def _watch(self):
        while True:
            if (self._voice is not None and not self.speaking
                    and time.time() - self._last_say > self.IDLE_UNLOAD_S):
                self._voice = None      # GC frees the onnx session
                print("tts model unloaded (idle)", flush=True)
            try:
                mt = os.path.getmtime(DECISION_FILE)
                if mt != self._mt:
                    self._mt = mt
                    with open(DECISION_FILE) as f:
                        d = json.load(f)
                    if (not d.get("cached")
                            and time.time() - d.get("ts", 0) < 15):
                        for a in d.get("actions", []):
                            if (isinstance(a, dict)
                                    and a.get("do") == "say"
                                    and a.get("text")):
                                self.q.put(str(a["text"])[:300])
            except (OSError, ValueError):
                pass
            time.sleep(0.3)

    def synth(self, text):
        if self._voice is None:
            from piper import PiperVoice
            self._voice = PiperVoice.load(PIPER_MODEL)
        with wave.open(TTS_WAV, "wb") as w:
            try:
                self._voice.synthesize_wav(text, w)    # piper-tts >= 1.3
            except AttributeError:
                self._voice.synthesize(text, w)        # 1.2 api
        subprocess.run(["paplay", "--device=@DEFAULT_SINK@", TTS_WAV],
                       timeout=60, stderr=subprocess.DEVNULL)

    def _speak_loop(self):
        while True:
            text = self.q.get()
            self.speaking = True
            self._last_say = time.time()
            t0 = time.time()
            try:
                self.synth(text)
                print(f"spoke ({time.time() - t0:.1f}s): {text[:60]!r}",
                      flush=True)
            except Exception as e:
                print(f"tts failed: {e}", flush=True)
            finally:
                time.sleep(0.3)    # let the room settle before listening
                self.speaking = False


def decode_wav(path):
    """Offline check: run the streaming recognizer over a wav file."""
    rec = make_recognizer()
    s = rec.create_stream()
    with wave.open(path) as w:
        assert w.getframerate() == RATE and w.getnchannels() == 1, \
            "need 16 kHz mono"
        samples = np.frombuffer(w.readframes(w.getnframes()),
                                np.int16).astype(np.float32) / 32768.0
    s.accept_waveform(RATE, samples)
    s.accept_waveform(RATE, np.zeros(int(RATE * 0.8), np.float32))
    while rec.is_ready(s):
        rec.decode_stream(s)
    return rec.get_result(s)


def run():
    rec = make_recognizer()
    spk = Speaker()
    print("voice: recognizer + speaker up, capturing", flush=True)
    stream = rec.create_stream()
    final, final_ts = "", 0.0
    nbytes = int(RATE * CHUNK_S) * 2
    # ENERGY GATE: the zipformer encoder costs ~40% of a core if it runs
    # on silence too. Only decode while the room is louder than GATE_DB
    # or within HANG_S of the last loud chunk (sentence tails, pauses).
    # The mic itself STAYS OPEN the whole time -- gating is about CPU,
    # not attention; Parviz remains continuously engaged.
    GATE_DB = -48.0
    HANG_S = 2.0
    loud_until = 0.0
    while True:
        proc = subprocess.Popen(
            ["parec", "--device=@DEFAULT_SOURCE@", "--format=s16le",
             f"--rate={RATE}", "--channels=1", "--latency-msec=100"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            while True:
                buf = proc.stdout.read(nbytes)
                if len(buf) < nbytes:
                    break
                x = np.frombuffer(buf, np.int16).astype(np.float32)
                rms = float(np.sqrt(np.mean(x * x))) + 1e-6
                db = 20 * math.log10(rms / 32768.0)
                now = time.time()
                if spk.speaking:
                    # HALF-DUPLEX: our own voice is playing; drop any
                    # in-flight partial and keep the gate shut
                    if rec.get_result(stream):
                        rec.reset(stream)
                    loud_until = 0.0
                    write_atomic(SPEECH_JSON, {
                        "ts": round(now, 2), "partial": "",
                        "final": final, "final_ts": round(final_ts, 2),
                        "level_db": round(db, 1), "speaking": True,
                    })
                    continue
                if db > GATE_DB:
                    loud_until = now + HANG_S
                partial = ""
                if now < loud_until:
                    stream.accept_waveform(RATE, x / 32768.0)
                    while rec.is_ready(stream):
                        rec.decode_stream(stream)
                    partial = rec.get_result(stream).lower()
                    if rec.is_endpoint(stream):
                        if partial.strip():
                            final, final_ts = partial.strip(), now
                            print(f"heard: {final!r}", flush=True)
                        rec.reset(stream)
                        partial = ""
                else:
                    # gate just closed with an utterance still pending
                    # (endpoint 0.8 s normally beats the 2 s hangover;
                    # this is the safety net): finalize it
                    pend = rec.get_result(stream).lower().strip()
                    if pend:
                        final, final_ts = pend, now
                        print(f"heard (gate): {final!r}", flush=True)
                        rec.reset(stream)
                write_atomic(SPEECH_JSON, {
                    "ts": round(now, 2),
                    "partial": partial,
                    "final": final,
                    "final_ts": round(final_ts, 2),
                    "level_db": round(db, 1),
                    "speaking": False,
                })
        finally:
            try:
                proc.kill()
            except OSError:
                pass
        print("voice: capture died, retrying in 3 s", flush=True)
        time.sleep(3)


def main():
    os.environ.setdefault("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    ap = argparse.ArgumentParser()
    ap.add_argument("--wav", default=None,
                    help="decode a 16 kHz mono wav and print the text")
    ap.add_argument("--say", default=None,
                    help="speak a line through the default sink and exit")
    args = ap.parse_args()
    if args.wav:
        print(repr(decode_wav(args.wav)))
        return
    if args.say:
        sp = object.__new__(Speaker)   # no watcher threads, just synth
        sp._voice = None
        sp.synth(args.say)
        return
    run()


if __name__ == "__main__":
    main()
