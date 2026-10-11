"""Sound: effects are synthesized from waveforms; the background music is two looping mp3 files in assets/music."""
import math
import os
import random
from array import array

import pygame

import config

SR = 22050
MUSIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "music")
TRACKS = {"lobby": os.path.join(MUSIC_DIR, "casino_night.mp3"),      # menus
          "game": os.path.join(MUSIC_DIR, "late_night.mp3")}        # playing, shop


def _to_sound(samples, vol=1.0):
    buf = array("h", (int(max(-1.0, min(1.0, s * vol)) * 32000) for s in samples))
    return pygame.mixer.Sound(buffer=buf.tobytes())


def tone(freq, dur, vol=0.5, wave="sine", decay=5.0, f1=None):
    n = int(SR * dur)
    out, ph = [], 0.0
    f1 = f1 or freq
    for i in range(n):
        t = i / n
        ph += math.tau * (freq + (f1 - freq) * t) / SR
        if wave == "sine":
            v = math.sin(ph)
        elif wave == "square":
            v = 1.0 if math.sin(ph) > 0 else -1.0
        elif wave == "tri":
            v = 2 / math.pi * math.asin(math.sin(ph))
        else:
            v = (ph / math.pi) % 2 - 1
        att = min(1.0, i / (SR * 0.004))
        out.append(v * vol * att * math.exp(-decay * t))
    return out


def noise(dur, vol=0.5, lp=0.3, decay=4.0, sweep=None):
    n = int(SR * dur)
    out, y = [], 0.0
    for i in range(n):
        t = i / n
        a = lp if sweep is None else lp + (sweep - lp) * t
        y += a * (random.uniform(-1, 1) - y)
        out.append(y * vol * math.exp(-decay * t) * min(1.0, i / (SR * 0.005)))
    return out


def mix(*tracks):
    n = max(len(t) for t in tracks)
    return [sum(t[i] for t in tracks if i < len(t)) for i in range(n)]


def seq(*parts, gap=0.0):
    out = []
    for p in parts:
        out += p + [0.0] * int(SR * gap)
    return out


def _note(semi, base=220.0):
    return base * 2 ** (semi / 12)


class Sfx:
    def __init__(self):
        self.ok = False
        self.muted = not config.SOUND
        self.volume = config.MASTER_VOLUME          # sound effects
        self.music_volume = 0.5
        self.sounds = {}
        self.music = None                           # synthesized fallback loop (used only if the mp3 files are missing)
        self.track = None                           # name of the mp3 track currently playing
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(SR, -16, 1, 512)
            pygame.mixer.set_num_channels(24)
            self._build()
            self.ok = True
        except Exception as e:  # no audio device: game still runs silently
            print("audio disabled:", e)

    # ------------------------------------------------------------ build
    def _build(self):
        S = self.sounds
        S["click"] = _to_sound(tone(900, 0.06, 0.5, "square", 40), 0.5)
        S["error"] = _to_sound(tone(160, 0.14, 0.6, "square", 10), 0.5)
        for i in range(6):                                           # select pitch rises with count
            S[f"select{i}"] = _to_sound(mix(tone(_note(i * 2 + 7), 0.09, 0.5, "tri", 22),
                                            tone(_note(i * 2 + 19), 0.09, 0.2, "sine", 25)))
        S["deal"] = _to_sound(noise(0.16, 0.5, 0.15, 5, sweep=0.6), 0.6)
        for i in range(12):                                          # score tick rises per step
            S[f"tick{i}"] = _to_sound(mix(tone(_note(min(i, 11) * 2 + 12), 0.12, 0.5, "sine", 14),
                                          tone(_note(min(i, 11) * 2 + 24), 0.1, 0.25, "tri", 16)))
        for r in range(1, 11):                                       # combo chord by rank
            ratios = [0, 4, 7, 12, 16, 19][:min(6, 1 + (r + 1) // 2)]
            base = 4 + r * 0.5
            S[f"combo{r}"] = _to_sound(mix(*[tone(_note(base + s), 0.25 + r * 0.05, 0.28, "tri", 3.2) for s in ratios]))
        S["lightning"] = _to_sound(mix(noise(0.3, 0.9, 0.9, 7), tone(1400, 0.25, 0.4, "saw", 9, 200)))
        S["ice"] = _to_sound(mix(tone(2200, 0.5, 0.3, "sine", 5), tone(3300, 0.45, 0.2, "sine", 6),
                                 tone(2750, 0.6, 0.2, "sine", 4)))
        S["fire"] = _to_sound(mix(noise(0.55, 0.9, 0.1, 3.5, sweep=0.35), tone(90, 0.5, 0.4, "saw", 4)))
        S["coin"] = _to_sound(seq(tone(1318, 0.07, 0.4, "square", 12), tone(1760, 0.22, 0.4, "square", 8)), 0.5)
        S["double"] = _to_sound(mix(tone(440, 0.5, 0.4, "tri", 3, 880), tone(660, 0.5, 0.3, "sine", 3, 1320)))
        S["gacha"] = _to_sound(mix(tone(200, 0.9, 0.35, "saw", 0.5, 1200), tone(300, 0.9, 0.2, "sine", 0.3, 1800)))
        S["reveal"] = _to_sound(mix(*[tone(_note(s), 0.8, 0.28, "tri", 3) for s in (12, 16, 19, 24)]))
        S["win"] = _to_sound(seq(*[tone(_note(s), 0.16, 0.4, "square", 6) for s in (12, 16, 19, 24, 28)], gap=0.02)
                             + tone(_note(31), 0.7, 0.4, "tri", 3), 0.6)
        S["over"] = _to_sound(seq(*[tone(_note(s), 0.3, 0.4, "saw", 3) for s in (7, 3, 0, -5)]), 0.6)
        S["whoosh"] = _to_sound(noise(0.35, 0.6, 0.05, 3, sweep=0.5), 0.6)
        S["splash"] = _to_sound(mix(noise(0.45, 0.8, 0.3, 5, sweep=0.2), tone(600, 0.2, 0.25, "sine", 12, 1500)), 0.6)
        S["boom"] = _to_sound(mix(noise(0.6, 1.0, 0.04, 4), tone(70, 0.6, 0.7, "sine", 4, 35)), 0.8)
        S["clank"] = _to_sound(seq(tone(520, 0.05, 0.5, "square", 30), tone(780, 0.05, 0.5, "square", 30),
                                   tone(390, 0.12, 0.5, "square", 20)), 0.5)
        S["chime"] = _to_sound(mix(*[tone(_note(s + 24), 0.6, 0.22, "sine", 4) for s in (0, 7, 12, 16)]), 0.6)
        S["slash"] = _to_sound(noise(0.18, 0.9, 0.7, 12, sweep=1.8), 0.6)
        S["pop"] = _to_sound(mix(noise(0.5, 0.9, 0.5, 6), tone(180, 0.25, 0.5, "sine", 9, 60)), 0.7)
        S["slam"] = _to_sound(mix(noise(0.3, 1.0, 0.08, 9), tone(110, 0.35, 0.8, "square", 8, 55)), 0.8)
        if config.MUSIC and not all(os.path.exists(p) for p in TRACKS.values()):
            self._build_music()                                      # fallback when the mp3 files are missing

    def _build_music(self):
        chords = [(0, 3, 7), (-4, 0, 3), (3, 7, 10), (-2, 2, 5)]     # Cm  Ab  Eb  Bb  flavour
        step = 0.16
        out = []
        for ch in chords:
            for i in range(8):
                s = ch[[0, 1, 2, 1][i % 4]] + (12 if i >= 4 and i % 2 else 0)
                out += tone(_note(s, 130.8), step, 0.5, "tri", 5)
            out[-int(SR * step * 8):] = mix(out[-int(SR * step * 8):],
                                            tone(_note(ch[0] - 12, 130.8), step * 8, 0.5, "sine", 0.6))
        self.music = _to_sound(out, 0.16)

    # ------------------------------------------------------------ control
    def _apply(self):
        for s in self.sounds.values():
            s.set_volume(0 if self.muted else self.volume)
        if self.music:
            self.music.set_volume(0 if self.muted else self.music_volume * 0.35)
        try:
            pygame.mixer.music.set_volume(0 if self.muted else self.music_volume)
        except pygame.error:
            pass

    def start_music(self):
        """Start the lobby track (or the synthesized fallback when the mp3 files are missing)."""
        if not self.ok:
            return
        if not self.set_track("lobby") and self.music:
            self.music.play(-1)
        self._apply()

    def set_track(self, name):
        """Switch the looping background music: "lobby" (menus) or "game" (playing and shop). None / the same track
        keeps what is playing. Returns True when an mp3 track is active."""
        if not self.ok or not config.MUSIC:
            return False
        if name is None or name == self.track:
            return self.track is not None
        path = TRACKS.get(name)
        if not path or not os.path.exists(path):
            return False
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1, fade_ms=700)
        except pygame.error as e:
            print("music disabled:", e)
            return False
        if self.music:
            self.music.stop()
        self.track = name
        self._apply()
        return True

    def play(self, name):
        if self.ok and name in self.sounds and not self.muted:
            self.sounds[name].set_volume(self.volume)
            self.sounds[name].play()

    def toggle_mute(self):
        self.muted = not self.muted
        if self.ok:
            self._apply()

    def set_music_volume(self, v):
        self.music_volume = max(0.0, min(1.0, v))
        if self.ok:
            self._apply()

    def set_sfx_volume(self, v):
        self.volume = max(0.0, min(1.0, v))
        if self.ok:
            self._apply()

    def change_volume(self, d):
        self.volume = max(0.0, min(1.0, round(self.volume + d, 2)))
        if self.ok:
            self._apply()
