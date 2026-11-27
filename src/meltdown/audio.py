"""Cross-platform zero-dependency audio engine for MELTDOWN."""

import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import wave

try:
    import winsound
except ImportError:
    winsound = None


def _synth_wav_bytes(freq: int, duration_ms: int, volume: float = 0.25) -> bytes:
    """Synthesize a tiny in-memory mono 16-bit PCM WAV tone."""
    sample_rate = 22050
    n_samples = max(1, int(sample_rate * duration_ms / 1000.0))
    frames = bytearray()
    for i in range(n_samples):
        # Smooth attack/decay envelope to avoid clicks
        env = min(1.0, i / 120.0, (n_samples - i) / 120.0)
        val = int(32767 * volume * env * math.sin(2.0 * math.pi * freq * i / sample_rate))
        frames.extend(struct.pack("<h", max(-32768, min(32767, val))))
    buf = tempfile.SpooledTemporaryFile()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(bytes(frames))
    buf.seek(0)
    return buf.read()


class Sound:
    """Non-blocking cross-platform sound effects with graceful fallback."""

    enabled = True
    _unix_player = None
    _checked_player = False

    @classmethod
    def _find_unix_player(cls):
        if not cls._checked_player:
            cls._checked_player = True
            for cmd in ("afplay", "aplay", "paplay"):
                path = shutil.which(cmd)
                if path:
                    cls._unix_player = path
                    break
        return cls._unix_player

    @classmethod
    def play_tone(cls, freq: int, duration_ms: int = 80) -> None:
        """Play a tone asynchronously without blocking the game loop."""
        if not cls.enabled:
            return

        def _worker():
            try:
                if sys.platform == "win32" and winsound is not None:
                    winsound.Beep(max(37, min(32767, int(freq))), max(20, int(duration_ms)))
                    return
                player = cls._find_unix_player()
                if player:
                    wav_data = _synth_wav_bytes(freq, duration_ms)
                    fd, tmp_path = tempfile.mkstemp(suffix=".wav")
                    try:
                        with os.fdopen(fd, "wb") as f:
                            f.write(wav_data)
                        subprocess.run(
                            [player, tmp_path],
                            stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            timeout=2,
                        )
                    finally:
                        try:
                            os.remove(tmp_path)
                        except OSError:
                            pass
            except Exception:
                pass

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    @classmethod
    def beep(cls):
        cls.play_tone(440, 75)

    @classmethod
    def wrong(cls):
        cls.play_tone(220, 120)

    @classmethod
    def expire(cls):
        cls.play_tone(180, 160)

    @classmethod
    def surge(cls):
        cls.play_tone(660, 110)

    @classmethod
    def boss(cls):
        cls.play_tone(150, 220)

    @classmethod
    def combo(cls, combo_count: int):
        """Play a rising-pitch chime on combo milestones."""
        if combo_count in (2, 5, 10, 15, 20) or (combo_count > 20 and combo_count % 5 == 0):
            freq = min(1400, 520 + combo_count * 35)
            cls.play_tone(freq, 70)

    @classmethod
    def powerup(cls):
        cls.play_tone(880, 90)

    @classmethod
    def warning_pulse(cls):
        cls.play_tone(300, 60)

    @classmethod
    def chord(cls, freqs, note_ms: int = 75):
        """Play a short multi-tone arpeggio chord asynchronously."""
        if not cls.enabled:
            return

        def _seq():
            import time as _t
            for f in freqs:
                cls.play_tone(f, note_ms)
                _t.sleep(note_ms / 1000.0)

        threading.Thread(target=_seq, daemon=True).start()

    @classmethod
    def level_clear(cls):
        cls.chord([523, 659, 784], 70)

    @classmethod
    def rank_s(cls):
        cls.chord([587, 740, 880, 1175], 80)

    @classmethod
    def boss_defeat(cls):
        cls.chord([392, 523, 659, 1046], 90)
