# Check-in call audio

One MP3 per prompt, named by its id. The words are the script of record in
[`backend/app/voice_calls/script.py`](../../../../backend/app/voice_calls/script.py); change them there first.

| File | Bangla |
| --- | --- |
| `greeting.mp3` | আসসালামু আলাইকুম, ওষুধসাথী থেকে বলছি। |
| `slot_morning.mp3` | সকালের ওষুধ খেয়ে থাকলে ১ চাপুন, না খেলে ২ চাপুন। |
| `slot_noon.mp3` | দুপুরের ওষুধ খেয়ে থাকলে ১ চাপুন, না খেলে ২ চাপুন। |
| `slot_night.mp3` | রাতের ওষুধ খেয়ে থাকলে ১ চাপুন, না খেলে ২ চাপুন। |
| `emergency_ask.mp3` | বুকে ব্যথা, শ্বাসকষ্ট বা অজ্ঞান হওয়ার মতো সমস্যা হলে ৯ চাপুন। |
| `emergency.mp3` | এখনই ৯৯৯-এ ফোন করুন বা কাছের হাসপাতালে যান। |
| `closing.mp3` | ধন্যবাদ। কোনো প্রশ্ন থাকলে ফার্মাসিস্টকে জিজ্ঞেস করুন। |

**Status: not recorded yet.** Until the files exist, the simulator shows the words on screen and says
the audio is not ready. Record them with a team member's voice, or generate them once with a TTS tool
and have a native speaker check each file. Never use live TTS during a call. Keep each file short
(mono, 16 kHz or higher), with no names and no music.
