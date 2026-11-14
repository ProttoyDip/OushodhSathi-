"""Bangla speech to text with OpenAI Whisper large-v3, hosted by NVIDIA (build.nvidia.com).

NVIDIA serves it through the Riva gRPC API (not an OpenAI-style REST endpoint), offline mode only.
Per the build.nvidia.com example (https://build.nvidia.com/openai/whisper-large-v3/api) and the
NIM docs (https://docs.nvidia.com/nim/speech/latest/asr/deploy-asr-models/whisper.html):
  server  grpc.nvcf.nvidia.com:443 with SSL
  metadata  function-id: <the model's function id>, authorization: Bearer <NVIDIA_API_KEY>
Configure NVIDIA_ASR_FUNCTION_ID (and NVIDIA_ASR_SERVER to override the server) in backend/.env.

Privacy: audio is handled in memory only and never written to disk or logged. The transcript is
returned to the family to read and edit; it reaches a model only through the normal Sathi path,
where guard.py runs first and patient names are redacted.
"""
from __future__ import annotations

import io
import logging
import os
import struct
import wave
from dataclasses import dataclass

log = logging.getLogger("oushodh.asr")

DEFAULT_SERVER = "grpc.nvcf.nvidia.com:443"
MAX_SECONDS = 30
MAX_BYTES = 2 * 1024 * 1024
TIMEOUT_S = 15
OPUS_RATE = 48_000  # Ogg Opus granule positions always count 48 kHz samples (RFC 7845)


class AsrUnavailable(RuntimeError):
    """Not configured, or the service failed: the app falls back to the browser's recognition."""


class AudioRejected(ValueError):
    """Wrong format, too long or too large."""


@dataclass(frozen=True)
class Audio:
    encoding: str          # "LINEAR_PCM" | "OGGOPUS"
    data: bytes            # raw PCM frames for WAV, the whole stream for Ogg Opus
    sample_rate: int
    channels: int
    seconds: float


def _env(name: str) -> str:
    return os.getenv(name, "").split("#", 1)[0].strip()


def configured() -> bool:
    return bool(_env("NVIDIA_API_KEY") and _env("NVIDIA_ASR_FUNCTION_ID"))


def parse_audio(data: bytes, content_type: str) -> Audio:
    """Validates and unpacks an upload in memory. WAV (PCM) and Ogg Opus only: Riva does not
    accept WebM, so the app records WAV."""
    if len(data) > MAX_BYTES:
        raise AudioRejected("too_large")
    kind = (content_type or "").split(";")[0].strip().lower()
    if data[:4] == b"RIFF" or kind in ("audio/wav", "audio/x-wav", "audio/wave"):
        try:
            with wave.open(io.BytesIO(data), "rb") as w:
                rate, channels, frames = w.getframerate(), w.getnchannels(), w.getnframes()
                if w.getsampwidth() != 2:
                    raise AudioRejected("wav_must_be_16bit")
                pcm = w.readframes(frames)
        except (wave.Error, EOFError) as e:
            raise AudioRejected("bad_wav") from e
        seconds = frames / rate if rate else 0
        audio = Audio("LINEAR_PCM", pcm, rate, channels, seconds)
    elif data[:4] == b"OggS" or kind in ("audio/ogg", "audio/opus"):
        last = data.rfind(b"OggS")
        if last < 0 or len(data) < last + 14:
            raise AudioRejected("bad_ogg")
        granule = struct.unpack_from("<q", data, last + 6)[0]
        audio = Audio("OGGOPUS", data, OPUS_RATE, 1, max(granule, 0) / OPUS_RATE)
    elif kind in ("audio/webm", "video/webm") or data[:4] == b"\x1a\x45\xdf\xa3":
        raise AudioRejected("webm_not_supported")
    else:
        raise AudioRejected("unsupported_format")
    if audio.seconds > MAX_SECONDS:
        raise AudioRejected("too_long")
    return audio


def transcribe(audio: Audio, lang: str = "bn") -> str:
    """Offline recognition with Whisper large-v3. Raises AsrUnavailable on any failure."""
    if not configured():
        raise AsrUnavailable("not configured")
    try:
        import riva.client as rc
    except ImportError as e:  # the package is in requirements.txt; this guards a partial install
        raise AsrUnavailable("riva client not installed") from e
    try:
        auth = rc.Auth(uri=_env("NVIDIA_ASR_SERVER") or DEFAULT_SERVER, use_ssl=True, metadata_args=[
            ["function-id", _env("NVIDIA_ASR_FUNCTION_ID")],
            ["authorization", f"Bearer {_env('NVIDIA_API_KEY')}"],
        ])
        config = rc.RecognitionConfig(
            encoding=getattr(rc.AudioEncoding, audio.encoding),
            sample_rate_hertz=audio.sample_rate,
            audio_channel_count=audio.channels,
            language_code="bn" if lang == "bn" else "en",
            max_alternatives=1,
            enable_automatic_punctuation=True,
        )
        future = rc.ASRService(auth).offline_recognize(audio.data, config, future=True)
        response = future.result(timeout=TIMEOUT_S)
    except Exception as e:  # noqa: BLE001 - any transport or service error means "fall back"
        log.warning("speech recognition failed: %s", type(e).__name__)  # never the audio, never the text
        raise AsrUnavailable(type(e).__name__) from e
    parts = [r.alternatives[0].transcript.strip() for r in response.results if r.alternatives]
    return " ".join(p for p in parts if p).strip()
