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
import collections
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
MOONSHINE_DIR = os.path.join(
    HERE, "models", "sherpa-onnx-moonshine-base-en-int8")
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


class QualityPass:
    """Second ASR pass: the 20M streaming model is fast but mangles
    words (user verdict: not good enough), so each FINISHED utterance
    is re-decoded by Moonshine base (proper casing/punctuation, far
    better vocabulary; still 100% local). The streaming result stays
    on screen as the live caption and becomes the fallback if this
    pass fails. Runs in its own thread; a 4 s utterance costs ~1 s."""

    def __init__(self, shared):
        import sherpa_onnx
        self.rec = sherpa_onnx.OfflineRecognizer.from_moonshine(
            preprocessor=os.path.join(MOONSHINE_DIR, "preprocess.onnx"),
            encoder=os.path.join(MOONSHINE_DIR, "encode.int8.onnx"),
            uncached_decoder=os.path.join(MOONSHINE_DIR,
                                          "uncached_decode.int8.onnx"),
            cached_decoder=os.path.join(MOONSHINE_DIR,
                                        "cached_decode.int8.onnx"),
            tokens=os.path.join(MOONSHINE_DIR, "tokens.txt"),
            num_threads=2,
        )
        self.q = queue.Queue()
        self.shared = shared
        threading.Thread(target=self._loop, daemon=True).start()

    def submit(self, samples, fallback):
        self.q.put((samples, fallback))

    def _loop(self):
        while True:
            samples, fallback = self.q.get()
            t0 = time.time()
            text = ""
            try:
                s = self.rec.create_stream()
                s.accept_waveform(RATE, samples)
                self.rec.decode_stream(s)
                text = s.result.text.strip()
            except Exception as e:
                print(f"quality pass failed: {e}", flush=True)
            text = text or fallback
            if text:
                self.shared["final"] = text
                self.shared["final_ts"] = time.time()
                print(f"heard ({time.time() - t0:.1f}s): {text!r}",
                      flush=True)


def _pactl_names(kind):
    try:
        out = subprocess.run(["pactl", "list", "short", kind],
                             capture_output=True, text=True,
                             timeout=5).stdout
        return [line.split("\t")[1] for line in out.splitlines()
                if "\t" in line]
    except (OSError, subprocess.SubprocessError, IndexError):
        return []


def find_mic_source():
    """The bluetooth mic, coaxed into existence if needed.

    Freshly reconnected AirPods land in the a2dp profile (output only,
    NO input node) -- that is why 'out and back in' used to go deaf:
    @DEFAULT_SOURCE@ resolved to nothing useful and stayed there. If a
    bluez card exists without its input, flip it to the headset profile
    and wait for the mic node. Falls back to the default source."""
    for s in _pactl_names("sources"):
        if s.startswith("bluez_input"):
            return s
    for card in _pactl_names("cards"):
        if not card.startswith("bluez_card"):
            continue
        subprocess.run(["pactl", "set-card-profile", card,
                        "headset-head-unit"],
                       capture_output=True, timeout=5)
        for _ in range(10):
            time.sleep(0.5)
            for s in _pactl_names("sources"):
                if s.startswith("bluez_input"):
                    print(f"voice: switched {card} to headset profile",
                          flush=True)
                    return s
    return "@DEFAULT_SOURCE@"


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
    shared = {"final": "", "final_ts": 0.0}   # QualityPass writes here
    try:
        qp = QualityPass(shared)
        print("voice: quality pass up (moonshine base)", flush=True)
    except Exception as e:
        qp = None
        print(f"quality pass unavailable ({e}); streaming text only",
              flush=True)
    print("voice: recognizer + speaker up, capturing", flush=True)
    stream = rec.create_stream()
    nbytes = int(RATE * CHUNK_S) * 2
    preroll = collections.deque(maxlen=3)   # 0.3 s before the gate opens
    utt = []                                # current utterance samples

    def finish(fallback, now):
        """Endpoint/gate-close: hand the utterance to the quality pass
        (or publish the streaming text directly without one)."""
        if qp is not None and utt:
            qp.submit(np.concatenate(utt), fallback)
        elif fallback:
            shared["final"], shared["final_ts"] = fallback, now
            print(f"heard: {fallback!r}", flush=True)
        del utt[:]
    # ENERGY GATE: the zipformer encoder costs ~40% of a core if it runs
    # on silence too. Only decode while the room is louder than GATE_DB
    # or within HANG_S of the last loud chunk (sentence tails, pauses).
    # The mic itself STAYS OPEN the whole time -- gating is about CPU,
    # not attention; Parviz remains continuously engaged.
    GATE_DB = -48.0
    HANG_S = 2.0
    loud_until = 0.0
    zero_since = None   # dead-source watchdog: pure digital silence
    while True:
        dev = find_mic_source()
        print(f"voice: capturing from {dev}", flush=True)
        proc = subprocess.Popen(
            ["parec", f"--device={dev}", "--format=s16le",
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
                # WATCHDOG: -120 dB is digital zero, not a quiet room --
                # the source died under us (bluetooth drop -> parec keeps
                # streaming silence from a dummy). Respawn so the capture
                # re-resolves @DEFAULT_SOURCE@ when the device returns.
                if db < -120.0:
                    zero_since = zero_since or now
                    if now - zero_since > 10.0:
                        print("voice: source is digital-silent, "
                              "respawning capture", flush=True)
                        zero_since = None
                        break
                else:
                    zero_since = None
                xf = x / 32768.0
                preroll.append(xf)
                if spk.speaking:
                    # HALF-DUPLEX: our own voice is playing; drop any
                    # in-flight partial and keep the gate shut
                    if rec.get_result(stream):
                        rec.reset(stream)
                    loud_until = 0.0
                    del utt[:]
                    write_atomic(SPEECH_JSON, {
                        "ts": round(now, 2), "partial": "",
                        "final": shared["final"],
                        "final_ts": round(shared["final_ts"], 2),
                        "level_db": round(db, 1), "speaking": True,
                    })
                    continue
                if db > GATE_DB:
                    if now >= loud_until:      # gate opening: keep the
                        utt.extend(preroll)    # 0.3 s that woke it
                    loud_until = now + HANG_S
                partial = ""
                if now < loud_until:
                    if len(utt) < 300:         # 30 s hard cap
                        utt.append(xf)
                    stream.accept_waveform(RATE, xf)
                    while rec.is_ready(stream):
                        rec.decode_stream(stream)
                    partial = rec.get_result(stream).lower()
                    if rec.is_endpoint(stream):
                        finish(partial.strip(), now)
                        rec.reset(stream)
                        partial = ""
                else:
                    # gate just closed with an utterance still pending
                    # (endpoint 0.8 s normally beats the 2 s hangover;
                    # this is the safety net): finalize it
                    pend = rec.get_result(stream).lower().strip()
                    if pend:
                        finish(pend, now)
                        rec.reset(stream)
                    elif utt:
                        del utt[:]
                write_atomic(SPEECH_JSON, {
                    "ts": round(now, 2),
                    "partial": partial,
                    "final": shared["final"],
                    "final_ts": round(shared["final_ts"], 2),
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
