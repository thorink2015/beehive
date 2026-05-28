"""Convert Markdown into beehiiv-safe HTML.

beehiiv strips <style> and <link> tags and ignores CSS classes, so all
styling must be inline style="" attributes. This module renders Markdown to
HTML, injects inline styles onto known tags, then sanitizes the result.
"""
import re
import markdown
import bleach
from bleach.css_sanitizer import CSSSanitizer

ALLOWED_TAGS = [
    "p", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "ul", "ol", "li",
    "strong", "em", "a", "img", "figure", "figcaption", "hr", "br",
    "table", "thead", "tbody", "tr", "th", "td", "code", "pre", "span",
]
ALLOWED_ATTRS = {
    "*": ["style"],
    "a": ["href", "target", "rel", "style"],
    "img": ["src", "alt", "title", "style"],
}
CSS = CSSSanitizer(allowed_css_properties=[
    "color", "background-color", "font-family", "font-size", "font-weight",
    "font-style", "line-height", "text-align", "margin", "margin-top",
    "margin-bottom", "padding", "padding-left", "padding-right",
    "padding-top", "padding-bottom", "border", "border-top", "border-left",
    "border-radius", "width", "max-width", "text-decoration",
])

# Inline styles applied to each tag. Tweak these to restyle the whole newsletter.
INLINE = {
    "p":          "font-family:Inter,Arial,sans-serif;font-size:16px;line-height:1.55;margin:0 0 16px",
    "h1":         "font-family:Inter,Arial,sans-serif;font-size:28px;font-weight:700;margin:24px 0 12px",
    "h2":         "font-family:Inter,Arial,sans-serif;font-size:22px;font-weight:700;margin:20px 0 10px",
    "h3":         "font-family:Inter,Arial,sans-serif;font-size:18px;font-weight:700;margin:18px 0 8px",
    "ul":         "font-family:Inter,Arial,sans-serif;font-size:16px;line-height:1.55;margin:0 0 16px;padding-left:24px",
    "ol":         "font-family:Inter,Arial,sans-serif;font-size:16px;line-height:1.55;margin:0 0 16px;padding-left:24px",
    "li":         "margin:0 0 6px",
    "blockquote": "border-left:4px solid #ddd;padding:8px 16px;color:#555;margin:16px 0",
    "a":          "color:#1a73e8;text-decoration:underline",
    "code":       "font-family:ui-monospace,Menlo,monospace;background:#f4f4f5;padding:2px 4px;border-radius:3px",
    "img":        "max-width:100%;border-radius:6px",
    "hr":         "border:0;border-top:1px solid #e5e5e5;margin:24px 0",
}


def _inject(html: str) -> str:
    """Add inline style="" to the opening of each known tag (preserving attrs)."""
    for tag, style in INLINE.items():
        # <tag>  or  <tag attr="...">   ->   <tag style="..." attr="...">
        html = re.sub(
            rf"<{tag}(\s|>)",
            lambda m, s=style, t=tag: f'<{t} style="{s}"{m.group(1)}',
            html,
        )
    return html


def md_to_beehiiv_html(md_text: str) -> str:
    raw = markdown.markdown(md_text, extensions=["extra", "sane_lists", "smarty"])
    styled = _inject(raw)
    return bleach.clean(
        styled,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        css_sanitizer=CSS,
        strip=True,
    )
