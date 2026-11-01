import math
import struct
import wave
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from .config import CACHE_DIR

class MusicEngine:
    """
    Advanced procedural soundtrack and SFX generator.
    Produces rich, multi-voice ambient music beds with intro whoosh impacts.
    """

    SAMPLE_RATE = 44100

    @staticmethod
    def generate_soundtrack(
        duration: float,
        style: str = "cyber_pulse",
        output_file: Optional[Path] = None,
        volume: float = 0.22,
        add_intro_whoosh: bool = True
    ) -> str:
        """
        Synthesizes a rich, looping ambient background track of the requested duration.
        Includes a subtle cinematic whoosh at 0.0s to hook viewer attention immediately.
        """
        if output_file is None:
            output_file = CACHE_DIR / f"music_{style}_{uuid.uuid4().hex[:6]}.wav"

        num_samples = int(MusicEngine.SAMPLE_RATE * duration)
        fade_in_samples = int(MusicEngine.SAMPLE_RATE * 0.8)
        fade_out_samples = int(MusicEngine.SAMPLE_RATE * 2.0)

        # Chords & Pulse settings
        if style == "cyber_pulse":
            chords = [
                [73.42, 146.83, 220.00, 261.63, 329.63], # Dm9
                [58.27, 116.54, 174.61, 233.08, 293.66], # Bbmaj7
                [87.31, 174.61, 261.63, 329.63, 392.00], # Fmaj9
                [65.41, 130.81, 196.00, 246.94, 293.66], # Cadd9
            ]
            pulse_rate = 2.0
        elif style == "deep_mystery":
            chords = [
                [55.00, 110.00, 164.81, 220.00, 261.63], # Am
                [43.65, 87.31, 130.81, 174.61, 220.00],  # Fmaj
                [65.41, 130.81, 196.00, 261.63, 329.63], # Cmaj
                [49.00, 98.00, 146.83, 196.00, 246.94],  # Gmaj
            ]
            pulse_rate = 1.0
        elif style == "cinematic_drive":
            chords = [
                [65.41, 130.81, 196.00, 293.66],        # C suspended
                [73.42, 146.83, 220.00, 329.63],        # D minor
                [58.27, 116.54, 174.61, 261.63],        # Bb major
                [65.41, 130.81, 196.00, 293.66],        # C suspended
            ]
            pulse_rate = 2.4
        else: # curiosity_lofi
            chords = [
                [65.41, 130.81, 164.81, 196.00, 246.94], # Cmaj7
                [58.27, 116.54, 146.83, 174.61, 220.00], # Bbmaj7
                [55.00, 110.00, 130.81, 164.81, 196.00], # Am7
                [43.65, 87.31, 110.00, 130.81, 164.81],  # Fmaj7
            ]
            pulse_rate = 1.5

        chord_len_secs = 3.5
        total_chords = len(chords)

        with wave.open(str(output_file), "w") as wav_file:
            wav_file.setnchannels(2)
            wav_file.setsampwidth(2)
            wav_file.setframerate(MusicEngine.SAMPLE_RATE)

            frames = bytearray()
            for i in range(num_samples):
                t = i / MusicEngine.SAMPLE_RATE

                # Active chord
                chord_idx = int((t / chord_len_secs)) % total_chords
                current_chord = chords[chord_idx]

                sample_l = 0.0
                sample_r = 0.0

                for f_idx, freq in enumerate(current_chord):
                    detune_l = -0.4 if f_idx % 2 == 0 else 0.4
                    detune_r = 0.4 if f_idx % 2 == 0 else -0.4

                    v_l = math.sin(2.0 * math.pi * (freq + detune_l) * t)
                    v_r = math.sin(2.0 * math.pi * (freq + detune_r) * t)

                    # Sub-harmonic depth
                    v_l += 0.25 * math.sin(4.0 * math.pi * freq * t)
                    v_r += 0.25 * math.sin(4.0 * math.pi * freq * t)

                    weight = 1.0 / (1.0 + f_idx * 0.35)
                    sample_l += v_l * weight
                    sample_r += v_r * weight

                # Pumping pulse
                pulse = 0.88 + 0.12 * math.sin(2.0 * math.pi * pulse_rate * t)
                sample_l *= pulse
                sample_r *= pulse

                # Cinematic Whoosh Hook at t = 0.0s to 0.7s
                if add_intro_whoosh and t < 0.7:
                    whoosh_prog = t / 0.7
                    whoosh_freq = 60.0 + (380.0 * (whoosh_prog ** 2))
                    whoosh_vol = math.sin(math.pi * whoosh_prog) * 0.4
                    whoosh_val = math.sin(2.0 * math.pi * whoosh_freq * t) * whoosh_vol
                    sample_l += whoosh_val
                    sample_r += whoosh_val

                # Base volume
                sample_l *= (volume / len(current_chord))
                sample_r *= (volume / len(current_chord))

                # Smooth Fades
                fade = 1.0
                if i < fade_in_samples:
                    fade = i / fade_in_samples
                elif i > (num_samples - fade_out_samples):
                    fade = (num_samples - i) / fade_out_samples
                fade = max(0.0, min(1.0, fade))

                sample_l *= fade
                sample_r *= fade

                # Clamping
                s_int_l = int(max(-32767, min(32767, sample_l * 32767)))
                s_int_r = int(max(-32767, min(32767, sample_r * 32767)))
                frames.extend(struct.pack("<hh", s_int_l, s_int_r))

            wav_file.writeframes(frames)

        return str(output_file)
