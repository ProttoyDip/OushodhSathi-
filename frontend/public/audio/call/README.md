# Check-in call audio

One MP3 per prompt, named by its id. The words are the script of record in
[`backend/app/voice_calls/script.py`](../../../../backend/app/voice_calls/script.py); change them there first,
then regenerate. Never use live TTS during a call.

| File | Bangla (on screen) |
| --- | --- |
| `greeting.mp3` | আসসালামু আলাইকুম, ওষুধসাথী থেকে বলছি। |
| `slot_morning.mp3` | সকালের ওষুধ খেয়ে থাকলে ১ চাপুন, না খেলে ২ চাপুন। |
| `slot_noon.mp3` | দুপুরের ওষুধ খেয়ে থাকলে ১ চাপুন, না খেলে ২ চাপুন। |
| `slot_night.mp3` | রাতের ওষুধ খেয়ে থাকলে ১ চাপুন, না খেলে ২ চাপুন। |
| `emergency_ask.mp3` | বুকে ব্যথা, শ্বাসকষ্ট বা অজ্ঞান হওয়ার মতো সমস্যা হলে ৯ চাপুন। |
| `emergency.mp3` | এখনই ৯৯৯-এ ফোন করুন বা কাছের হাসপাতালে যান। |
| `closing.mp3` | ধন্যবাদ। কোনো প্রশ্ন থাকলে ফার্মাসিস্টকে জিজ্ঞেস করুন। |

## Generate

```sh
python backend/scripts/make_call_audio.py --engine azure   # Azure bn-BD voice (AZURE_SPEECH_KEY, AZURE_SPEECH_REGION)
python backend/scripts/make_call_audio.py --engine mms     # local draft voice, no key (needs torch, transformers, ffmpeg)
```

Digits are spoken as words ("১ চাপুন" is said "এক চাপুন", "৯৯৯-এ" is said "নয় নয় নয় নম্বরে"), so no model
can drop the key to press. [`manifest.json`](manifest.json) records the engine, voice, licence and the
exact words of every file.

## Before real calls

- **A native speaker must listen to every file** and set `"checked_by_native_speaker": true` in the
  manifest, or replace the file with a recording of a team member's voice.
- **Licence:** files made with `--engine mms` (Meta MMS-TTS) are **CC-BY-NC 4.0, non-commercial only**.
  They are fine for the free pilot and the demo; regenerate with Azure, or record them, before any paid use.
