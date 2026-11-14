"""Writes the seven 1920x1080 video scenes. Run: python video/scenes/build_scenes.py

Real, cited numbers only. Our own numbers come from eval/ (sathi_results_*.json); the
pilot has not started, so no pilot result appears here.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
MARK = (HERE / "_mark.svg.txt").read_text().strip()
TOTAL = 7


def page(n: int, slug: str, title: str, body: str, foot_left: str = "") -> None:
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=1920">
<title>{title} · OushodhSathi</title><link rel="stylesheet" href="scenes.css"></head>
<body><main class="scene">
<header class="topbar"><div class="mark">{MARK}<span class="bn-display" lang="bn">ওষুধসাথী</span><span class="display">OushodhSathi</span></div>
<span class="step tab">{n:02d} / {TOTAL:02d} · {title}</span></header>
{body}
<footer class="foot"><span>{foot_left}</span><span>International AI Builders Congress 2026 · HealthSphere AI</span></footer>
</main></body></html>
"""
    (HERE / f"{n:02d}-{slug}.html").write_text(html, encoding="utf-8")


# the latest Sathi safety eval (guard + guide retrieval, as run in CI)
runs = sorted((ROOT / "eval").glob("sathi_results_*.json"))
SATHI = json.loads(runs[-1].read_text(encoding="utf-8"))["by_category"] if runs else None


def score(cat: str) -> str:
    s = SATHI[cat]
    return f'{s["correct"]}<span style="font-size:.45em;color:var(--ink-faint)"> / {s["n"]}</span>'


for old in HERE.glob("0*-*.html"):
    old.unlink()  # scene numbers moved when the families scene was added

page(1, "problem", "The problem", """
<div style="margin-top:70px">
  <p class="kicker rise">The problem · সমস্যা</p>
  <h1 class="display rise d1" style="font-size:104px;max-width:1450px">Three prescribers. One shelf. Nobody looks at the whole of it.</h1>
  <p class="sub-bn bn rise d2" lang="bn" style="font-size:46px">তিনজন চিকিৎসক, এক তাক ওষুধ — পুরোটা কেউ দেখে না।</p>
</div>
<div class="rise d3" style="display:grid;grid-template-columns:repeat(3,1fr);margin-top:auto;border-top:3px solid var(--ink)">
  <div style="padding:34px 40px 0 0">
    <p class="display tab" style="font-size:92px;line-height:1">78.28<span style="font-size:38px"> / 1,000</span></p>
    <p style="font-size:28px;margin-top:14px;line-height:1.35">Hypertension is now Bangladesh's most common illness.</p>
    <p style="font-size:19px;color:var(--ink-faint);margin-top:12px">BBS Health and Morbidity Status Survey 2025</p>
  </div>
  <div style="padding:34px 40px 0;border-left:1px solid var(--rule-strong)">
    <p class="display tab" style="font-size:92px;line-height:1">11%</p>
    <p style="font-size:28px;margin-top:14px;line-height:1.35">of people with hypertension had it controlled below 140/90.</p>
    <p style="font-size:19px;color:var(--ink-faint);margin-top:12px">WHO-HEARTS evaluation in Bangladesh, Heart (BMJ) 2024</p>
  </div>
  <div style="padding:34px 0 0 40px;border-left:1px solid var(--rule-strong)">
    <p class="display tab" style="font-size:92px;line-height:1">69%</p>
    <p style="font-size:28px;margin-top:14px;line-height:1.35">of 35 geriatric outpatients were prescribed five or more medicines.</p>
    <p style="font-size:19px;color:var(--ink-faint);margin-top:12px">Small 2011 private-hospital study, Bangladesh</p>
  </div>
</div>""", "Sources linked on the /docs page")

page(2, "solution", "The solution", """
<div style="display:grid;grid-template-columns:1fr 600px;gap:80px;align-items:center;margin:auto 0">
  <div>
    <p class="kicker rise">The solution · সমাধান</p>
    <h1 class="display rise d1" style="font-size:88px">A pharmacist for every elderly home.</h1>
    <p class="sub-bn bn rise d2" lang="bn" style="font-size:40px">প্রতিটি বয়স্ক মানুষের ঘরে একজন ফার্মাসিস্ট।</p>
    <ol class="rise d3" style="list-style:none;margin-top:40px;display:grid;gap:16px;font-size:27px;line-height:1.35">
      <li><b class="tab" style="color:var(--neel);margin-right:18px">1</b>A family member photographs every strip, box and prescription.</li>
      <li><b class="tab" style="color:var(--neel);margin-right:18px">2</b>One list, every brand mapped to its generic; rules find the risks.</li>
      <li><b class="tab" style="color:var(--neel);margin-right:18px">3</b>A pharmacist or doctor confirms every finding, then the family sees it, in Bangla.</li>
      <li><b class="tab" style="color:var(--neel);margin-right:18px">4</b>Sathi shows the next step; a passport goes to every doctor visit.</li>
    </ol>
  </div>
  <div class="rise d4" style="position:relative;height:560px;width:640px">
    <div class="strip" style="position:absolute;top:40px;left:0;width:500px;transform:rotate(-2deg)">
      <div class="foil"><i></i><i></i></div>
      <div class="body"><p class="brand">Napa<small>500 mg</small></p><span class="chip neel bn" lang="bn">প্যারাসিটামল</span></div>
    </div>
    <div class="strip" style="position:absolute;top:290px;left:24px;width:500px;transform:rotate(1.5deg)">
      <div class="foil"><i></i><i></i></div>
      <div class="body"><p class="brand">Ace<small>500 mg</small></p><span class="chip neel bn" lang="bn">প্যারাসিটামল</span></div>
    </div>
    <svg width="60" height="300" viewBox="0 0 60 300" style="position:absolute;left:548px;top:110px" aria-hidden="true">
      <path d="M6 4h30v292H6" fill="none" stroke="var(--red)" stroke-width="5" stroke-linejoin="round"/>
    </svg>
    <span class="chip red bn" lang="bn" style="position:absolute;left:390px;top:236px;white-space:nowrap;box-shadow:0 0 0 6px var(--paper)">দুটোই প্যারাসিটামল</span>
    <p style="position:absolute;left:24px;top:510px;font-size:24px;color:var(--ink-soft)">Different names, same medicine — taken twice.</p>
  </div>
</div>""", "Demo household — invented data")

page(3, "architecture", "Architecture", """
<div style="margin-top:50px">
  <p class="kicker rise">How it works · কীভাবে কাজ করে</p>
  <h1 class="display rise d1" style="font-size:88px">From a photo to a doctor-checked list.</h1>
</div>
<div class="rise d2" style="margin-top:80px;display:grid;grid-template-columns:repeat(6,1fr);gap:28px;align-items:stretch">
  <div class="card"><b>Photos</b><span>strips, boxes, prescriptions · in memory only, never stored</span></div>
  <div class="card" style="background:linear-gradient(160deg,var(--foil-hi),var(--foil))"><b>Vision model</b><span>NVIDIA Nemotron VL first, free fallbacks · typed data</span></div>
  <div class="card" style="background:linear-gradient(160deg,var(--foil-hi),var(--foil))"><b>Brand → generic</b><span>table first; unknown brands searched, must cite a source</span></div>
  <div class="card" style="background:var(--ink);color:var(--paper);border-color:var(--ink)"><b>Rules engine</b><span style="color:rgb(255 255 255 / .75)">duplicates, interactions, Beers 65+, expiry · no AI</span></div>
  <div class="card dye"><b>Clinician review</b><span>confirm or dismiss every flag · AI summary marked "check the evidence"</span></div>
  <div class="card"><b>Family</b><span>confirmed findings in Bangla · passport · Sathi helper</span></div>
</div>
<div class="rise d3" style="display:grid;grid-template-columns:repeat(6,1fr);gap:28px;margin-top:20px;font-size:20px;letter-spacing:.1em;text-transform:uppercase;font-weight:600;white-space:nowrap">
  <span style="grid-column:2/span 2;border-top:4px solid var(--foil-lo);padding-top:12px;color:var(--ink-faint)">AI · perception</span>
  <span style="border-top:4px solid var(--ink);padding-top:12px">Rules · judgement</span>
  <span style="border-top:4px solid var(--dye);padding-top:12px;color:var(--dye)">People · judgement</span>
</div>
<div class="rise d4" style="margin-top:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:28px;font-size:23px;color:var(--ink-soft);line-height:1.4">
  <p><b style="color:var(--ink)">Sathi guard</b><br>every question checked before and after any model</p>
  <p><b style="color:var(--ink)">Private by default</b><br>each family opens its list with its own link · rate-limited</p>
  <p><b style="color:var(--ink)">Built on</b><br>Next.js · FastAPI · Pydantic-AI · Postgres · FHIR R4 export</p>
</div>""")

if SATHI:
    eval_row = f"""
<div class="rise d4" style="margin-top:auto;border-top:3px solid var(--ink);padding-top:20px">
  <p style="font-size:24px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--neel)">Sathi safety test · 83 questions in Bangla, Banglish and English</p>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:36px;margin-top:18px">
    <div><p class="display tab" style="font-size:68px;line-height:1">{score('medical')}</p><p style="font-size:22px;margin-top:6px;line-height:1.3">medical questions sent to the pharmacist</p></div>
    <div><p class="display tab" style="font-size:68px;line-height:1">{score('emergency')}</p><p style="font-size:22px;margin-top:6px;line-height:1.3">emergencies given the 999 message</p></div>
    <div><p class="display tab" style="font-size:68px;line-height:1">{score('injection')}</p><p style="font-size:22px;margin-top:6px;line-height:1.3">attempts to break its rules refused</p></div>
    <div><p class="display tab" style="font-size:68px;line-height:1">{score('app')}</p><p style="font-size:22px;margin-top:6px;line-height:1.3">app questions answered from the right guide entry</p></div>
  </div>
  <p style="font-size:19px;color:var(--ink-faint);margin-top:14px">Guard and guide alone, as run on every code change (eval/run_sathi_eval.py). Questions written by the team; native-speaker review pending.</p>
</div>"""
else:
    eval_row = ""

page(4, "ai-approach", "AI approach", f"""
<div style="margin-top:10px">
  <p class="kicker rise">AI approach · কৃত্রিম বুদ্ধিমত্তার ভূমিকা</p>
  <h1 class="display rise d1" style="font-size:80px">AI for perception.<br>Rules and humans for judgement.</h1>
</div>
<div class="rise d3" style="display:grid;grid-template-columns:1fr 1fr;gap:64px;margin-top:34px;font-size:24px;line-height:1.35">
  <div style="border-top:4px solid var(--foil-lo);padding-top:20px">
    <p style="font-weight:600;font-size:28px">What models do</p>
    <ul style="list-style:none;display:grid;gap:4px;margin-top:10px;color:var(--ink-soft)">
      <li>Read cut strips, prescriptions and BP machines</li>
      <li>Look up unknown brands, citing the source</li>
      <li>Word Bangla explanations and Sathi's answers from the app guide</li>
      <li>Summarise facts for the reviewer, names checked</li>
    </ul>
  </div>
  <div style="border-top:4px solid var(--ink);padding-top:20px">
    <p style="font-weight:600;font-size:28px">What models never do</p>
    <ul style="list-style:none;display:grid;gap:4px;margin-top:10px;color:var(--ink-soft)">
      <li>Create, remove or change a safety flag</li>
      <li>Show the family anything a clinician has not confirmed</li>
      <li>Answer medical questions, or say stop or change a medicine</li>
      <li>See a patient's name</li>
    </ul>
  </div>
</div>{eval_row}""")

TILE = 'class="card" style="padding:28px 30px"'
page(5, "families", "Made for real families", f"""
<div style="margin-top:40px">
  <p class="kicker rise">Made for real families · সত্যিকারের পরিবারের জন্য</p>
  <h1 class="display rise d1" style="font-size:92px">For parents who can't read, and children far away.</h1>
  <p class="sub-bn bn rise d2" lang="bn" style="font-size:40px">যে বাবা-মা পড়তে পারেন না, আর যে সন্তান দূরে থাকেন — দুজনের জন্যই।</p>
</div>
<div class="rise d3" style="display:grid;grid-template-columns:repeat(3,1fr);gap:28px;margin-top:auto">
  <div {TILE}><b>Sathi, the helper</b><span>always the one next step; how-to answers only from the app guide; medical questions go to a pharmacist</span></div>
  <div {TILE}><b>Today's medicines</b><span>morning, noon, night as pictures, tablets drawn, read aloud in Bangla, a fridge sheet to print</span></div>
  <div {TILE}><b>Emergency QR</b><span>medicines, allergies and a contact, no login, first name only; the family can switch it off</span></div>
  <div {TILE}><b>Before the doctor visit</b><span>what changed and who changed it, four weeks of blood pressure, the family's questions, on one page</span></div>
  <div {TILE}><b>Set aside</b><span>expired strips and medicines the pharmacist stopped, so nobody takes them by mistake</span></div>
  <div {TILE}><b>Blood pressure from a photo</b><span>the machine's numbers read for the family, who check them before saving</span></div>
</div>""", "Demo household — invented data")

page(6, "impact", "Impact and next", """
<div style="margin-top:70px">
  <p class="kicker rise">Impact and next · প্রভাব ও পরবর্তী ধাপ</p>
  <h1 class="display rise d1" style="font-size:108px">Families abroad pay.<br>Parents stay safe.</h1>
  <p class="sub-bn bn rise d2" lang="bn" style="font-size:44px">প্রবাসী সন্তান খরচ দেন; বাবা-মা নিরাপদ থাকেন।</p>
</div>
<div class="rise d3" style="display:grid;grid-template-columns:1.1fr 1fr 1fr 1fr;gap:36px;margin-top:auto;border-top:3px solid var(--ink);padding-top:32px;font-size:28px;line-height:1.35">
  <div style="border:2px dashed var(--stitch);border-radius:12px;padding:24px 28px;margin-top:-6px">
    <p style="font-weight:600">Pilot</p>
    <p style="color:var(--ink-soft);margin-top:8px;font-size:23px">Results are published only once they are real, with 95% confidence intervals. Every review is already timed.</p>
  </div>
  <div><p style="font-weight:600">Partner pharmacies</p><p style="color:var(--ink-soft);margin-top:8px;font-size:23px">as scan points, and a paid review service for model pharmacies</p></div>
  <div><p style="font-weight:600">Shared Health Record</p><p style="color:var(--ink-soft);margin-top:8px;font-size:23px">FHIR R4 export is ready for Bangladesh's health ID plans</p></div>
  <div><p style="font-weight:600">Licensed drug database</p><p style="color:var(--ink-soft);margin-top:8px;font-size:23px">pharmacist-verified brands and interactions</p></div>
</div>""")

page(7, "close", "Close", """
<div style="display:grid;grid-template-columns:1fr 660px;gap:100px;align-items:center;margin:auto 0">
  <div>
    <h1 class="display rise" style="font-size:136px;margin-top:0">Build locally,<br>protect globally.</h1>
    <p class="sub-bn bn-display rise d1" lang="bn" style="font-size:46px;margin-top:34px;white-space:nowrap">প্রতিবার ডাক্তার দেখানোর সময় এটি দেখান।</p>
    <p class="rise d2" style="font-size:30px;color:var(--ink-soft);margin-top:14px">Show this at every doctor visit.</p>
  </div>
  <div class="rise d3" style="background:var(--paper-raised);border:1px solid var(--rule-strong);border-radius:12px;box-shadow:var(--shadow);padding:40px 46px;transform:rotate(1.5deg)">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:24px">
      <div><p class="bn-display" lang="bn" style="font-size:44px">ওষুধের পাসপোর্ট</p>
      <p style="font-size:22px;color:var(--ink-faint);margin-top:2px">Medicine passport · Rahima Begum, 68</p></div>
      <div style="width:84px;height:84px;border:2px solid var(--ink);border-radius:6px;display:grid;place-items:center;font-size:15px;font-weight:600;text-align:center;line-height:1.1">QR<br>emergency</div>
    </div>
    <div style="border-top:2px solid var(--ink);margin-top:22px;padding-top:18px;display:grid;gap:14px">
      <p class="bn" lang="bn" style="font-size:22px;color:var(--neel);font-weight:600;letter-spacing:.04em">সকাল · Morning</p>
      <p style="font-size:30px;font-weight:600">Amlodipine 5 mg <span style="font-size:21px;font-weight:400;color:var(--ink-faint)">Camlodin</span>
        <span class="bn" lang="bn" style="display:block;font-size:20px;font-weight:400;color:var(--ink-soft)">কিসের জন্য: রক্তচাপ · Blood pressure</span></p>
      <p style="font-size:30px;font-weight:600">Metformin 500 mg <span style="font-size:21px;font-weight:400;color:var(--ink-faint)">Comet</span>
        <span class="bn" lang="bn" style="display:block;font-size:20px;font-weight:400;color:var(--ink-soft)">কিসের জন্য: ডায়াবেটিস · Diabetes</span></p>
      <p style="font-size:22px;border-top:1px solid var(--rule);padding-top:12px"><b>Allergy:</b> Penicillin <span style="color:var(--ink-faint);font-size:18px">· confirmed by the pharmacist</span></p>
    </div>
    <p style="margin-top:20px;font-size:18px;color:var(--ink-faint);border:1px dashed var(--rule-strong);border-radius:999px;display:inline-block;padding:6px 16px">Demo household — invented data</p>
  </div>
</div>""", "Research prototype, not a medical device. Every finding is confirmed by a registered pharmacist or doctor.")
print(f"wrote {TOTAL} scenes" + (" (with the Sathi eval)" if SATHI else " (no Sathi eval results found)"))
