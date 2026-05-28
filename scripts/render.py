"""Render a draft to paste-ready beehiiv HTML. WORKS ON ANY PLAN (no API).

This is the no-cost workaround for the fact that programmatic publishing is
Enterprise-only. It turns drafts/<file>.md into:

  rendered/<slug>.html          -> inline-styled HTML to paste into beehiiv's
                                    "Custom HTML" / source block
  rendered/<slug>.preview.html  -> a full web page you can open in a browser
                                    to see roughly how it will look

It also prints the Subject line, Preview text and Display date so you can copy
them straight into the matching fields in the beehiiv Post Builder.

Usage:
    python scripts/render.py drafts/2026-05-01-issue-01.md
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _draft import parse
from md_to_beehiiv_html import md_to_beehiiv_html, qa

PREVIEW_SHELL = """<!doctype html>
<html><head><meta charset="utf-8"><title>{title} — preview</title></head>
<body style="margin:0;background:#f4f4f5;padding:24px">
  <div style="max-width:600px;margin:0 auto;background:#fff;padding:32px;border-radius:8px">
{body}
  </div>
  <p style="max-width:600px;margin:16px auto;color:#999;font-family:sans-serif;font-size:12px">
    Local preview only. beehiiv adds its own email shell + footer on publish.
  </p>
</body></html>
"""


def main(md_path: str) -> None:
    meta, body_md = parse(md_path)
    slug = meta.get("slug") or pathlib.Path(md_path).stem
    html = md_to_beehiiv_html(body_md, meta=meta)

    out_dir = pathlib.Path(__file__).parent.parent / "rendered"
    out_dir.mkdir(exist_ok=True)
    body_path = out_dir / f"{slug}.html"
    preview_path = out_dir / f"{slug}.preview.html"
    body_path.write_text(html)
    preview_path.write_text(PREVIEW_SHELL.format(title=meta["title"], body=html))

    print("Rendered:")
    print(f"  paste-into-beehiiv : {body_path}")
    print(f"  browser preview    : {preview_path}")
    print()
    print("Copy these into the beehiiv Post Builder fields:")
    print(f"  Title         : {meta['title']}")
    print(f"  Subject line  : {meta.get('subject', meta['title'])}")
    print(f"  Preview text  : {meta.get('preview', '')}")
    print(f"  Web slug      : {slug}")
    if meta.get("displayed_at"):
        print(f"  Display date  : {meta['displayed_at']}  (Web tab -> Advanced -> Custom display date)")
    if meta.get("web_only"):
        print("  Audience      : WEB ONLY — uncheck all Email Audience options (backfill, no email sent)")

    errors, warnings = qa(html)
    print()
    if errors:
        print("QA ERRORS (fix before sending):")
        for e in errors:
            print(f"  ✗ {e}")
    if warnings:
        print("QA warnings:")
        for w in warnings:
            print(f"  ! {w}")
    if not errors and not warnings:
        print("QA: clean.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/render.py drafts/<file>.md")
    main(sys.argv[1])
