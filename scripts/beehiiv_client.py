"""Thin beehiiv REST API v2 client.

Reads (list/get posts, segments, subscribers) work on any PAID plan.
create_post / update_post require the ENTERPRISE plan (Send API beta) and
will return 403 on other plans — that is expected, not a bug in this code.
"""
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

BASE = "https://api.beehiiv.com/v2"
KEY = os.environ.get("BEEHIIV_API_KEY", "")
PUB = os.environ.get("BEEHIIV_PUBLICATION_ID", "")
TEMPLATE = os.environ.get("BEEHIIV_POST_TEMPLATE_ID", "")
HEADERS = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}


def _req(method, path, **kw):
    if not KEY or not PUB:
        raise SystemExit(
            "BEEHIIV_API_KEY / BEEHIIV_PUBLICATION_ID not set. Copy .env.example to "
            ".env and fill them in."
        )
    r = requests.request(method, f"{BASE}{path}", headers=HEADERS, timeout=30, **kw)
    if r.status_code == 429:  # rate limited: 180/min per org
        reset = int(r.headers.get("RateLimit-Reset", time.time() + 5))
        time.sleep(max(1, reset - int(time.time())))
        return _req(method, path, **kw)
    if r.status_code == 403:
        raise SystemExit(
            "403 Forbidden from beehiiv. create/update post is Enterprise-only "
            "(Send API beta). Use scripts/render.py + paste-publish instead, or "
            "upgrade to Enterprise and request Send API access."
        )
    r.raise_for_status()
    return r.json()


# ── Reads (any paid plan) ────────────────────────────────────────────────
def list_posts(limit=10, status="all"):
    return _req("GET", f"/publications/{PUB}/posts", params={
        "limit": limit, "status": status,
        "order_by": "publish_date", "direction": "desc",
    })


def get_post(post_id, expand=("free_web_content",)):
    return _req("GET", f"/publications/{PUB}/posts/{post_id}",
                params={"expand[]": list(expand)})


def list_segments():
    return _req("GET", f"/publications/{PUB}/segments")


def create_subscriber(email, **fields):
    return _req("POST", f"/publications/{PUB}/subscriptions",
                json={"email": email, **fields})


# ── ENTERPRISE-ONLY below this line ──────────────────────────────────────
def create_post(*, title, html=None, blocks=None, subject, preview,
                scheduled_at=None, override_scheduled_at=None,
                tiers=("free",), web_only=False,
                template_id=None, slug=None, tags=None):
    """Create a post. Enterprise-only. Returns {'data': {'id': 'post_...'}}.

    - scheduled_at: ISO-8601 UTC future timestamp; if None -> publish now.
    - override_scheduled_at: visible/displayed date (may be in the past).
    - web_only=True: omit email recipients -> web-only article (no email sent).
    """
    if (html is None) == (blocks is None):
        raise ValueError("Pass exactly one of html or blocks")

    body = {
        "title": title,
        "status": "confirmed",
        "email_settings": {
            "email_subject_line": subject,
            "email_preview_text": preview,
            "display_title_in_email": True,
            "display_subtitle_in_email": True,
        },
        "web_settings": {"slug": slug} if slug else {},
        "content_tags": list(tags or []),
    }
    if html is not None:
        body["body_content"] = html
    else:
        body["blocks"] = blocks
    if scheduled_at:
        body["scheduled_at"] = scheduled_at
    if override_scheduled_at:
        body["override_scheduled_at"] = override_scheduled_at
    if template_id or TEMPLATE:
        body["post_template_id"] = template_id or TEMPLATE
    body["recipients"] = (
        {"web": {"tier_ids": list(tiers)}} if web_only
        else {"web": {"tier_ids": list(tiers)}, "email": {"tier_ids": list(tiers)}}
    )
    return _req("POST", f"/publications/{PUB}/posts", json=body)
