"""Submit the daily check-in template to Meta for approval (run once; Meta reviews it before use).

  python backend/scripts/create_whatsapp_template.py            # submit
  python backend/scripts/create_whatsapp_template.py --dry-run  # print the request only

Creates a "utility" template in Bengali ("bn") with the body and three quick-reply buttons from
app/whatsapp_checkin/flow.py, via POST https://graph.facebook.com/<API_VERSION>/<WABA_ID>/message_templates
(https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/utility-templates/utility-templates.md;
quick-reply buttons: .../templates/components.md, up to 25 characters each; languages:
.../templates/supported-languages.md). Needs WHATSAPP_TOKEN and WHATSAPP_BUSINESS_ACCOUNT_ID.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.whatsapp_checkin import flow  # noqa: E402


def request_body() -> dict:
    return {
        "name": flow.TEMPLATE_NAME,
        "language": flow.TEMPLATE_LANGUAGE,
        "category": "utility",
        "components": [
            {"type": "body", "text": flow.DAILY},
            {"type": "buttons", "buttons": [{"type": "quick_reply", "text": label} for label in flow.TEMPLATE_BUTTONS]},
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    body = request_body()
    if a.dry_run:
        print(json.dumps(body, ensure_ascii=False, indent=2))
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / "backend" / ".env")
    except ImportError:
        pass
    token, waba = os.getenv("WHATSAPP_TOKEN", "").strip(), os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "").strip()
    if not token or not waba:
        sys.exit("Set WHATSAPP_TOKEN and WHATSAPP_BUSINESS_ACCOUNT_ID in backend/.env first.")
    import httpx

    version = os.getenv("WHATSAPP_API_VERSION", "").strip() or "v27.0"
    r = httpx.post(f"https://graph.facebook.com/{version}/{waba}/message_templates", json=body,
                   headers={"Authorization": f"Bearer {token}"}, timeout=30)
    print(r.status_code, r.text)


if __name__ == "__main__":
    main()
