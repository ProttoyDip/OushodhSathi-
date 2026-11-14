// Records the microphone as 16 kHz mono 16-bit WAV, in memory only. WAV because the speech service
// (Riva, Whisper large-v3) does not accept the browser's usual WebM; 16 kHz keeps 30 seconds under 1 MB.

const TARGET_RATE = 16_000;
export const MAX_SECONDS = 30;

export type Recording = { stop: () => Promise<Blob>; cancel: () => void };

export async function startWavRecording(onLimit?: () => void): Promise<Recording> {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } });
  const Ctx = window.AudioContext ?? (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
  const ctx = new Ctx();
  const source = ctx.createMediaStreamSource(stream);
  // ScriptProcessor is old but works everywhere we need; the audio never leaves this function until stop()
  const node = ctx.createScriptProcessor(4096, 1, 1);
  const chunks: Float32Array[] = [];
  let samples = 0;
  const limit = MAX_SECONDS * ctx.sampleRate;
  node.onaudioprocess = (e) => {
    if (samples >= limit) return;
    const data = new Float32Array(e.inputBuffer.getChannelData(0));
    chunks.push(data);
    samples += data.length;
    if (samples >= limit) onLimit?.();
  };
  source.connect(node);
  node.connect(ctx.destination);

  const release = () => {
    node.disconnect();
    source.disconnect();
    stream.getTracks().forEach((t) => t.stop());
    void ctx.close();
  };

  return {
    cancel: release,
    stop: async () => {
      release();
      const mono = new Float32Array(Math.min(samples, limit));
      let offset = 0;
      for (const c of chunks) {
        const take = Math.min(c.length, mono.length - offset);
        mono.set(c.subarray(0, take), offset);
        offset += take;
        if (offset >= mono.length) break;
      }
      return encodeWav(downsample(mono, ctx.sampleRate, TARGET_RATE), TARGET_RATE);
    },
  };
}

function downsample(input: Float32Array, from: number, to: number): Float32Array {
  if (from <= to) return input;
  const ratio = from / to;
  const out = new Float32Array(Math.floor(input.length / ratio));
  for (let i = 0; i < out.length; i++) {
    // average the source samples this output sample covers (a simple low-pass)
    const start = Math.floor(i * ratio);
    const end = Math.min(Math.floor((i + 1) * ratio), input.length);
    let sum = 0;
    for (let j = start; j < end; j++) sum += input[j];
    out[i] = sum / Math.max(end - start, 1);
  }
  return out;
}

function encodeWav(samples: Float32Array, rate: number): Blob {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const v = new DataView(buffer);
  const text = (o: number, s: string) => [...s].forEach((ch, i) => v.setUint8(o + i, ch.charCodeAt(0)));
  text(0, "RIFF");
  v.setUint32(4, 36 + samples.length * 2, true);
  text(8, "WAVE");
  text(12, "fmt ");
  v.setUint32(16, 16, true);
  v.setUint16(20, 1, true); // PCM
  v.setUint16(22, 1, true); // mono
  v.setUint32(24, rate, true);
  v.setUint32(28, rate * 2, true);
  v.setUint16(32, 2, true);
  v.setUint16(34, 16, true);
  text(36, "data");
  v.setUint32(40, samples.length * 2, true);
  samples.forEach((s, i) => v.setInt16(44 + i * 2, Math.max(-1, Math.min(1, s)) * 0x7fff, true));
  return new Blob([buffer], { type: "audio/wav" });
}
