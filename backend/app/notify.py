"""Family email: "results are ready" and the weekly report. Fixed templates, no AI.

Only for households that gave an email AND opted in at /start or in settings. What an email may
carry: counts, and the brand and generic names of CONFIRMED findings (the family's own medicines).
What it never carries: the reviewer's note, the Bangla explanation, evidence, or the family key.
The link opens the app; the family's own device holds the key.

Sending is Resend over HTTPS (RESEND_API_KEY, NOTIFY_FROM). Without a key nothing is sent and
nothing fails: WhatsApp sharing in the app is the main channel.
"""
from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass

import httpx

log = logging.getLogger("oushodh.notify")

RESEND_URL = "https://api.resend.com/emails"
CODE_BN = {
    "DUPLICATE_GENERIC": "একই ওষুধ দুইবার",
    "THERAPEUTIC_DUPLICATION": "একই ধরনের দুটি ওষুধ",
    "INTERACTION": "দুটি ওষুধ একসাথে ঝুঁকিপূর্ণ",
    "BEERS_65": "৬৫ বছরের পরে সাবধানে খাওয়ার ওষুধ",
    "EXPIRED": "মেয়াদ শেষ",
    "ANTICHOLINERGIC_BURDEN": "মাথা ঘোরা ও পড়ে যাওয়ার ঝুঁকি",
    "LOOK_ALIKE_NAMES": "নাম প্রায় একই, ওষুধ আলাদা",
}
CODE_EN = {
    "DUPLICATE_GENERIC": "Same medicine twice",
    "THERAPEUTIC_DUPLICATION": "Two medicines of the same kind",
    "INTERACTION": "Two medicines that can interact",
    "BEERS_65": "Needs care after age 65",
    "EXPIRED": "Expired strip",
    "ANTICHOLINERGIC_BURDEN": "Risk of confusion and falls",
    "LOOK_ALIKE_NAMES": "Similar names, different medicines",
}
FOOTER = (
    "\n\n—\nওষুধসাথী কখনো কোনো ওষুধ বন্ধ বা পরিবর্তন করতে বলে না। ডাক্তারের সাথে কথা না বলে কোনো ওষুধ বন্ধ করবেন না।\n"
    "OushodhSathi never tells anyone to stop or change a medicine. Talk to the doctor before changing anything.\n"
    "To stop these emails, turn them off in Settings in the app."
)


@dataclass
class Email:
    to: str
    subject: str
    text: str


def configured() -> bool:
    return bool(os.getenv("RESEND_API_KEY", "").strip())


def app_url() -> str:
    return (os.getenv("PUBLIC_APP_URL") or "https://oushodhsathi.vercel.app").rstrip("/")


def results_ready(pid: int, findings: list[dict]) -> tuple[str, str]:
    """findings: [{"code", "brands": [...], "generics": [...]}] for CONFIRMED flags only."""
    link = f"{app_url()}/p/{pid}/results"
    if findings:
        lines_bn = [f"• {CODE_BN.get(f['code'], f['code'])}: {', '.join(f['brands'])}" for f in findings]
        lines_en = [f"• {CODE_EN.get(f['code'], f['code'])}: {', '.join(f['brands'])}" for f in findings]
        head_bn = f"ফার্মাসিস্ট বা ডাক্তার তালিকাটি দেখেছেন এবং {len(findings)}টি বিষয় নিশ্চিত করেছেন।"
        head_en = f"A pharmacist or doctor checked the list and confirmed {len(findings)} finding(s)."
    else:
        lines_bn, lines_en = [], []
        head_bn = "ফার্মাসিস্ট বা ডাক্তার তালিকাটি দেখেছেন। নিশ্চিত করার মতো কোনো সমস্যা পাওয়া যায়নি।"
        head_en = "A pharmacist or doctor checked the list. No problem needed confirming."
    text = "\n".join([
        head_bn, *lines_bn, "", f"সহজ বাংলায় ব্যাখ্যা অ্যাপে দেখুন: {link}", "", head_en, *lines_en, "",
        f"Read the plain-language explanation in the app: {link}",
    ]) + FOOTER
    return "ওষুধের তালিকা দেখা হয়েছে · Your medicine check is ready", text


def weekly(pid: int, report: dict) -> tuple[str, str]:
    """report: the dict from build_weekly_report (counts and refill names only are used)."""
    link = f"{app_url()}/p/{pid}/report"
    f = report.get("flags") or {}
    refills = report.get("refills_due") or []
    bp = (report.get("bp") or {}).get("readings") or []
    refill_bn = [f"• {r['brand']}: আর {r['days_left']} দিনের ওষুধ আছে" for r in refills]
    refill_en = [f"• {r['brand']}: about {r['days_left']} day(s) left" for r in refills]
    text = "\n".join([
        "এই সপ্তাহের সারসংক্ষেপ",
        f"• নিশ্চিত সতর্কতা খোলা: {f.get('confirmed_open', 0)}",
        f"• রক্তচাপ লেখা হয়েছে: {len(bp)} বার",
        *(["• শীঘ্রই কিনতে হবে:"] + refill_bn if refills else []),
        f"পুরো রিপোর্ট: {link}", "",
        "This week",
        f"• Confirmed findings still open: {f.get('confirmed_open', 0)}",
        f"• Blood pressure readings: {len(bp)}",
        *(["• Running out soon:"] + refill_en if refills else []),
        f"Full report: {link}",
    ]) + FOOTER
    return "সাপ্তাহিক রিপোর্ট · Weekly report", text


def send(email: Email) -> None:
    """Fire and forget on a daemon thread, outside any database lock. Never logs addresses or text."""
    key = os.getenv("RESEND_API_KEY", "").strip()
    if not key:
        return
    sender = os.getenv("NOTIFY_FROM") or "OushodhSathi <onboarding@resend.dev>"

    def go() -> None:
        try:
            r = httpx.post(RESEND_URL, timeout=10, headers={"Authorization": f"Bearer {key}"},
                           json={"from": sender, "to": [email.to], "subject": email.subject, "text": email.text})
            if r.status_code >= 300:
                log.warning("email not accepted: HTTP %s", r.status_code)
        except httpx.HTTPError as e:
            log.warning("email failed: %s", type(e).__name__)

    threading.Thread(target=go, daemon=True).start()
