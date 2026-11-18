# Daily check-ins: phone call and WhatsApp message

Once a day, at a time the family chooses, OushodhSathi asks whether the pharmacist-approved medicines were
taken. It asks by a short recorded Bangla phone call, or by a WhatsApp message with buttons. Both run in a
browser simulator today; this guide explains how they work and what is needed to switch each one on for real.

## What both channels share

- **Consent first.**
  - **What the family gives:** in Settings they choose the channel, read the consent text, say who is agreeing, and pick a time.
  - **What is stored:** the consent time and who gave it.
  - **Stopping:** turns the check-in off and erases the number at once.
- **The number** is needed only for a real provider.
  - It is a Bangladeshi mobile number, stored encrypted (Fernet, `PHONE_ENCRYPTION_KEY`), shown masked, and masked in the export.
  - It goes only to the call provider or to WhatsApp, never to an AI model.
- **Quiet hours:** never between 21:00 and 08:00 Bangladesh time. Times can be set from 08:00 to 20:45.
- **Answers become dose ticks** for each pharmacist-approved medicine in that slot, marked `source=call` or `source=whatsapp`. The pharmacist sees them in adherence and in the check-in history.
- **Emergency:** "9" on the call, or the emergency button or emergency words on WhatsApp, gives the fixed message "এখনই ৯৯৯-এ ফোন করুন বা কাছের হাসপাতালে যান।" and alerts the family contact (`N8N_ALERT_WEBHOOK`, ids only).
- **No AI and no advice.** Every word is fixed Bangla, checked by the same safety filter as the explanations. After "not taken", nothing is said; the answer is only recorded.
- **Missed check-ins:** 3 of the last 5 unanswered adds one point ("calls_missed") to the household's place in the reviewer queue.
- **Export and delete** cover the schedule and every check-in.

## The phone call (IVR)

Code: [`backend/app/voice_calls/`](../backend/app/voice_calls).

```text
greeting → for each approved slot: "সকালের ওষুধ খেয়ে থাকলে ১ চাপুন, না খেলে ২ চাপুন।" → "...সমস্যা হলে ৯ চাপুন।" → closing
```

- **Keys:** 1 is taken, 2 is not taken, 9 is emergency. With no key, the call repeats the question once, then moves on without recording anything.
- **Scheduling:** `POST /calls/run-due` (admin token), called by the GitHub Actions workflow [`check-in-calls.yml`](../.github/workflows/check-in-calls.yml) every 15 minutes. That workflow stays off until the repository variable `CALLS_ENABLED=true` is set.
  - One retry 15 minutes after an unanswered call, and at most two attempts a day.
  - Running it twice never places a call twice.
- **Provider interface:** `place_call`, `parse_webhook` and `verify_signature`.
  - The simulator is the default adapter and never dials.
  - Real callbacks arrive at `POST /calls/webhook/{provider}`, which checks the signature first, refuses unknown calls, and ignores repeated deliveries (by `seq`).
- **Audio:** seven MP3 prompts in [`frontend/public/audio/call/`](../frontend/public/audio/call), generated once by [`backend/scripts/make_call_audio.py`](../backend/scripts/make_call_audio.py). Digits are spoken as words, so the key to press is never dropped.
  - **Draft voice:** Meta MMS-TTS, licensed **CC-BY-NC 4.0 (non-commercial)**.
  - **Production voice:** Azure `bn-BD-NabanitaNeural` (`--engine azure`, with `AZURE_SPEECH_KEY` and `AZURE_SPEECH_REGION`), or a team member's recording.
  - **Before real calls:** a native speaker must listen to each file and set `checked_by_native_speaker` in `manifest.json`.

**To go live:**

1. **Choose a provider** that can call Bangladeshi mobiles with key presses and webhooks. Prices to Bangladesh mobile, from their own pricing pages in November 2026:
   - Plivo: $0.046/min
   - Twilio: $0.06/min
   - Telnyx: base rate plus a destination fee it doesn't publish
   - Ask the provider about BTRC licensing and caller ID.
2. **Add its adapter** next to `simulator.py`, implementing the three interface methods from the provider's current docs.
3. **Set the configuration:** `CALL_PROVIDER`, the provider's keys, `PUBLIC_API_URL` and `PHONE_ENCRYPTION_KEY` on Render.
4. **Switch on the cron:** set `CALLS_ENABLED=true` in the GitHub repository variables and `ADMIN_TOKEN` as a secret.

## The WhatsApp message

Code: [`backend/app/whatsapp_checkin/`](../backend/app/whatsapp_checkin).

```text
template (paid, once a day): "আজকের ওষুধগুলো কি খাওয়া হয়েছে?"  [সব খেয়েছি] [কিছু বাদ গেছে] [জরুরি সমস্যা]
  সব খেয়েছি      → every approved slot recorded as taken → closing
  কিছু বাদ গেছে   → for each slot: "সকালের ওষুধ কি খাওয়া হয়েছে?" [খেয়েছি] [খাইনি] [জরুরি]  (free: inside the 24-hour window)
  জরুরি সমস্যা    → the fixed 999 message + alert
```

- **One paid message a day.** The tap opens WhatsApp's 24-hour customer service window, so the follow-ups are free service messages. There is no retry; no reply in 12 hours counts as unanswered.
- **Matching replies:** each reply is matched to the message it answers (`context.id`), not by phone number, and each incoming message id is handled once.
- **Webhook security:**
  - `GET /whatsapp/webhook` answers Meta's subscription check (`hub.challenge` with `WHATSAPP_VERIFY_TOKEN`).
  - `POST /whatsapp/webhook` checks `X-Hub-Signature-256`, an HMAC-SHA256 of the raw body with `WHATSAPP_APP_SECRET`, before reading anything.
- **Typed messages** are not stored and never reach a model.
  - Emergency words get the 999 reply, even from someone not linked to a household.
  - Anything else gets "please tap a button".
- Limits from Meta's docs: up to 3 reply buttons, titles up to 20 characters (template quick replies up to 25).

**To go live:**

1. **Business account:** create a verified Meta business account and a WhatsApp Business phone number on the Cloud API.
2. **Configuration:** set `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_APP_SECRET`, `WHATSAPP_VERIFY_TOKEN` and `PHONE_ENCRYPTION_KEY` on Render.
3. **Template:** submit it with `python backend/scripts/create_whatsapp_template.py` (needs `WHATSAPP_BUSINESS_ACCOUNT_ID`; `--dry-run` prints the request) and wait for Meta's approval.
4. **Webhook:** in the Meta app, set the URL to `https://<api>/whatsapp/webhook` with the same verify token, and subscribe to the `messages` field.
5. **Cron:** switch on the check-in cron as for the call. The same `POST /calls/run-due` sends the daily WhatsApp message to households that chose it.

## Trying it

- **Phone call:** turn it on in Settings, then open `/p/{id}/call` (or [`/call-demo`](https://oushodhsathi.vercel.app/call-demo) for the demo household) and press "Ring now (test)".
- **WhatsApp:** choose "হোয়াটসঅ্যাপ মেসেজ" in Settings; `/p/{id}/call` then shows the chat simulator with "Send today's message (test)".
- **Tests:** [`backend/tests/test_calls.py`](../backend/tests/test_calls.py) and [`test_whatsapp_checkin.py`](../backend/tests/test_whatsapp_checkin.py) cover:
  - every branch;
  - consent;
  - quiet hours, the retry and the daily cap;
  - signatures and repeated webhook deliveries;
  - export and delete.
