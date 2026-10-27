# Video shot list: "Vibe to Production in 180 Seconds"

Length **2:58**, 1920×1080. The timeline lives in [`video/record.mjs`](../../video/record.mjs);
`cd video && npm install && node record.mjs` re-records every clip into `docs/video/clips/` (each walkthrough step is its own clip, cut
to its exact slot) and stitches a silent draft, `docs/video/draft-cut.mp4`. Add your own voice over the draft (calm,
confident), then upload as Public or Unlisted with both caption files:
[`captions.en.srt`](captions.en.srt) and [`captions.bn.srt`](captions.bn.srt).

Every number on screen is either cited (scene 01) or comes from our own eval run
(`eval/sathi_results_sathi_bn.v1.json`). The pilot has not started, so no pilot result is
claimed anywhere. Every product screen shows "Demo household — invented data".

## Before you record

1. **Replace the shelf placeholder (0:15–0:30)** with a real photo or short clip of a messy
   medicine shelf from a consenting family. The draft uses the demo shelf until then.
2. **Say one Bangla sentence on camera** (localisation is mandatory). Suggested, over the
   duplicate (1:09): *"নাম আলাদা, ওষুধ একই — তাই প্রতিটি ওষুধ একজন ফার্মাসিস্ট দেখে দেন।"*
3. **If the pilot starts before you record**, swap the 2:40 line for the real numbers
   ("In our pilot, N of M homes had a problem a doctor confirmed"). Never estimate.

## Timeline

| Time | Shot | Clip | On screen | Voiceover |
| --- | --- | --- | --- | --- |
| 0:00–0:15 | Scene 01 | `01-problem` | Three prescribers, one shelf; 78.28/1,000, 11%, 69% with sources | "Hypertension is now Bangladesh's most common illness, yet only about one in ten people with it has it under control." |
| 0:15–0:30 | Shelf | `shelf` (**placeholder**) | Demo shelf of strips; replace with a real family's shelf | "Our grandparents collect medicines from a hospital doctor, a village doctor and the local drug shop, under thousands of brand names. Nobody ever looks at the whole shelf." |
| 0:30–0:50 | Scene 02 | `02-solution` | "A pharmacist for every elderly home", four steps, Napa + Ace bracket | "OushodhSathi is a pharmacist for every elderly home. A family member photographs every medicine. We turn the pile into one doctor-checked list, in Bangla…" |
| 0:50–1:00 | Product | `landing` | The live landing page and hero animation | "…with a helper called Sathi, and a medicine passport for every doctor visit." |
| 1:00–1:04 | Demo · Scan | `demo-02-scan` | The shelf in the camera frame | "This is a demo household: Rahima Begum, sixty-eight. Her daughter photographs the shelf…" |
| 1:04–1:09 | Demo · The list | `demo-03-the-list` | Strip cards assemble | "…and the list builds itself." |
| 1:09–1:16 | Demo · Duplicate | `demo-04-duplicate` | Napa + Ace snap together, red bracket "দুটোই প্যারাসিটামল" | "Here: Napa and Ace. Different names, same medicine — paracetamol, twice." **(Bangla sentence here)** |
| 1:16–1:22 | Demo · Review | `demo-05-review` | Reviewer evidence, the AI summary marked "check the evidence", Confirmed | "A pharmacist checks the evidence, with an AI summary they must verify, and confirms it." |
| 1:22–1:27 | Demo · Family | `demo-06-family` | The confirmed finding on the daughter's phone, in Bangla | "Only then does the family see it, in simple Bangla." |
| 1:27–1:33 | Demo · Passport | `demo-07-passport` | Passport: what each medicine is for, allergy, prescribers | "The passport says what each medicine is for…" |
| 1:33–1:38 | Demo · Emergency | `demo-08-emergency` | QR → emergency page: first name, allergy, call button | "…and its QR opens an emergency page: no login, first name only." |
| 1:38–1:44 | Demo · Today | `demo-09-today` | Sunrise, sun, moon; tablets drawn; Listen | "For a mother who can't read, today's medicines are pictures, read aloud." |
| 1:44–1:48 | Demo · Report | `demo-10-report` | BP trend; 142/88 read from a photo of the machine | "Blood pressure can be read from a photo of the machine." |
| 1:48–1:53 | Demo · Sathi | `demo-11-sathi` | Next-step card; "ছবি ঝাপসা হলে?" answered from the app guide | "Sathi, our helper, always shows the next step…" |
| 1:53–1:59 | Demo · Ask a person | `demo-12-ask-a-person` | "Ace কি বন্ধ করে দেব?" → sent to the pharmacist → a person replies | "…and when Nusrat asks 'Should Ma stop Ace?', Sathi doesn't guess. It sends the question to the pharmacist." |
| 1:59–2:05 | Demo · Doctor visit | `demo-13-doctor-visit` | One printable page: what changed, questions, BP | "Before every visit, one page shows what changed, and who changed it." |
| 2:05–2:15 | Scene 03 | `03-architecture` | Photo → vision → brand → rules → clinician → family | "AI does perception: a vision model reads cut strips and prescriptions; unknown brands must cite a source." |
| 2:15–2:30 | Scene 04 | `04-ai-approach` | What models do / never do; Sathi test 30/30, 10/10, 5/5, 34/35 | "Rules and humans do judgement: a deterministic engine checks every list, and a clinician confirms every flag. In our eighty-question safety test, Sathi sent all thirty medical questions to a pharmacist, and every emergency to 999." |
| 2:30–2:40 | Scene 05 | `05-families` | Six tiles: Sathi, Today, Emergency QR, visit, set aside, BP photo | "It's built for parents who can't read, and children far away." |
| 2:40–2:50 | Scene 06 | `06-impact` | Families abroad pay; pilot (honest); next steps | "Families abroad pay; parents stay safe. We are now recruiting our first pilot families, and will publish results only when they are real." |
| 2:50–2:58 | Scene 07 | `07-close` | "Build locally, protect globally" and the passport card | "OushodhSathi. Build locally, protect globally." |

## Full voiceover (≈ 330 words, about 2:50 at a calm pace)

> Hypertension is now Bangladesh's most common illness, yet only about one in ten people with it
> has it under control. Our grandparents collect medicines from a hospital doctor, a village
> doctor and the local drug shop, under thousands of brand names. Nobody ever looks at the whole
> shelf.
>
> OushodhSathi is a pharmacist for every elderly home. A family member photographs every
> medicine. We turn the pile into one doctor-checked list, in Bangla, with a helper called Sathi
> and a medicine passport for every doctor visit.
>
> This is a demo household: Rahima Begum, sixty-eight. Her daughter photographs the shelf, and
> the list builds itself. Here: Napa and Ace. Different names, same medicine: paracetamol, twice.
> *নাম আলাদা, ওষুধ একই — তাই প্রতিটি ওষুধ একজন ফার্মাসিস্ট দেখে দেন।* A pharmacist checks the
> evidence, with an AI summary they must verify, and confirms it. Only then does the family see
> it, in simple Bangla. The passport says what each medicine is for, and its QR opens an
> emergency page: no login, first name only. For a mother who can't read, today's medicines are
> pictures, read aloud. Blood pressure can be read from a photo of the machine. Sathi, our
> helper, always shows the next step, and when Nusrat asks "Should Ma stop Ace?", Sathi doesn't
> guess. It sends the question to the pharmacist. Before every visit, one page shows what
> changed, and who changed it.
>
> AI does perception: a vision model reads cut strips and prescriptions, and unknown brands must
> cite a source. Rules and humans do judgement: a deterministic engine checks every list, and a
> clinician confirms every flag. In our eighty-question safety test, Sathi sent all thirty
> medical questions to a pharmacist, and every emergency to 999.
>
> It's built for parents who can't read, and children far away. Families abroad pay; parents
> stay safe. We are now recruiting our first pilot families, and will publish results only when
> they are real.
>
> OushodhSathi. Build locally, protect globally.

## Rules this cut keeps

- Real numbers only: the three problem statistics are cited on scene 01; the Sathi numbers are
  our own eval. "Thousands of brand names", not an uncited exact count. No review-time claim
  until reviews have been timed in the pilot.
- The product is shown working (65 seconds of the walkthrough), not only slides.
- One Bangla sentence is spoken; all captions exist in Bangla and English.
- It ends on the passport card, not a logo.
