"""Bangla voice input: /sathi/transcribe (Whisper large-v3 via NVIDIA, gRPC client mocked)."""
import builtins
import io
import struct
import sys
import types
import wave

import pytest

from app import asr


def wav(seconds=2.0, rate=16000):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * int(seconds * rate))
    return buf.getvalue()


def ogg(seconds):
    """Two minimal Ogg pages; the last one's granule position says how long the audio is."""
    page = lambda granule: b"OggS\x00\x00" + struct.pack("<q", granule) + b"\x00" * 14  # noqa: E731
    return page(0) + page(int(seconds * asr.OPUS_RATE))


@pytest.fixture
def fake_riva(monkeypatch):
    """Replaces riva.client with a fake that records the call and returns a transcript."""
    calls = {}

    class Alt:
        def __init__(self, text):
            self.transcript = text

    class Result:
        def __init__(self, text):
            self.alternatives = [Alt(text)]

    class Future:
        def result(self, timeout=None):
            calls["timeout"] = timeout
            if calls.get("fail"):
                raise RuntimeError("UNAVAILABLE")
            return types.SimpleNamespace(results=[Result(calls.get("text", "মা শ্বাস নিতে পারছে না"))])

    class ASRService:
        def __init__(self, auth):
            calls["auth"] = auth

        def offline_recognize(self, data, config, future=False):
            calls.update(bytes=len(data), config=config, future=future)
            return Future()

    client = types.ModuleType("riva.client")
    client.Auth = lambda **kw: kw
    client.RecognitionConfig = lambda **kw: kw
    client.AudioEncoding = types.SimpleNamespace(LINEAR_PCM="LINEAR_PCM", OGGOPUS="OGGOPUS")
    client.ASRService = ASRService
    pkg = types.ModuleType("riva")
    pkg.client = client
    monkeypatch.setitem(sys.modules, "riva", pkg)
    monkeypatch.setitem(sys.modules, "riva.client", client)
    monkeypatch.setenv("NVIDIA_API_KEY", "nv-key")
    monkeypatch.setenv("NVIDIA_ASR_FUNCTION_ID", "fn-123")
    return calls


def post(client, data, content_type="audio/wav", **form):
    return client.post("/sathi/transcribe", files={"audio": ("speech", data, content_type)}, data={"lang": "bn", **form})


def test_transcribes_wav_in_bangla(client, fake_riva):
    r = post(client, wav(2))
    assert r.status_code == 200 and r.json() == {"text": "মা শ্বাস নিতে পারছে না"}
    cfg = fake_riva["config"]
    assert cfg["language_code"] == "bn" and cfg["encoding"] == "LINEAR_PCM" and cfg["sample_rate_hertz"] == 16000
    assert fake_riva["future"] is True and fake_riva["timeout"] == asr.TIMEOUT_S
    assert fake_riva["auth"]["uri"] == asr.DEFAULT_SERVER and fake_riva["auth"]["use_ssl"] is True
    assert ["function-id", "fn-123"] in fake_riva["auth"]["metadata_args"]


def test_limits_on_size_duration_and_format(client, fake_riva):
    assert post(client, wav(31)).status_code == 413                       # over 30 seconds
    assert post(client, b"\x00" * (asr.MAX_BYTES + 10)).status_code == 413  # over 2 MB
    assert post(client, b"\x1a\x45\xdf\xa3webm", "audio/webm").status_code == 415  # Riva takes no WebM
    assert post(client, b"hello", "text/plain").status_code == 415
    assert post(client, ogg(31), "audio/ogg").status_code == 413
    ok = post(client, ogg(3), "audio/ogg")
    assert ok.status_code == 200 and fake_riva["config"]["encoding"] == "OGGOPUS"


def test_503_when_not_configured_or_failing(client, fake_riva, monkeypatch):
    fake_riva["fail"] = True
    assert post(client, wav(1)).status_code == 503       # service error -> browser fallback
    monkeypatch.setenv("NVIDIA_ASR_FUNCTION_ID", "")
    assert post(client, wav(1)).status_code == 503       # not configured
    assert client.get("/health").json()["voice"] is False


def test_audio_is_never_written_to_disk(client, fake_riva, monkeypatch, tmp_path):
    real_open = builtins.open
    writes = []

    def guarded_open(file, mode="r", *a, **kw):
        if any(m in mode for m in ("w", "a", "x")):
            writes.append(str(file))
        return real_open(file, mode, *a, **kw)

    monkeypatch.setattr(builtins, "open", guarded_open)
    before = set(tmp_path.parent.iterdir())
    assert post(client, wav(2)).status_code == 200
    assert writes == [] and set(tmp_path.parent.iterdir()) == before


def test_household_must_match_when_given(client, fake_riva):
    r = client.post("/patients", json={"name": "Voice", "age": 70, "consent": True}).json()
    assert post(client, wav(1), patient_id=str(r["id"])).status_code == 404  # no family key
    ok = client.post("/sathi/transcribe", files={"audio": ("s", wav(1), "audio/wav")},
                     data={"lang": "bn", "patient_id": str(r["id"])}, headers={"X-Family-Key": r["family_key"]})
    assert ok.status_code == 200


def test_transcript_goes_through_the_guard_like_typed_text(client, fake_riva):
    """The transcript is only text for the box: asking it goes the normal way, guard first."""
    r = client.post("/patients", json={"name": "Voice", "age": 70, "consent": True}).json()
    h = {"X-Family-Key": r["family_key"]}
    text = client.post("/sathi/transcribe", files={"audio": ("s", wav(1), "audio/wav")},
                       data={"lang": "bn", "patient_id": str(r["id"])}, headers=h).json()["text"]
    reply = client.post("/assistant/ask", json={"patient_id": r["id"], "question": text, "lang": "bn"}, headers=h).json()
    assert reply["kind"] == "emergency"  # breathing words: the fixed emergency message, no model
    fake_riva["text"] = "বুকে খুব ব্যথা করছে"
    text = client.post("/sathi/transcribe", files={"audio": ("s", wav(1), "audio/wav")},
                       data={"lang": "bn", "patient_id": str(r["id"])}, headers=h).json()["text"]
    reply = client.post("/assistant/ask", json={"patient_id": r["id"], "question": text, "lang": "bn"}, headers=h).json()
    assert reply["kind"] in ("emergency", "medical_redirect")  # never answered from the app guide or a model


def test_transcribe_is_rate_limited(client, fake_riva, monkeypatch):
    monkeypatch.setenv("SATHI_LIMIT_PER_IP", "2")
    codes = [post(client, wav(1)).status_code for _ in range(3)]
    assert codes == [200, 200, 429]
