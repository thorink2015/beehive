"""Render Markdown into a bulletproof, beehiiv-safe HTML body fragment.

Implements the Tank Mix template (see docs/email-template.md): table-first
single-column layout, 100% inline styles, MSO ghost table + VML buttons for
classic Outlook, dark-mode-resilient palette. Output is a BODY FRAGMENT ONLY
(no doctype/html/head/body) — beehiiv supplies the outer shell.

Segment system — each newsletter category gets its own visual treatment:
  ## Segment Name        -> uppercase section label + divider (divides categories)
  ### Subhead            -> serif subsection heading
  :::intro [label]       -> "from the cab" opener (accent bar + kicker)
  :::stat [big number]   -> hero number callout (e.g. one $/acre figure)
  :::quote               -> operator pull-quote; "~ Name, Company" line = attribution
  :::note                -> bordered callout box (regs, checklists)
  :::sponsor [label]     -> dashed sponsor box
  [label](url "button")  -> VML-hybrid CTA button

Brand values come from scripts/brand.yaml; pass `tokens=` to override per call.
"""
import pathlib
import re
from datetime import datetime, timezone

import bleach
import markdown
import yaml
from bleach.css_sanitizer import CSSSanitizer

_HERE = pathlib.Path(__file__).parent

ALLOWED_TAGS = [
    "h1", "h2", "h3", "h4", "p", "ul", "ol", "li", "blockquote",
    "strong", "em", "a", "img", "hr", "br", "code", "pre", "span",
]
ALLOWED_ATTRS = {
    "*": ["style"],
    "a": ["href", "title", "target", "rel", "style"],
    "img": ["src", "alt", "title", "width", "height", "style"],
}
_CSS = CSSSanitizer(allowed_css_properties=[
    "color", "background-color", "font-family", "font-size", "font-weight",
    "font-style", "line-height", "text-align", "text-decoration",
    "text-underline-offset", "letter-spacing", "text-transform", "margin",
    "margin-top", "margin-bottom", "padding", "padding-left", "padding-right",
    "padding-top", "padding-bottom", "border", "border-top", "border-left",
    "border-radius", "width", "max-width", "height", "display",
    "mso-line-height-rule", "-webkit-text-size-adjust", "-ms-interpolation-mode",
])

DEFAULT_TOKENS = {
    "brand_name": "Tank Mix",
    "website_url": "https://tankmix.example/",
    "logo_url": "",
    "logo_width_px": 140,
    "footer_note": "",
    "ink": "#1A1A1A",
    "ink_soft": "#3B3B3B",
    "muted": "#6B6B6B",
    "bg_canvas": "#FAF8F3",
    "bg_card": "#FFFFFF",
    "accent": "#2E5A1C",
    "accent_dark": "#6FA84A",
    "border": "#E5E1D6",
    "max_width_px": 600,
    "pad_outer": "24px 12px",
    "pad_card_px": 32,
    "font_heading": "Georgia, 'Times New Roman', 'Iowan Old Style', serif",
    "font_body": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
    "button_width_px": 240,
    "button_height_px": 48,
    "button_radius_px": 4,
}


def load_tokens(overrides=None):
    t = dict(DEFAULT_TOKENS)
    brand_file = _HERE / "brand.yaml"
    if brand_file.exists():
        loaded = yaml.safe_load(brand_file.read_text()) or {}
        t.update({k: v for k, v in loaded.items() if v not in (None, "")})
    if overrides:
        t.update({k: v for k, v in overrides.items() if v not in (None, "")})
    return t


# ── inline style strings, built from tokens ──────────────────────────────
def _styles(t):
    body = (f"font-family:{t['font_body']};-webkit-text-size-adjust:none;"
            "mso-line-height-rule:exactly;")
    head = (f"font-family:{t['font_heading']};font-weight:700;color:{t['ink']};"
            "mso-line-height-rule:exactly;")
    return {
        "h1": f"margin:0 0 16px 0;{head}font-size:30px;line-height:36px;letter-spacing:-0.2px;",
        # h2 is rendered as a per-category section header (see _section_header).
        "h3": f"margin:22px 0 8px 0;{head}font-size:18px;line-height:24px;",
        "h4": f"margin:18px 0 8px 0;{head}font-size:16px;line-height:22px;",
        "p":  f"margin:0 0 18px 0;{body}font-size:17px;line-height:27px;color:{t['ink']};",
        "ul": f"margin:0 0 18px 0;padding-left:24px;{body}font-size:17px;line-height:27px;color:{t['ink']};",
        "ol": f"margin:0 0 18px 0;padding-left:24px;{body}font-size:17px;line-height:27px;color:{t['ink']};",
        "li": "margin:0 0 8px 0;",
        "blockquote": (f"margin:24px 0;padding:4px 0 4px 18px;border-left:3px solid {t['accent']};"
                       f"font-family:{t['font_heading']};font-style:italic;font-size:18px;"
                       f"line-height:28px;color:{t['ink_soft']};mso-line-height-rule:exactly;"),
        "a": f"color:{t['accent']};text-decoration:underline;text-underline-offset:2px;",
        "code": ("font-family:ui-monospace,Menlo,Consolas,monospace;background-color:#F1EEE6;"
                 "padding:2px 5px;border-radius:3px;font-size:15px;"),
        "img": ("width:100%;max-width:100%;height:auto;display:block;border:0;"
                "-ms-interpolation-mode:bicubic;margin:8px 0 18px 0;"),
        "hr": f"border:0;border-top:1px solid {t['border']};margin:28px 0;height:0;line-height:0;font-size:0;",
        "lead": f"margin:0 0 20px 0;{body}font-size:18px;line-height:28px;color:{t['ink']};",
    }


_TAG_RE = {tag: re.compile(rf"<{tag}(\s|>)") for tag in
           ["h1", "h3", "h4", "p", "ul", "ol", "li", "blockquote",
            "a", "code", "img", "hr"]}


def _inject(html, styles):
    for tag, rx in _TAG_RE.items():
        style = styles[tag]
        html = rx.sub(lambda m, s=style, t=tag: f'<{t} style="{s}"{m.group(1)}', html)
    html = html.replace(f'<p style="{styles["p"]}"', f'<p style="{styles["lead"]}"', 1)
    return html


# ── per-category section markers (monogram chip + accent color) ───────────
# Each known segment gets a distinct, subtle identity. Edit/extend freely.
# Colors are muted, earthy, and all pass WCAG AA on white. White-on-chip too.
SEGMENT_STYLES = {
    "the window":            ("W", "#2E5A1C"),  # brand green
    "by the numbers":        ("#", "#2C5366"),  # steel-blue
    "the going rate":        ("$", "#6E5210"),  # ochre
    "the fine print":        ("§", "#34495E"),  # slate, section sign
    "the china watch":       ("C", "#8C3B2B"),  # brick
    "open acres":            ("A", "#5A6B1C"),  # olive
    "heard at the headland": ("“", "#5B4636"),  # warm brown, open quote
    "the tailgate":          ("★", "#8A4A10"),  # burnt orange, star
    "watch this":            ("▶", "#8C3B2B"),  # play triangle
    "tank talk":             ("T", "#1F5C58"),  # teal
    "in the cab":            ("P", "#2E5A1C"),
    "rate map":              ("M", "#6E5210"),
    "gear teardown":         ("G", "#4A5568"),  # steel
    "the bonus hustle":      ("H", "#3F6B1C"),
    "the books":             ("B", "#34495E"),
}


def _segment_lookup(text, t):
    key = re.sub(r"<[^>]+>", "", text).strip().lower()
    if key in SEGMENT_STYLES:
        return SEGMENT_STYLES[key]
    core = re.sub(r"^the\s+", "", key)
    return (core[:1].upper() if core else "▪", t["accent"])


def _section_header(text, t):
    """Minimal, Apple-leaning section marker: a thin rule, then a colored
    monogram glyph beside an uppercase colored label. No filled chip."""
    label = re.sub(r"<[^>]+>", "", text).strip().upper()
    mono, color = _segment_lookup(text, t)
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;margin:0;">'
        f'<tr><td height="38" style="height:38px;font-size:0;line-height:38px;">&nbsp;</td></tr>'
        f'<tr><td style="border-top:1px solid {t["border"]};padding-top:16px;">'
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
        f'<td valign="middle" style="padding-right:10px;font-family:{t["font_heading"]};font-size:19px;'
        f'font-weight:700;line-height:22px;color:{color};mso-line-height-rule:exactly;">{mono}</td>'
        f'<td valign="middle" style="font-family:{t["font_body"]};font-size:13px;font-weight:700;'
        f'letter-spacing:1.6px;text-transform:uppercase;color:{color};-webkit-text-size-adjust:none;">{label}</td>'
        f'</tr></table></td></tr>'
        f'<tr><td height="10" style="height:10px;font-size:0;line-height:10px;">&nbsp;</td></tr>'
        f'</table>'
    )


_H2_RE = re.compile(r"<h2\b[^>]*>(.*?)</h2>", re.S)


def _render_section_headers(html, t):
    return _H2_RE.sub(lambda m: _section_header(m.group(1), t), html)


# ── VML-hybrid CTA button ─────────────────────────────────────────────────
def render_button(href, label, t):
    w, h, r = t["button_width_px"], t["button_height_px"], t["button_radius_px"]
    arc = max(1, round(r / h * 100))
    return f"""<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="left" style="margin:8px 0 24px 0;"><tr><td align="center">
<!--[if mso]>
<v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{href}" style="height:{h}px;v-text-anchor:middle;width:{w}px;" arcsize="{arc}%" stroke="f" fillcolor="{t['accent']}">
<w:anchorlock/><center style="color:#FFFFFF;font-family:{t['font_heading']};font-size:16px;font-weight:700;letter-spacing:0.3px;">{label}</center>
</v:roundrect>
<![endif]-->
<!--[if !mso]><!-- -->
<a href="{href}" style="background-color:{t['accent']};border:1px solid {t['accent']};border-radius:{r}px;color:#FFFFFF;display:inline-block;font-family:{t['font_heading']};font-size:16px;font-weight:700;letter-spacing:0.3px;line-height:{h}px;text-align:center;text-decoration:none;width:{w}px;-webkit-text-size-adjust:none;">{label}</a>
<!--<![endif]--></td></tr></table>"""


_ANCHOR_RE = re.compile(r'<a\b([^>]*)>(.*?)</a>', re.S)
_HREF_RE = re.compile(r'href="([^"]+)"')


def _render_buttons(html, t):
    buttons = []

    def stash(m):
        attrs, inner = m.group(1), m.group(2)
        if 'title="button"' not in attrs:
            return m.group(0)
        href = _HREF_RE.search(attrs)
        if not href:
            return m.group(0)
        buttons.append(render_button(href.group(1), inner.strip(), t))
        return f"\x00BTN{len(buttons) - 1}\x00"

    html = _ANCHOR_RE.sub(stash, html)
    html = re.sub(r"<p\b[^>]*>\s*(\x00BTN\d+\x00)\s*</p>", r"\1", html)
    for i, btn in enumerate(buttons):
        html = html.replace(f"\x00BTN{i}\x00", btn)
    return html


# ── block-level + inline helpers (no directive parsing) ───────────────────
def _render_fragment(md_text, t):
    raw = markdown.markdown(md_text, extensions=["extra", "sane_lists"])
    clean = bleach.clean(raw, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS,
                         css_sanitizer=_CSS, strip=True)
    return _render_buttons(_inject(clean, _styles(t)), t)


def _inline(md_text, t):
    frag = _render_fragment(md_text, t)
    m = re.match(r"\s*<p[^>]*>(.*)</p>\s*$", frag, re.S)
    return (m.group(1) if m else frag).strip()


# ── segment components (directives) ───────────────────────────────────────
def _intro(arg, inner, t):
    label = (arg.strip() or "FROM THE CAB").upper()
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 8px 0;width:100%;">'
            f'<tr><td style="padding:0 0 0 18px;border-left:3px solid {t["accent"]};">'
            f'<div style="font-family:{t["font_body"]};font-size:13px;font-weight:700;letter-spacing:1.4px;'
            f'color:{t["accent"]};margin:0 0 10px 0;-webkit-text-size-adjust:none;">{label}</div>'
            f'{_render_fragment(inner, t)}</td></tr></table>')


def _stat(arg, inner, t):
    arg = arg.strip()
    lines = inner.split("\n")
    if arg:
        number, caption_md = arg, inner
    else:
        idx = next((k for k, l in enumerate(lines) if l.strip()), None)
        number = lines[idx].strip() if idx is not None else ""
        caption_md = "\n".join(lines[idx + 1:]) if idx is not None else ""
    cap = ""
    if caption_md.strip():
        cap = (f'<div style="font-family:{t["font_body"]};font-size:14px;line-height:20px;'
               f'color:{t["muted"]};margin-top:8px;-webkit-text-size-adjust:none;">{_inline(caption_md, t)}</div>')
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:8px 0 22px 0;width:100%;">'
            f'<tr><td style="background-color:{t["bg_canvas"]};border-left:4px solid {t["accent"]};padding:18px 20px;">'
            f'<div style="font-family:{t["font_heading"]};font-size:34px;line-height:40px;font-weight:700;'
            f'color:{t["accent"]};mso-line-height-rule:exactly;">{_inline(number, t)}</div>{cap}</td></tr></table>')


def _quote(arg, inner, t):
    body, attrib = [], ""
    for line in inner.split("\n"):
        s = line.strip()
        if not s:
            continue
        if s.startswith("~"):
            attrib = s.lstrip("~").strip()
        else:
            body.append(s)
    att = ""
    if attrib:
        att = (f'<div style="font-family:{t["font_body"]};font-size:14px;line-height:20px;'
               f'color:{t["muted"]};margin-top:12px;-webkit-text-size-adjust:none;">{_inline(attrib, t)}</div>')
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:8px 0 24px 0;width:100%;">'
            f'<tr><td style="padding:4px 0 4px 20px;border-left:3px solid {t["accent"]};">'
            f'<div style="font-family:{t["font_heading"]};font-style:italic;font-size:21px;line-height:30px;'
            f'color:{t["ink_soft"]};mso-line-height-rule:exactly;">{_inline(" ".join(body), t)}</div>{att}</td></tr></table>')


def _numbers(arg, inner, t):
    """Grouped 'by the numbers' list. One entry per line: `figure | caption`."""
    rows = []
    for line in inner.split("\n"):
        s = line.strip()
        if not s:
            continue
        fig, cap = (s.split("|", 1) + [""])[:2]
        cap_html = ""
        if cap.strip():
            cap_html = (f'<div style="font-family:{t["font_body"]};font-size:15px;line-height:22px;'
                        f'color:{t["ink"]};margin-top:3px;-webkit-text-size-adjust:none;">{_inline(cap.strip(), t)}</div>')
        top = "" if not rows else f"border-top:1px solid {t['border']};"
        rows.append(
            f'<tr><td style="{top}padding:14px 0;">'
            f'<div style="font-family:{t["font_heading"]};font-size:27px;line-height:31px;font-weight:700;'
            f'color:{t["accent"]};mso-line-height-rule:exactly;">{_inline(fig.strip(), t)}</div>{cap_html}</td></tr>')
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;margin:8px 0 18px 0;">'
            + "".join(rows) + "</table>")


def _note(arg, inner, t):
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:8px 0 22px 0;width:100%;">'
            f'<tr><td style="background-color:{t["bg_canvas"]};border:1px solid {t["border"]};border-radius:6px;'
            f'padding:18px 20px 2px 20px;">{_render_fragment(inner, t)}</td></tr></table>')


def _sponsor(arg, inner, t):
    label = (arg.strip() or "SPONSORED").upper()
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:28px 0 8px 0;width:100%;">'
            f'<tr><td style="background-color:{t["bg_canvas"]};border:1px dashed {t["accent"]};border-radius:6px;'
            f'padding:6px 20px 2px 20px;">'
            f'<div style="font-family:{t["font_body"]};font-size:11px;font-weight:700;letter-spacing:1.5px;'
            f'color:{t["muted"]};margin:12px 0 4px 0;-webkit-text-size-adjust:none;">{label}</div>'
            f'{_render_fragment(inner, t)}</td></tr></table>')


_DIRECTIVES = {"intro": _intro, "stat": _stat, "quote": _quote, "note": _note,
               "sponsor": _sponsor, "numbers": _numbers}
_SOURCE_RE = re.compile(r'<p style="[^"]*">\s*<em[^>]*>\s*(Source:.*?)\s*</em>\s*</p>', re.S | re.I)


def _style_sources(html, t):
    """Render a standalone italic 'Source: ...' line as a small muted caption."""
    repl = (f'<p style="font-family:{t["font_body"]};font-size:13px;line-height:18px;color:{t["muted"]};'
            f'margin:-6px 0 18px 0;-webkit-text-size-adjust:none;">\\1</p>')
    return _SOURCE_RE.sub(repl, html)
_FENCE_RE = re.compile(r"^:::\s*(\w+)\s*(.*)$")


def _build_body(md_text, t):
    lines = md_text.split("\n")
    out, blocks, i = [], [], 0
    while i < len(lines):
        m = _FENCE_RE.match(lines[i].strip())
        if m:
            kind, arg = m.group(1).lower(), m.group(2)
            inner, i = [], i + 1
            while i < len(lines) and lines[i].strip() != ":::":
                inner.append(lines[i])
                i += 1
            i += 1  # skip closing :::
            fn = _DIRECTIVES.get(kind)
            html = fn(arg, "\n".join(inner), t) if fn else _render_fragment("\n".join(inner), t)
            out += ["", f"DIRBLOCK{len(blocks)}MARKER", ""]
            blocks.append(html)
        else:
            out.append(lines[i])
            i += 1

    html = _render_fragment("\n".join(out), t)
    html = re.sub(r"<p\b[^>]*>\s*(DIRBLOCK\d+MARKER)\s*</p>", r"\1", html)
    for j, block in enumerate(blocks):
        html = html.replace(f"DIRBLOCK{j}MARKER", block)
    html = _style_sources(html, t)
    return _render_section_headers(html, t)


def _fmt_date(iso):
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).strftime("%B %-d, %Y")
    except (ValueError, TypeError):
        return ""


def _wordmark(t):
    if t.get("logo_url"):
        return (f'<img src="{t["logo_url"]}" alt="{t["brand_name"]}" '
                f'width="{t["logo_width_px"]}" '
                f'style="display:block;border:0;width:{t["logo_width_px"]}px;height:auto;">')
    return (f'<span style="display:inline-block;padding:4px 10px;background-color:{t["bg_canvas"]};'
            f'color:{t["accent"]};font-family:{t["font_heading"]};font-size:24px;font-weight:700;'
            f'letter-spacing:0.5px;border:1px solid {t["accent"]};">{t["brand_name"].replace(" ", "&nbsp;")}</span>')


def _issue_label(meta):
    bits = []
    if meta.get("issue_number"):
        bits.append(f"Issue {meta['issue_number']}")
    date = meta.get("issue_date") or _fmt_date(meta.get("displayed_at") or meta.get("scheduled_at"))
    if date:
        bits.append(date)
    return " &middot; ".join(bits)


def _wrapper(body_html, meta, t):
    cp = f"{t['pad_card_px']}px"
    canvas, card, border, muted = t["bg_canvas"], t["bg_card"], t["border"], t["muted"]
    fb, mw = t["font_body"], t["max_width_px"]

    preheader = meta.get("preheader") or meta.get("preview") or ""
    pre_html = ""
    if preheader:
        spacer = "&#847;&zwnj;&nbsp;" * 12
        pre_html = (f'<div style="display:none !important;visibility:hidden;mso-hide:all;'
                    f'font-size:1px;color:{canvas};line-height:1px;max-height:0;max-width:0;'
                    f'opacity:0;overflow:hidden;">{preheader} {spacer}</div>\n')

    label = _issue_label(meta)
    meta_html = ""
    if label:
        meta_html = (f'<div style="font-family:{fb};font-size:12px;color:{muted};'
                     f'margin-top:8px;-webkit-text-size-adjust:none;">{label}</div>')

    footer = t.get("footer_note") or f"Thanks for reading {t['brand_name']}."
    wordmark = _wordmark(t)

    return f"""<div style="color-scheme:light dark;supported-color-schemes:light dark;">
{pre_html}<!--[if mso]>
<xml><o:OfficeDocumentSettings><o:AllowPNG/><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml>
<![endif]-->
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%;background-color:{canvas};margin:0;padding:0;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;">
<tr><td align="center" style="padding:{t['pad_outer']};">
<!--[if mso | IE]>
<table role="presentation" align="center" cellpadding="0" cellspacing="0" border="0" width="{mw}"><tr><td>
<![endif]-->
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%;max-width:{mw}px;background-color:{card};border:1px solid {border};">
<tr><td style="padding:{cp} {cp} 8px {cp};">
<a href="{t['website_url']}" style="text-decoration:none;color:{t['accent']};">{wordmark}</a>
{meta_html}
</td></tr>
<tr><td style="padding:0 {cp};">
<hr style="border:0;border-top:1px solid {border};margin:16px 0 24px 0;height:0;line-height:0;font-size:0;">
</td></tr>
<tr><td style="padding:0 {cp} {cp} {cp};">
{body_html}
</td></tr>
<tr><td style="padding:0 {cp} {cp} {cp};border-top:1px solid {border};">
<p style="font-family:{fb};font-size:13px;line-height:21px;color:{muted};margin:24px 0 0 0;-webkit-text-size-adjust:none;mso-line-height-rule:exactly;">{footer}</p>
</td></tr>
</table>
<!--[if mso | IE]>
</td></tr></table>
<![endif]-->
</td></tr></table>
</div>"""


def md_to_beehiiv_html(md_text, meta=None, tokens=None):
    t = load_tokens(tokens)
    return _wrapper(_build_body(md_text, t), meta or {}, t)


# ── QA linter (machine-checkable subset of the pre-send checklist) ─────────
_IMG_RE = re.compile(r"<img\b[^>]*>", re.I)


def qa(html):
    """Return (errors, warnings). Errors should block a send."""
    errors, warnings = [], []
    size = len(html.encode("utf-8"))
    if size >= 102_400:
        errors.append(f"HTML is {size/1024:.1f} KB — over Gmail's 102 KB clip limit.")
    elif size > 90_000:
        warnings.append(f"HTML is {size/1024:.1f} KB — over the 90 KB target.")

    for tag in ["<style", "<link", "<script", "<iframe", "<form", "<input", "<audio", "<video"]:
        if tag in html.lower():
            errors.append(f"Contains {tag}> — beehiiv strips it or it won't render.")

    for img in _IMG_RE.findall(html):
        low = img.lower()
        src = re.search(r'src="([^"]*)"', img)
        url = src.group(1) if src else ""
        if url.startswith("data:"):
            errors.append("Image uses a data: URI — host on a CDN over HTTPS instead.")
        elif url and not url.startswith("https://"):
            errors.append(f"Image src is not HTTPS: {url}")
        if "alt=" not in low:
            warnings.append("An <img> is missing alt text.")
        if "width=" not in low or "height=" not in low:
            warnings.append("An <img> is missing width/height attributes (Outlook may blow it up).")

    if "—" in html:
        warnings.append("Contains an em dash (—). Tank Mix style avoids them.")

    return errors, warnings
