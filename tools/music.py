"""Royalty-free instrumental bed for lalehstore videos, synthesized in code (numpy/scipy only).

Every track is generated from scratch, so there is no copyright claim on it. It follows the
video: a short filtered intro under the hook, the groove when the first scene ends, a paper
"whoosh" on every scene change, and a soft fade at the end.

Moods (spec["music"]["mood"]): "lofi" (warm keys, lazy swing), "house" (bright chill house),
"pop" (plucky upbeat). Default: picked from the spec seed.

Usage (normally called by cinema.py):
  python3 -I music.py out.wav DURATION [--cuts 3.4,7.6] [--mood lofi] [--seed 7]
"""
import math
import sys
import wave

import numpy as np
from scipy import signal

SR = 44100

KEYS = {"A": 57, "C": 60, "D": 62, "E": 64, "F": 65, "G": 67}
PROGS = {   # semitone offsets from the key root (minor-ish, pleasant, loopable)
    "lofi": [[-3, 0, 4, 7, 11], [-7, -3, 0, 4, 7], [0, 4, 7, 11, 14], [-5, -1, 2, 5, 9]],
    "house": [[-3, 0, 4, 7], [-7, -3, 0, 4], [0, 4, 7, 11], [-5, -1, 2, 7]],
    "pop": [[0, 4, 7, 12], [-5, -1, 2, 7], [-3, 0, 4, 9], [-7, -3, 0, 5]],
}
BPM = {"lofi": 84, "house": 118, "pop": 104}


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tv(n):
    return np.arange(n) / SR


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, min(f, SR * 0.45), "lowpass", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "highpass", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(signal.butter(order, [lo, hi], "bandpass", fs=SR, output="sos"), x)


class Synth:
    def __init__(self, seed):
        self.r = np.random.default_rng(seed)

    # ---------------- instruments (mono)
    def keys(self, notes, length, bright=1.2):
        n = int(length * SR)
        t = tv(n)
        x = np.zeros(n)
        for m in notes:
            f = hz(m) * (1 + self.r.uniform(-0.0015, 0.0015))
            mod = bright * np.exp(-t / 0.35) * np.sin(2 * np.pi * f * t)
            x += np.sin(2 * np.pi * f * t + mod) + 0.15 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.2)
        trem = 1 + 0.12 * np.sin(2 * np.pi * 4.2 * t)
        env = np.exp(-t / 1.6) * (1 - np.exp(-t / 0.004)) * np.clip((length - t) / 0.08, 0, 1)
        return x / len(notes) * env * trem

    def pad(self, notes, length, cutoff=1400):
        n = int(length * SR)
        t = tv(n)
        x = np.zeros(n)
        for m in notes:
            for d in (-0.07, 0.0, 0.07):
                x += signal.sawtooth(2 * np.pi * hz(m) * 2 ** (d / 12) * t + self.r.uniform(0, 6.28))
        x = lp(x, cutoff, 2)
        env = np.clip(t / 0.35, 0, 1) * np.clip((length - t) / 0.4, 0, 1)
        return x / (3 * len(notes)) * env

    def bass(self, m, length):
        n = int(length * SR)
        t = tv(n)
        f = hz(m)
        x = np.sin(2 * np.pi * f * t) + 0.7 * signal.sawtooth(2 * np.pi * f * t)
        x = lp(x, 900, 2)
        return np.tanh(1.4 * x) * np.clip(t / 0.005, 0, 1) * np.clip((length - t) / 0.03, 0, 1) * np.exp(-t / 1.4)

    def pluck(self, m, length=0.3):
        n = int(length * SR)
        t = tv(n)
        f = hz(m)
        x = signal.sawtooth(2 * np.pi * f * t) + 0.6 * signal.square(2 * np.pi * f * 1.003 * t)
        x = lp(x, 2600, 2)
        return x * np.exp(-t / 0.11) * np.clip(t / 0.002, 0, 1)

    def kick(self, soft=True):
        n = int(0.4 * SR)
        t = tv(n)
        f = 48 + 110 * np.exp(-t / 0.03)
        body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (0.14 if soft else 0.18))
        click = hp(self.r.standard_normal(n) * np.exp(-t / 0.0015), 2000) * 0.18
        return np.tanh(1.6 * (body + click))

    def snare(self):
        n = int(0.3 * SR)
        t = tv(n)
        noise = bp(self.r.standard_normal(n), 1200, 6000) * np.exp(-t / 0.07)
        tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.04)
        return 0.7 * noise + 0.4 * tone

    def clap(self):
        n = int(0.3 * SR)
        t = tv(n)
        e = sum(np.exp(-np.maximum(t - d, 0) / 0.006) * (t >= d) for d in (0, 0.01, 0.021))
        e = e + 0.6 * np.exp(-np.maximum(t - 0.03, 0) / 0.08) * (t >= 0.03)
        return bp(self.r.standard_normal(n), 900, 3500) * e

    def hat(self, open_=False):
        n = int((0.25 if open_ else 0.06) * SR)
        t = tv(n)
        return hp(self.r.standard_normal(n), 7000, 3) * np.exp(-t / (0.08 if open_ else 0.018))

    def shaker(self):
        n = int(0.09 * SR)
        t = tv(n)
        return bp(self.r.standard_normal(n), 4000, 11000) * np.sin(np.pi * np.clip(t / 0.09, 0, 1)) ** 2

    def whoosh(self, length=0.75):
        n = int(length * SR)
        p = np.linspace(0, 1, n)
        x = self.r.standard_normal(n)
        out = np.zeros(n)
        block = 512
        for i in range(0, n, block):   # band-pass sweep up then down
            k = p[i]
            fc = 300 + 5200 * math.sin(math.pi * k) ** 1.5
            seg = x[max(0, i - 1024): i + block]
            y = bp(seg, fc * 0.6, min(fc * 1.6, SR * 0.45))
            out[i: i + block] = y[-len(out[i: i + block]):]
        return out * np.sin(np.pi * p) ** 2 * 1.4

    def impact(self):
        n = int(1.2 * SR)
        t = tv(n)
        f = 32 + 50 * np.exp(-t / 0.2)
        return np.tanh(1.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.45)) * 0.8

    def crackle(self, n):
        x = np.zeros(n)
        idx = self.r.integers(0, n, n // 900)
        x[idx] = self.r.uniform(-1, 1, len(idx))
        return lp(hp(x, 1500), 7000) * 0.5 + lp(self.r.standard_normal(n), 900) * 0.01


class Mix:
    def __init__(self, dur):
        self.n = int((dur + 2) * SR)
        self.L, self.R = np.zeros(self.n), np.zeros(self.n)

    def add(self, x, at, gain=1.0, pan=0.0):
        s = int(at * SR)
        if s < 0:
            x, s = x[-s:], 0
        if s >= self.n or len(x) == 0:
            return
        e = min(self.n, s + len(x))
        a = (pan + 1) / 2
        self.L[s:e] += x[: e - s] * gain * math.sqrt(1 - a)
        self.R[s:e] += x[: e - s] * gain * math.sqrt(a)


def make(dur, cuts=(), mood=None, seed=7, key=None):
    rnd = np.random.default_rng(seed)
    mood = mood or ["lofi", "house", "pop"][seed % 3]
    key = key or list(KEYS)[seed % len(KEYS)]
    root = KEYS[key]
    bpm = BPM[mood]
    beat = 60 / bpm
    bar = 4 * beat
    syn = Synth(seed)
    music, drums, fx = Mix(dur), Mix(dur), Mix(dur)
    groove_at = cuts[0] if cuts else min(3.0, dur / 4)
    # snap the groove start to the bar grid so the drop lands on a downbeat
    groove_bar = max(1, round(groove_at / bar))
    t_drop = groove_bar * bar
    shift = groove_at - t_drop          # move the whole grid so the downbeat hits the first cut
    t_drop = groove_at
    prog = PROGS[mood]
    nbars = int((dur - shift) / bar) + 2
    swing = 0.12 if mood == "lofi" else 0.04
    kicks = []
    for b in range(nbars):
        t_bar = shift + b * bar
        if t_bar > dur + bar:
            break
        if t_bar + bar < 0:
            continue
        ch = [root + o for o in prog[b % 4]]
        in_groove = t_bar >= t_drop - 1e-6
        # chords
        if mood == "lofi":
            music.add(syn.keys(ch, bar * 0.98), t_bar, 1.5 if in_groove else 1.3, pan=-0.1)
            music.add(syn.keys(ch[1:], beat * 1.2, 0.8), t_bar + 2.5 * beat, 0.6, pan=0.25)
        else:
            music.add(syn.pad(ch, bar, 1800 if mood == "house" else 2400), t_bar, 1.3)
            for s in (0, 1.5, 3) if mood == "house" else (0, 2):
                music.add(syn.keys(ch, beat * 0.9, 1.6), t_bar + s * beat, 0.8, pan=0.15)
        if not in_groove:
            continue
        # bass
        bnote = ch[0] - 12 if ch[0] >= 48 else ch[0]
        while bnote > 47:
            bnote -= 12
        pat = [(0, 1.4), (2.5, 0.5), (3, 0.9)] if mood != "lofi" else [(0, 1.8), (2.75, 1.0)]
        for s, l in pat:
            music.add(syn.bass(bnote, l * beat), t_bar + s * beat, 0.4)
        # melody (pentatonic plucks every other bar, not under the very first groove bar)
        if mood != "lofi" and b % 2 == 1:
            scale = [0, 3, 5, 7, 10, 12, 15]
            for i in range(8):
                if rnd.random() < 0.55:
                    m = root + 12 + scale[int(rnd.integers(0, len(scale)))]
                    music.add(syn.pluck(m, 0.28), t_bar + i * beat / 2, 0.42, pan=rnd.uniform(-0.4, 0.4))
        # drums
        for q in range(4):
            tb = t_bar + q * beat
            if mood == "lofi":
                if q in (0, 2) or (q == 3 and b % 2):
                    drums.add(syn.kick(True), tb + (0.5 * beat if q == 3 else 0), 0.5)
                    kicks.append(tb)
                if q in (1, 3):
                    drums.add(syn.snare(), tb, 0.32)
            else:
                drums.add(syn.kick(mood == "pop"), tb, 0.55)
                kicks.append(tb)
                if q in (1, 3):
                    drums.add(syn.clap(), tb, 0.38)
            for h in (0, 1):
                off = h * beat / 2 + (swing * beat if h else 0)
                drums.add(syn.hat(open_=(mood == "house" and h == 1)), tb + off, 0.14 if h else 0.1,
                          pan=0.3)
            if mood != "lofi":
                drums.add(syn.shaker(), tb + beat * 0.25, 0.07, pan=-0.35)
    # transitions: whoosh into every cut, impact on the drop
    for c in cuts:
        w = syn.whoosh(0.8)
        fx.add(w, c - 0.42, 0.16, pan=-0.3)
        fx.add(w[::-1] * 0.6, c - 0.42, 0.12, pan=0.3)
    fx.add(syn.impact(), t_drop, 0.25)
    fx.add(syn.crackle(fx.n), 0, 0.6 if mood == "lofi" else 0.25)
    # sidechain pump on music
    n = music.n
    t = tv(n)
    g = np.ones(n)
    for kt in kicks:
        s = int(kt * SR)
        if 0 <= s < n:
            seg = t[s:] - kt
            g[s:] = np.minimum(g[s:], 1 - 0.38 * np.exp(-seg / 0.12))
    # intro: low-pass the hook section and open it at the drop
    L = music.L * g
    R = music.R * g
    d0 = int(max(0, t_drop) * SR)
    if d0 > 0:
        L[:d0] = lp(L[:d0], 700)
        R[:d0] = lp(R[:d0], 700)
    L = L + drums.L + fx.L
    R = R + drums.R + fx.R
    st = np.stack([L, R])[:, : int(dur * SR)]
    st = hp(st[0], 30)[None], hp(st[1], 30)[None]
    st = np.concatenate(st)
    # glue + fade
    st = np.tanh(st * 1.3) / 1.3
    fade = int(1.4 * SR)
    st[:, -fade:] *= np.linspace(1, 0, fade) ** 1.5
    st[:, : int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
    rms = np.sqrt(np.mean(st ** 2)) + 1e-9
    st = st * (0.16 / rms)                          # ~ -16 dBFS RMS, loudnorm finishes in ffmpeg
    st = np.clip(st, -0.98, 0.98)
    return st, {"mood": mood, "key": key, "bpm": bpm, "drop": round(t_drop + 0, 2)}


def write_wav(path, st):
    data = (st.T * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


def main():
    out, dur = sys.argv[1], float(sys.argv[2])
    cuts, mood, seed = [], None, 7
    if "--cuts" in sys.argv:
        cuts = [float(x) for x in sys.argv[sys.argv.index("--cuts") + 1].split(",") if x]
    if "--mood" in sys.argv:
        mood = sys.argv[sys.argv.index("--mood") + 1]
    if "--seed" in sys.argv:
        seed = int(sys.argv[sys.argv.index("--seed") + 1])
    st, info = make(dur, cuts, mood, seed)
    write_wav(out, st)
    print(info)


if __name__ == "__main__":
    main()
