import os
import sys
import uuid
import datetime
import json
import ssl
import subprocess
import types
import urllib.request
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import websockets

# Import DRM token logic from local vendored lib or site-packages
PROJECT_DIR = Path(__file__).resolve().parent.parent
lib_dir = str(PROJECT_DIR / "lib")
if lib_dir not in sys.path:
    sys.path.insert(0, lib_dir)

if 'aiohttp' not in sys.modules:
    sys.modules['aiohttp'] = types.ModuleType('aiohttp')

from edge_tts.drm import DRM, generate_sec_ms_gec_v2
from edge_tts.constants import CHROMIUM_FULL_VERSION, SEC_MS_GEC_VERSION, TRUSTED_CLIENT_TOKEN, BASE_URL
from .config import DEFAULT_VOICE, CACHE_DIR

class TTSEngine:
    """
    High-fidelity neural text-to-speech with word-level millisecond alignment.
    100% free with no API keys.
    """

    @staticmethod
    def _sync_clock_skew():
        """
        Synchronizes client clock with Microsoft Edge-TTS server clock to prevent
        HTTP 403 Forbidden DRM rejections caused by local system time skew.
        """
        try:
            req = urllib.request.Request(
                f"https://{BASE_URL}/edge/v1",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            date_str = None
            try:
                with urllib.request.urlopen(req, timeout=4) as resp:
                    date_str = resp.headers.get("Date")
            except urllib.error.HTTPError as e:
                date_str = e.headers.get("Date")
            except Exception:
                pass

            if date_str:
                server_dt = parsedate_to_datetime(date_str)
                client_ts = datetime.datetime.now(datetime.timezone.utc).timestamp()
                DRM.clock_skew_seconds = server_dt.timestamp() - client_ts
        except Exception:
            pass

    @staticmethod
    def _date_to_string() -> str:
        return datetime.datetime.fromtimestamp(
            DRM.get_unix_timestamp(), tz=datetime.timezone.utc
        ).strftime("%a %b %d %Y %H:%M:%S GMT+0000 (Coordinated Universal Time)")

    @staticmethod
    async def synthesize(
        text: str,
        voice: str = DEFAULT_VOICE,
        output_file: Optional[Path] = None,
        rate: str = "+0%",
        pitch: str = "+0Hz"
    ) -> Dict[str, Any]:
        """
        Synthesizes text into high quality MP3 and returns audio path + word boundaries.
        """
        if output_file is None:
            output_file = CACHE_DIR / f"voice_{uuid.uuid4().hex[:8]}.mp3"

        TTSEngine._sync_clock_skew()
        sec_ms_gec = generate_sec_ms_gec_v2()
        wss_url = (
            f"wss://{BASE_URL}/edge/v1"
            f"?TrustedClientToken={TRUSTED_CLIENT_TOKEN}"
            f"&Sec-MS-GEC={sec_ms_gec}"
            f"&Sec-MS-GEC-Version={SEC_MS_GEC_VERSION}"
            f"&ConnectionId={uuid.uuid4().hex}"
        )

        headers = {
            "Origin": "chrome-extension://jdiccldimpdaibmpdkjnbmckianbfold",
            "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{CHROMIUM_FULL_VERSION} Safari/537.36 Edg/{CHROMIUM_FULL_VERSION}",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }

        ssl_context = ssl.create_default_context()
        audio_data = bytearray()
        words: List[Dict[str, Any]] = []

        try:
            async with websockets.connect(wss_url, additional_headers=headers, ssl=ssl_context) as ws:
                req_id = uuid.uuid4().hex

                # 1. Speech config requesting WordBoundary metadata
                config_msg = (
                    f"X-Timestamp:{TTSEngine._date_to_string()}\r\n"
                    f"Content-Type:application/json; charset=utf-8\r\n"
                    f"Path:speech.config\r\n\r\n"
                    f'{{"context":{{"synthesis":{{"audio":{{"metadataoptions":{{"sentenceBoundaryEnabled":"false","wordBoundaryEnabled":"true"}},"outputFormat":"audio-24khz-48kbitrate-mono-mp3"}}}}}}}}'
                )
                await ws.send(config_msg)

                # 2. SSML
                clean_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                ssml = (
                    f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>"
                    f"<voice name='{voice}'>"
                    f"<prosody pitch='{pitch}' rate='{rate}' volume='+0%'>"
                    f"{clean_text}"
                    f"</prosody></voice></speak>"
                )
                ssml_msg = (
                    f"X-RequestId:{req_id}\r\n"
                    f"Content-Type:application/ssml+xml\r\n"
                    f"X-Timestamp:{TTSEngine._date_to_string()}\r\n"
                    f"Path:ssml\r\n\r\n"
                    f"{ssml}"
                )
                await ws.send(ssml_msg)

                # 3. Read stream
                while True:
                    msg = await ws.recv()
                    if isinstance(msg, bytes):
                        header_len = int.from_bytes(msg[:2], "big")
                        header = msg[2:2+header_len].decode("utf-8", errors="ignore")
                        if "Path:audio" in header:
                            audio_data.extend(msg[2+header_len:])
                    elif isinstance(msg, str):
                        if "Path:audio.metadata" in msg:
                            parts = msg.split("\r\n\r\n", 1)
                            if len(parts) > 1:
                                data = json.loads(parts[1])
                                for item in data.get("Metadata", []):
                                    if item.get("Type") == "WordBoundary":
                                        d = item["Data"]
                                        offset_sec = (d["Offset"] / 10000.0) / 1000.0
                                        dur_sec = (d["Duration"] / 10000.0) / 1000.0
                                        word_text = d["text"]["Text"]
                                        words.append({
                                            "word": word_text,
                                            "start": round(offset_sec, 3),
                                            "end": round(offset_sec + dur_sec, 3),
                                            "duration": round(dur_sec, 3)
                                        })
                        elif "Path:turn.end" in msg:
                            break

            with open(output_file, "wb") as f:
                f.write(audio_data)

        except Exception as e:
            # Fallback to local flite / espeak if network drops
            print(f"[TTS Warning] Remote neural TTS failed ({e}), using local synthesis fallback.")
            wav_file = output_file.with_suffix(".wav")
            import shutil
            if shutil.which("flite"):
                subprocess.run(["flite", "-t", text, "-o", str(wav_file)], check=True)
            elif shutil.which("espeak-ng"):
                subprocess.run(["espeak-ng", "-w", str(wav_file), text], check=True)
            elif shutil.which("espeak"):
                subprocess.run(["espeak", "-w", str(wav_file), text], check=True)
            else:
                raise RuntimeError(f"Neural TTS failed ({e}) and no local speech synthesizer (flite/espeak) found.")
            output_file = wav_file

        # Get audio duration using ffprobe
        probe_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(output_file)
        ]
        proc = subprocess.run(probe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        duration = float(proc.stdout.strip()) if proc.stdout.strip() else 0.0

        # Fallback word estimation if word boundaries were not captured
        if not words and duration > 0:
            raw_tokens = [w for w in text.split() if w]
            if raw_tokens:
                step = duration / len(raw_tokens)
                for i, token in enumerate(raw_tokens):
                    w_start = round(i * step, 3)
                    w_end = round((i + 1) * step, 3)
                    words.append({
                        "word": token,
                        "start": w_start,
                        "end": w_end,
                        "duration": round(step, 3)
                    })

        return {
            "audio_file": str(output_file),
            "duration": duration,
            "words": words
        }

