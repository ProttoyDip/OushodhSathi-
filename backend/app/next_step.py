"""The one thing a family should do next. A deterministic state machine: pure functions.

States are checked in priority order; the first match wins. Each state carries a fixed
Bangla and English line (the AI may only reword it, see sathi.phrase_next_step), a
button label and the screen the button opens.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")


def bn_num(n: int | float) -> str:
    return str(n).translate(BN_DIGITS)


@dataclass(frozen=True)
class StepContext:
    emergency_recent: bool = False      # an emergency message in the last 24 hours
    unread_replies: int = 0             # pharmacist replies the family has not opened
    unseen_results: int = 0             # confirmed findings reviewed after the family last looked
    results_ready: bool = False         # a finished review the family has not opened (may be 0 findings)
    unconfirmed: int = 0                # scanned items not yet confirmed by the family
    unconfirmed_need_check: int = 0     # of those, low confidence / not found / web match
    any_items: bool = False
    ready_to_send: bool = False         # confirmed items not yet sent for review
    in_review: bool = False
    reviewed: bool = False              # at least one finished review
    passport_seen: bool = False
    refills: list[tuple[str, int]] = field(default_factory=list)  # (brand, days left), soonest first


@dataclass(frozen=True)
class NextStep:
    code: str
    params: dict
    text_bn: str
    text_en: str
    button_bn: str
    button_en: str
    route: str  # an app path, or tel:999

    def to_dict(self) -> dict:
        return asdict(self)


def next_step(ctx: StepContext, pid: int) -> NextStep:
    home = f"/p/{pid}"

    if ctx.emergency_recent:
        return NextStep("EMERGENCY_ACTIVE", {},
                        "এখনো একই রকম হলে এখনই কাছের হাসপাতালে যান বা ৯৯৯-এ কল করুন।",
                        "If this is still happening, go to the nearest hospital now or call 999.",
                        "৯৯৯-এ কল করুন", "Call 999", "tel:999")
    if ctx.unread_replies:
        n = ctx.unread_replies
        return NextStep("PHARMACIST_REPLIED", {"n": n},
                        f"ফার্মাসিস্ট আপনার {bn_num(n)}টি প্রশ্নের উত্তর দিয়েছেন।",
                        f"The pharmacist answered {n} of your questions.",
                        "উত্তর দেখুন", "See the answer", f"{home}/questions")
    if ctx.results_ready:
        n = ctx.unseen_results
        if n:
            bn, en = (f"যাচাই করা {bn_num(n)}টি ফলাফল তৈরি। দেখে নিন।", f"{n} checked results are ready to read.")
        else:
            bn, en = ("যাচাই শেষ হয়েছে। ফলাফল দেখে নিন।", "The check is finished. Have a look at the result.")
        return NextStep("RESULTS_READY", {"n": n}, bn, en, "ফলাফল দেখুন", "See results", f"{home}/results")
    if ctx.unconfirmed_need_check:
        n = ctx.unconfirmed_need_check
        return NextStep("LOW_CONFIDENCE", {"n": n},
                        f"{bn_num(n)}টি ওষুধ ঠিকমতো পড়া যায়নি। একবার মিলিয়ে নিন।",
                        f"{n} medicines could not be read clearly. Please check them.",
                        "মিলিয়ে নিন", "Check them", f"{home}/confirm")
    if ctx.unconfirmed:
        n = ctx.unconfirmed
        return NextStep("ITEMS_TO_CONFIRM", {"n": n},
                        f"{bn_num(n)}টি ওষুধ আপনার যাচাইয়ের অপেক্ষায়।",
                        f"{n} medicines are waiting for you to check.",
                        "মিলিয়ে নিন", "Check them", f"{home}/confirm")
    if not ctx.any_items:
        return NextStep("NO_SCAN", {},
                        "শুরু করতে বাড়ির ওষুধের পাতা আর বাক্সের ছবি তুলুন।",
                        "Start by taking photos of the medicine strips and boxes at home.",
                        "ওষুধ স্ক্যান করুন", "Scan medicines", f"{home}/scan")
    if ctx.ready_to_send:
        return NextStep("READY_TO_SEND", {},
                        "তালিকা তৈরি। ফার্মাসিস্টের কাছে যাচাইয়ের জন্য পাঠান।",
                        "The list is ready. Send it to the pharmacist to check.",
                        "যাচাইয়ের জন্য পাঠান", "Send for checking", f"{home}/confirm")
    if ctx.in_review:
        return NextStep("SENT_FOR_REVIEW", {},
                        "একজন ফার্মাসিস্ট বা ডাক্তার তালিকাটি দেখছেন। সাধারণত এক দিনের মধ্যে হয়ে যায়।",
                        "A pharmacist or doctor is checking the list. It usually takes about a day.",
                        "অবস্থা দেখুন", "See progress", f"{home}/status")
    if ctx.reviewed and not ctx.passport_seen:
        return NextStep("PASSPORT_NOT_SAVED", {},
                        "ওষুধের পাসপোর্টটি প্রিন্ট বা সেভ করে রাখুন, ডাক্তারকে দেখানোর জন্য।",
                        "Print or save the medicine passport to show at the doctor.",
                        "পাসপোর্ট খুলুন", "Open passport", f"/passport/{pid}")
    if ctx.refills:
        med, days = ctx.refills[0]
        if days <= 0:
            bn, en = (f"{med} শেষ হয়ে এসেছে। নতুন আনার আগে প্রেসক্রিপশন দেখে নিন।",
                      f"{med} has run out or is about to. Check the prescription before buying more.")
        else:
            bn, en = (f"{med} আর প্রায় {bn_num(days)} দিন চলবে। নতুন আনার আগে প্রেসক্রিপশন দেখে নিন।",
                      f"{med} will last about {days} more days. Check the prescription before buying more.")
        return NextStep("REFILL_DUE", {"med": med, "days": days}, bn, en,
                        "রিপোর্ট দেখুন", "See the report", f"{home}/report")
    return NextStep("ALL_GOOD", {},
                    "এই মুহূর্তে আপনার কিছু করার নেই।",
                    "Nothing for you to do right now.",
                    "আজকের ওষুধ দেখুন", "See today's medicines", f"{home}/today")
