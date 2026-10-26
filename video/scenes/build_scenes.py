"""Writes the six 1920x1080 video scenes. Run: python video/scenes/build_scenes.py"""
from pathlib import Path

HERE = Path(__file__).parent
MARK = (HERE / "_mark.svg.txt").read_text().strip()


def page(n: int, slug: str, title: str, body: str, foot_left: str = "") -> None:
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=1920">
<title>{title} · OushodhSathi</title><link rel="stylesheet" href="scenes.css"></head>
<body><main class="scene">
<header class="topbar"><div class="mark">{MARK}<span class="bn-display" lang="bn">ওষুধসাথী</span><span class="serif">OushodhSathi</span></div>
<span class="step tab">{n:02d} / 06 · {title}</span></header>
{body}
<footer class="foot"><span>{foot_left}</span><span>International AI Builders Congress 2026 · HealthSphere AI</span></footer>
</main></body></html>
"""
    (HERE / f"{n:02d}-{slug}.html").write_text(html, encoding="utf-8")


page(1, "problem", "The problem", """
<div style="margin-top:96px">
  <p class="kicker rise">The problem · সমস্যা</p>
  <h1 class="serif rise d1" style="font-size:112px;max-width:1400px">Three prescribers. One shelf. Nobody looks at the whole of it.</h1>
  <p class="sub-bn bn rise d2" lang="bn" style="font-size:46px">তিনজন চিকিৎসক, এক তাক ওষুধ — পুরোটা কেউ দেখে না।</p>
</div>
<div class="rise d3" style="display:grid;grid-template-columns:repeat(3,1fr);gap:0;margin-top:auto;border-top:2px solid var(--ink)">
  <div style="padding:34px 40px 0 0">
    <p class="serif tab" style="font-size:96px;line-height:1">78.28<span style="font-size:40px"> / 1,000</span></p>
    <p style="font-size:28px;margin-top:14px;line-height:1.35">Hypertension is now Bangladesh's most common illness.</p>
    <p style="font-size:19px;color:var(--ink-faint);margin-top:12px">BBS Health and Morbidity Status Survey 2025</p>
  </div>
  <div style="padding:34px 40px 0;border-left:1px solid var(--rule-strong)">
    <p class="serif tab" style="font-size:96px;line-height:1">11%</p>
    <p style="font-size:28px;margin-top:14px;line-height:1.35">of people with hypertension had it controlled below 140/90.</p>
    <p style="font-size:19px;color:var(--ink-faint);margin-top:12px">WHO-HEARTS evaluation in Bangladesh, Heart (BMJ) 2024</p>
  </div>
  <div style="padding:34px 0 0 40px;border-left:1px solid var(--rule-strong)">
    <p class="serif tab" style="font-size:96px;line-height:1">69%</p>
    <p style="font-size:28px;margin-top:14px;line-height:1.35">of 35 geriatric outpatients were prescribed five or more medicines.</p>
    <p style="font-size:19px;color:var(--ink-faint);margin-top:12px">Small 2011 private-hospital study, Bangladesh</p>
  </div>
</div>""", "Sources linked on the /docs page")

page(2, "solution", "The solution", """
<div style="display:grid;grid-template-columns:1fr 640px;gap:100px;align-items:center;margin-top:auto;margin-bottom:auto">
  <div>
    <p class="kicker rise">The solution · সমাধান</p>
    <h1 class="serif rise d1" style="font-size:120px">A pharmacist for every elderly home.</h1>
    <p class="sub-bn bn rise d2" lang="bn" style="font-size:48px">প্রতিটি বয়স্ক মানুষের ঘরে একজন ফার্মাসিস্ট।</p>
    <ol class="rise d3 steps" style="list-style:none;margin-top:56px;display:grid;gap:22px;font-size:32px;line-height:1.35">
      <li><span class="tab" style="color:var(--teal);font-weight:600">1</span>A family member photographs every strip, box and prescription.</li>
      <li><span class="tab" style="color:var(--teal);font-weight:600">2</span>We turn the pile into one list, every brand mapped to its generic.</li>
      <li><span class="tab" style="color:var(--teal);font-weight:600">3</span>A pharmacist or doctor confirms every finding, in Bangla.</li>
    </ol>
  </div>
  <div class="rise d4" style="position:relative;height:560px;width:640px">
    <div class="strip" style="position:absolute;top:40px;left:0;width:500px;transform:rotate(-2deg)">
      <div class="foil"><i></i><i></i></div>
      <div class="body"><p class="brand">Napa<small>500 mg</small></p><span class="chip teal bn" lang="bn">প্যারাসিটামল</span></div>
    </div>
    <div class="strip" style="position:absolute;top:290px;left:24px;width:500px;transform:rotate(1.5deg)">
      <div class="foil"><i></i><i></i></div>
      <div class="body"><p class="brand">Ace<small>500 mg</small></p><span class="chip teal bn" lang="bn">প্যারাসিটামল</span></div>
    </div>
    <svg width="60" height="300" viewBox="0 0 60 300" style="position:absolute;left:548px;top:110px" aria-hidden="true">
      <path d="M6 4h30v292H6" fill="none" stroke="var(--red)" stroke-width="5" stroke-linejoin="round"/>
    </svg>
    <span class="chip red bn" lang="bn" style="position:absolute;left:400px;top:236px;white-space:nowrap;background:var(--red-tint);box-shadow:0 0 0 6px var(--paper)">দুটোই প্যারাসিটামল</span>
    <p style="position:absolute;left:24px;top:510px;font-size:24px;color:var(--ink-soft)">Different names, same medicine — taken twice.</p>
  </div>
</div>""", "Demo household — invented data")

ARCH_BOX = 'style="border:1.5px solid var(--rule-strong);background:var(--paper-raised);border-radius:10px;padding:22px 26px;font-size:26px;line-height:1.3"'
page(3, "architecture", "Architecture", f"""
<div style="margin-top:70px">
  <p class="kicker rise">How it works · কীভাবে কাজ করে</p>
  <h1 class="serif rise d1" style="font-size:96px">From a photo to a doctor-checked list.</h1>
</div>
<div class="rise d2 flow" style="margin-top:110px;display:grid;grid-template-columns:repeat(6,1fr);gap:40px;align-items:stretch">
  <div {ARCH_BOX}><b>Photos</b><br><span style="color:var(--ink-soft);font-size:22px">strips, boxes, prescriptions · kept in memory only</span></div>
  <div {ARCH_BOX.replace('var(--paper-raised)','linear-gradient(160deg,var(--foil-hi),var(--foil))')}><b>Vision model</b><br><span style="color:var(--ink-soft);font-size:22px">reads them into typed data</span></div>
  <div {ARCH_BOX.replace('var(--paper-raised)','linear-gradient(160deg,var(--foil-hi),var(--foil))')}><b>Brand → generic</b><br><span style="color:var(--ink-soft);font-size:22px">table first; unknown brands searched, must cite a source</span></div>
  <div style="border:1.5px solid var(--ink);background:var(--ink);color:var(--paper);border-radius:10px;padding:22px 26px;font-size:26px;line-height:1.3"><b>Rules engine</b><br><span style="opacity:.8;font-size:22px">duplicates, interactions, Beers 65+, expiry · no AI</span></div>
  <div style="border:1.5px solid var(--teal);background:var(--teal);color:#fff;border-radius:10px;padding:22px 26px;font-size:26px;line-height:1.3"><b>Clinician review</b><br><span style="opacity:.85;font-size:22px">confirm or dismiss every flag, with a note</span></div>
  <div {ARCH_BOX}><b>Family + passport</b><br><span style="color:var(--ink-soft);font-size:22px">confirmed flags only, in plain Bangla</span></div>
</div>
<div class="rise d3" style="display:grid;grid-template-columns:repeat(6,1fr);gap:40px;margin-top:22px;font-size:20px;letter-spacing:.1em;text-transform:uppercase;font-weight:600;white-space:nowrap">
  <span style="grid-column:2/span 2;border-top:4px solid var(--foil-lo);padding-top:12px;color:var(--ink-faint)">AI · perception</span>
  <span style="border-top:4px solid var(--ink);padding-top:12px">Rules · judgement</span>
  <span style="border-top:4px solid var(--teal);padding-top:12px;color:var(--teal)">People · judgement</span>
</div>
<p class="rise d4" style="margin-top:auto;font-size:24px;color:var(--ink-soft)">Next.js · FastAPI · Pydantic-AI · SQLite · n8n automations · read-only MCP server</p>""")

page(4, "ai-approach", "AI approach", """
<div style="margin-top:70px">
  <p class="kicker rise">AI approach · কৃত্রিম বুদ্ধিমত্তার ভূমিকা</p>
  <h1 class="serif rise d1" style="font-size:112px">AI for perception.<br>Rules and humans for judgement.</h1>
  <p class="sub-bn bn rise d2" lang="bn" style="font-size:44px">এআই ছবি পড়ে; সিদ্ধান্ত নেয় নিয়ম আর মানুষ।</p>
</div>
<div class="rise d3" style="display:grid;grid-template-columns:1fr 1fr;gap:64px;margin-top:auto;font-size:28px;line-height:1.4">
  <div style="border-top:4px solid var(--foil-lo);padding-top:26px">
    <p style="font-weight:600;font-size:30px">What models do</p>
    <ul style="list-style:none;display:grid;gap:14px;margin-top:16px;color:var(--ink-soft)">
      <li>Read cut strips and Bangla prescriptions into typed fields</li>
      <li>Look up unknown brands on Bangladeshi medicine sites, with a cited source</li>
      <li>Write the plain-Bangla explanation of a confirmed finding</li>
    </ul>
  </div>
  <div style="border-top:4px solid var(--ink);padding-top:26px">
    <p style="font-weight:600;font-size:30px">What models never do</p>
    <ul style="list-style:none;display:grid;gap:14px;margin-top:16px;color:var(--ink-soft)">
      <li>Create, remove or change the severity of a safety flag</li>
      <li>Show the family anything a clinician has not confirmed</li>
      <li>Tell a patient to stop, start or change a medicine</li>
    </ul>
  </div>
</div>
<p class="rise d4" style="margin-top:40px;font-size:22px;color:var(--ink-faint)">Free OpenRouter models with fallback routers · a private local model (Ollama, qwen2.5:3b) for Bangla · patient names never sent to a model</p>""")

page(5, "impact", "Impact and next", """
<div style="margin-top:96px">
  <p class="kicker rise">Impact and next · প্রভাব ও পরবর্তী ধাপ</p>
  <h1 class="serif rise d1" style="font-size:112px">Families abroad pay.<br>Parents stay safe.</h1>
  <p class="sub-bn bn rise d2" lang="bn" style="font-size:44px">প্রবাসী সন্তান খরচ দেন; বাবা-মা নিরাপদ থাকেন।</p>
</div>
<div class="rise d3" style="display:grid;grid-template-columns:1.1fr 1fr 1fr 1fr;gap:40px;margin-top:auto;border-top:2px solid var(--ink);padding-top:34px;font-size:28px;line-height:1.35">
  <div style="border:1.5px dashed var(--rule-strong);border-radius:10px;padding:24px 28px;margin-top:-6px">
    <p style="font-weight:600">Pilot</p>
    <p style="color:var(--ink-soft);margin-top:8px;font-size:24px">Results are published only once they are real, with 95% confidence intervals.</p>
  </div>
  <div><p style="font-weight:600">Partner pharmacies</p><p style="color:var(--ink-soft);margin-top:8px;font-size:24px">as scan points for homes without a smartphone</p></div>
  <div><p style="font-weight:600">Bangla voice check-ins</p><p style="color:var(--ink-soft);margin-top:8px;font-size:24px">for blood pressure and doses</p></div>
  <div><p style="font-weight:600">Licensed drug database</p><p style="color:var(--ink-soft);margin-top:8px;font-size:24px">pharmacist-verified brands and interactions</p></div>
</div>""")

page(6, "close", "Close", """
<div style="display:grid;grid-template-columns:1fr 620px;gap:110px;align-items:center;margin:auto 0">
  <div>
    <h1 class="serif rise" style="font-size:150px;margin-top:0">Build locally,<br>protect globally.</h1>
    <p class="sub-bn bn-display rise d1" lang="bn" style="font-size:46px;margin-top:34px;white-space:nowrap">প্রতিটি ডাক্তার দেখানোর সময় এটি সঙ্গে রাখুন।</p>
    <p class="rise d2" style="font-size:30px;color:var(--ink-soft);margin-top:14px">Show this at every doctor visit.</p>
  </div>
  <div class="rise d3" style="background:var(--paper-raised);border:1px solid var(--rule-strong);border-radius:12px;box-shadow:var(--shadow);padding:44px 48px;transform:rotate(1.5deg)">
    <p class="bn-display" lang="bn" style="font-size:44px">ওষুধের পাসপোর্ট</p>
    <p style="font-size:22px;color:var(--ink-faint);margin-top:2px">Medicine passport · Rahima Begum, 68</p>
    <div style="border-top:1px solid var(--rule);margin-top:24px;padding-top:20px;display:grid;gap:18px">
      <p class="bn" lang="bn" style="font-size:22px;color:var(--teal);font-weight:600;letter-spacing:.04em">সকাল · Morning</p>
      <p style="font-size:32px;font-weight:600">Amlodipine 5 mg <span style="font-size:22px;font-weight:400;color:var(--ink-faint)">Camlodin</span></p>
      <p style="font-size:32px;font-weight:600">Losartan 50 mg <span style="font-size:22px;font-weight:400;color:var(--ink-faint)">Angilock</span></p>
      <p class="bn" lang="bn" style="font-size:22px;color:var(--teal);font-weight:600;letter-spacing:.04em;margin-top:6px">রাত · Night</p>
      <p style="font-size:32px;font-weight:600">Metformin 500 mg <span style="font-size:22px;font-weight:400;color:var(--ink-faint)">Comet</span></p>
    </div>
    <p style="margin-top:26px;font-size:18px;color:var(--ink-faint);border:1px dashed var(--rule-strong);border-radius:999px;display:inline-block;padding:6px 16px">Demo household — invented data</p>
  </div>
</div>""", "Research prototype, not a medical device. Every finding is confirmed by a registered pharmacist or doctor.")
print("wrote 6 scenes")
