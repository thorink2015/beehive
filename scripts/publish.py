"""Publish a draft to beehiiv via the API. ENTERPRISE PLAN ONLY.

On non-Enterprise plans this will stop with a clear 403 message — that is
expected. Use scripts/render.py + paste-publish instead.

Usage:
    python scripts/publish.py drafts/2026-05-01-issue-01.md
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _draft import parse
from md_to_beehiiv_html import md_to_beehiiv_html
from beehiiv_client import create_post, get_post


def main(md_path: str) -> None:
    meta, body_md = parse(md_path)
    html = md_to_beehiiv_html(body_md, meta=meta)
    res = create_post(
        title=meta["title"],
        html=html,
        subject=meta.get("subject", meta["title"]),
        preview=meta.get("preview", ""),
        scheduled_at=meta.get("scheduled_at"),
        override_scheduled_at=meta.get("displayed_at"),
        tiers=tuple(meta.get("tiers", ["free"])),
        web_only=meta.get("web_only", False),
        slug=meta.get("slug"),
        tags=meta.get("tags", []),
    )
    post_id = res["data"]["id"]
    print("Created post:", post_id)
    print(get_post(post_id))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/publish.py drafts/<file>.md")
    main(sys.argv[1])
