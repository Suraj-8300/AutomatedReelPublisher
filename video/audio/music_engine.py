"""
Procedural Music Bed Generator for AutoReelStudio.
Generates royalty-free background music programmatically using pure Python
and standard library wave module. Zero external dependencies.
"""

import math
import struct
import wave
import hashlib
import subprocess
from pathlib import Path
from typing import Optional

from video.config import CACHE_DIR

_MUSIC_CACHE = CACHE_DIR / "music"
_MUSIC_CACHE.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE = 48000
CHANNELS = 2

# Style profiles: (bass_hz, sub_hz, lead_hz, bpm, description)
STYLE_PROFILES = {
    "heartwarming_story": (65.4,  32.7, 130.8,  76, "Warm acoustic & piano chords — cute animals & emotional storytelling"),
    "uplifting_journey":  (73.4,  36.7, 146.8,  92, "Bright hopeful melody — rescue journeys & joyful endings"),
    "upbeat_summer":      (82.4,  41.2, 164.8, 118, "Upbeat acoustic pop & warm summer rhythm — UGC, lifestyle & product showcases"),
    "cyber_pulse":        (65.4,  32.7, 130.8, 120, "Electronic pulse — tech/mechanical"),
    "deep_mystery":       (55.0,  27.5, 110.0,  90, "Dark ambient — cinematic/sci-fi"),
    "curiosity_lofi":     (73.4,  36.7, 146.8, 100, "Soft lo-fi — explainer/educational"),
    "ambient_glow":       (49.0,  24.5,  98.0,  70, "Atmospheric glow — science/space"),
    "action_hybrid":      (82.4,  41.2, 164.8, 130, "Driving energy — action scenes"),
}
DEFAULT_STYLE = "heartwarming_story"


class MusicEngine:
    """
    Generates procedural stereo music beds as 48kHz WAV files.
    Each style is cached so identical durations are never re-rendered.
    """

    @classmethod
    def generate(
        cls,
        style: str = DEFAULT_STYLE,
        duration_sec: float = 40.0,
    ) -> Path:
        """
        Generates or retrieves a cached procedural music track.
        Returns path to a 48kHz stereo WAV file.
        """
        style = style if style in STYLE_PROFILES else DEFAULT_STYLE
        cache_key = hashlib.md5(f"{style}_{int(duration_sec)}".encode()).hexdigest()[:8]
        wav_path = _MUSIC_CACHE / f"music_{style}_{cache_key}.wav"

        if wav_path.exists() and wav_path.stat().st_size > 10000:
            return wav_path

        profile = STYLE_PROFILES[style]
        f_bass, f_sub, f_lead, bpm, _ = profile

        total_samples = int(SAMPLE_RATE * duration_sec)
        beat_len = int(SAMPLE_RATE * 60.0 / bpm)

        frames = bytearray()
        for i in range(total_samples):
            t = i / SAMPLE_RATE
            beat_phase = (i % beat_len) / beat_len

            # Fade in/out envelopes
            fade_in  = min(1.0, t / 2.0)
            fade_out = min(1.0, (duration_sec - t) / 2.0)
            env = fade_in * fade_out

            # Kick drum: short sine burst on downbeats
            kick = 0.0
            if beat_phase < 0.03:
                kick = 0.4 * math.sin(2 * math.pi * 80 * t) * math.exp(-beat_phase * 60)

            # Sub bass: continuous sine
            sub = 0.15 * math.sin(2 * math.pi * f_sub * t)

            # Bass line: quarter notes
            bass_phase = (i % (beat_len // 4)) / (beat_len // 4)
            bass = 0.20 * math.sin(2 * math.pi * f_bass * t) * (1.0 - bass_phase * 0.3)

            # Lead arpeggio (eighth notes) — slight detuning per note
            arp_note = (i // (beat_len // 8)) % 4
            arp_freqs = [f_lead, f_lead * 1.189, f_lead * 1.335, f_lead * 1.498]
            arp = 0.12 * math.sin(2 * math.pi * arp_freqs[arp_note] * t) * 0.8

            # Hi-hat: noise pulse on upbeats
            hat_phase = (i % (beat_len // 2)) / (beat_len // 2)
            hat = 0.06 * (2 * (hash(i) % 1000) / 1000.0 - 1) * math.exp(-hat_phase * 25) if hat_phase < 0.05 else 0.0

            # Mix + stereo spread (slight delay on right channel)
            mono = (kick + sub + bass + arp + hat) * env * 0.7
            left  = mono + 0.08 * math.sin(2 * math.pi * f_lead * 0.5 * t) * env
            right = mono - 0.08 * math.sin(2 * math.pi * f_lead * 0.5 * t) * env

            # Clip & pack as 16-bit little-endian stereo
            left_s  = max(-32767, min(32767, int(left  * 32767)))
            right_s = max(-32767, min(32767, int(right * 32767)))
            frames.extend(struct.pack("<hh", left_s, right_s))

        with wave.open(str(wav_path), "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(bytes(frames))

        return wav_path

    @classmethod
    def get_ducked_mix(
        cls,
        music_path: Path,
        voice_path: Path,
        output_path: Path,
        music_volume_db: float = -18.0,
        duck_db: float = -14.0,
    ) -> Path:
        """
        Mixes music (attenuated) with voice using FFmpeg.
        Music is globally reduced by music_volume_db.
        Returns path to the mixed audio file (WAV).
        """
        # Build FFmpeg amix with sidechain ducking simulation via volume filter
        # music_vol when no speech: music_volume_db
        # music_vol during speech: music_volume_db + duck_db (more attenuation)
        music_vol = 10 ** (music_volume_db / 20.0)

        cmd = [
            "ffmpeg", "-y",
            "-i", str(voice_path),
            "-i", str(music_path),
            "-filter_complex",
            (
                f"[1:a]volume={music_vol:.4f}[music];"
                f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[out]"
            ),
            "-map", "[out]",
            "-ac", "2",
            "-ar", "48000",
            "-c:a", "pcm_s16le",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0 or not output_path.exists():
            # Fallback: just return the voice track
            import shutil
            shutil.copy2(voice_path, output_path)
        return output_path
