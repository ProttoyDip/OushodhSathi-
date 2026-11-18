"""Generate the check-in call's Bangla audio prompts ONCE, from the script of record.

  python backend/scripts/make_call_audio.py --engine azure     # production voice (needs a key)
  python backend/scripts/make_call_audio.py --engine mms       # local draft voice (no key)

Writes frontend/public/audio/call/<id>.mp3 for every prompt in app/voice_calls/script.py, plus
manifest.json recording the engine, voice, licence and the exact words. No live TTS ever runs during a
call: these files are generated once, then a native speaker must listen to each one and set
"checked_by_native_speaker" in the manifest (or replace the file with a recording).

Digits are spoken as words ("১ চাপুন" -> "এক চাপুন"): a TTS model may skip a digit it does not know, and
a call that loses "press 1" is useless. The on-screen text keeps the digits.

Engines
- azure: Azure AI Speech, voice bn-BD-NabanitaNeural (Bangla, Bangladesh) by default.
  REST: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/rest-text-to-speech
    POST https://<region>.tts.speech.microsoft.com/cognitiveservices/v1, headers
    Ocp-Apim-Subscription-Key, Content-Type: application/ssml+xml,
    X-Microsoft-OutputFormat: audio-24khz-48kbitrate-mono-mp3, User-Agent.
  Voices: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts
  Keys: AZURE_SPEECH_KEY, AZURE_SPEECH_REGION (names only in backend/.env.example).
- mms: Meta MMS-TTS facebook/mms-tts-ben, run locally with transformers (VitsModel).
  https://huggingface.co/facebook/mms-tts-ben  Licence: CC-BY-NC 4.0 (non-commercial only), so these
  are draft prompts for the pilot and the demo; replace them before any commercial use. Needs torch +
  transformers (not in the app's requirements) and ffmpeg (FFMPEG env var or on PATH) for MP3.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import wave
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.voice_calls.script import PROMPTS  # noqa: E402

OUT = ROOT / "frontend" / "public" / "audio" / "call"
_WORDS = {"০": "শূন্য", "১": "এক", "২": "দুই", "৩": "তিন", "৪": "চার", "৫": "পাঁচ", "৬": "ছয়", "৭": "সাত", "৮": "আট", "৯": "নয়"}


def spoken(text: str) -> str:
    """Bangla digits as words, one digit at a time ("৯৯৯" -> "নয় নয় নয়"), hyphen-suffixes dropped."""
    out, i = [], 0
    while i < len(text):
        ch = text[i]
        if ch in _WORDS:
            j = i
            while j < len(text) and text[j] in _WORDS:
                j += 1
            out.append(" ".join(_WORDS[d] for d in text[i:j]))
            if text[j:j + 2] == "-এ":   # "৯৯৯-এ ফোন করুন": a number takes "নম্বরে" when spoken
                j += 2
                out.append(" নম্বরে")
            i = j
        else:
            out.append(ch)
            i += 1
    return " ".join("".join(out).split())


def azure(text: str, voice: str) -> bytes:
    import httpx

    key, region = os.getenv("AZURE_SPEECH_KEY", "").strip(), os.getenv("AZURE_SPEECH_REGION", "").strip()
    if not key or not region:
        sys.exit("Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION in backend/.env (see .env.example).")
    ssml = (f"<speak version='1.0' xml:lang='bn-BD'><voice xml:lang='bn-BD' name='{voice}'>"
            f"{escape(text)}</voice></speak>")
    r = httpx.post(f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1", content=ssml.encode("utf-8"),
                   headers={"Ocp-Apim-Subscription-Key": key, "Content-Type": "application/ssml+xml",
                            "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
                            "User-Agent": "oushodhsathi-call-audio"}, timeout=30)
    r.raise_for_status()
    return r.content


class Mms:
    def __init__(self) -> None:
        try:
            import torch
            from transformers import AutoTokenizer, VitsModel
        except ImportError:
            sys.exit("The mms engine needs torch and transformers: pip install torch transformers")
        self.torch = torch
        self.model = VitsModel.from_pretrained("facebook/mms-tts-ben")
        self.tok = AutoTokenizer.from_pretrained("facebook/mms-tts-ben")
        self.ffmpeg = os.getenv("FFMPEG") or shutil.which("ffmpeg")
        if not self.ffmpeg:
            sys.exit("The mms engine needs ffmpeg to write MP3: set FFMPEG or put ffmpeg on PATH")

    def unknown_chars(self, text: str) -> set[str]:
        vocab = self.tok.get_vocab()
        return {c for c in text if not c.isspace() and c not in vocab and c not in "।,"}

    def __call__(self, text: str) -> bytes:
        torch = self.torch
        torch.manual_seed(7)  # VITS is stochastic: the same words give the same file
        with torch.no_grad():
            wav = self.model(**self.tok(text, return_tensors="pt")).waveform[0].numpy()
        pcm = (wav.clip(-1, 1) * 32767).astype("<i2").tobytes()
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(self.model.config.sampling_rate)
            w.writeframes(pcm)
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp) / "a.wav", Path(tmp) / "a.mp3"
            src.write_bytes(buf.getvalue())
            subprocess.run([self.ffmpeg, "-loglevel", "error", "-y", "-i", str(src), "-ac", "1", "-b:a", "64k", str(dst)],
                           check=True)
            return dst.read_bytes()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["azure", "mms"], required=True)
    ap.add_argument("--voice", default="bn-BD-NabanitaNeural", help="Azure voice name")
    a = ap.parse_args()
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / "backend" / ".env")
    except ImportError:
        pass
    OUT.mkdir(parents=True, exist_ok=True)
    engine = Mms() if a.engine == "mms" else None
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "engine": a.engine,
        "voice": a.voice if a.engine == "azure" else "facebook/mms-tts-ben",
        "licence": ("Azure AI Speech output (your Azure terms)" if a.engine == "azure"
                    else "CC-BY-NC 4.0 (MMS-TTS): non-commercial only; replace before commercial use"),
        "checked_by_native_speaker": False,
        "prompts": {},
    }
    for pid, texts in PROMPTS.items():
        say = spoken(texts["bn"])
        if engine is not None and (bad := engine.unknown_chars(say)):
            print(f"  warning {pid}: the model has no symbol for {''.join(sorted(bad))!r}")
        audio = azure(say, a.voice) if engine is None else engine(say)
        (OUT / f"{pid}.mp3").write_bytes(audio)
        manifest["prompts"][pid] = {"screen": texts["bn"], "spoken": say, "file": f"{pid}.mp3", "bytes": len(audio)}
        print(f"  {pid}.mp3  {len(audio) // 1024} KB  «{say}»")
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(PROMPTS)} files to {OUT}. A native speaker must now listen to each one.")


if __name__ == "__main__":
    main()
