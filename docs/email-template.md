# Tank Mix — Email Template Reference

Distilled from the template research brief. This is the spec the renderer
(`scripts/md_to_beehiiv_html.py`) implements. Edit brand values in
`scripts/brand.yaml`, not here.

## Non-negotiable constraints (beehiiv)

- Output is a **body fragment only** — no `<!doctype>`, `<html>`, `<head>`, or
  `<body>`. beehiiv wraps it in its own shell and supplies the post H1, byline,
  and CAN-SPAM/GDPR + unsubscribe footer.
- **100% inline `style=""`.** beehiiv strips `<style>`, `<link>`, `<script>`.
  CSS classes survive textually but are inert. Media queries are unavailable.
- Keep rendered HTML **under 90 KB** (hard ceiling 102 KB — Gmail clips above it).
- Images: **absolute HTTPS CDN URLs only.** Never base64/`data:` embed.
- Sections start at **`<h2>`** (beehiiv's post title is the H1).

## Layout

- Single column, **600px max content width**, table-first.
- Outer 100%-width table sets the canvas color; inner `max-width:600px` table is
  the content card; an **MSO ghost table** forces classic Outlook to honor 600px.
- `role="presentation"` on every layout table (screen readers skip structure).
- Per-`<td>` padding (Outlook ignores `margin` on most elements).
- Outlook needs MSO conditionals + VML buttons **through at least 2028** — keep them.

## Palette (all pairs pass WCAG AA; body + button hit AAA)

| Token | Hex | Use |
|---|---|---|
| Ink | `#1A1A1A` | Body text |
| Ink soft | `#3B3B3B` | Blockquote / secondary |
| Muted | `#6B6B6B` | Captions, meta, footer |
| Canvas | `#FAF8F3` | Outer background (warm off-white) |
| Card | `#FFFFFF` | Inner content card |
| Accent | `#2E5A1C` | Wordmark, links, button bg (8.09:1 white-on-green, AAA) |
| Accent (dark) | `#6FA84A` | Lighter green for inverted backgrounds — **text only, never button bg** |
| Border | `#E5E1D6` | Dividers, hr, card border |

## Fonts

- **Headings / wordmark / button:** `Georgia, 'Times New Roman', 'Iowan Old Style', serif`
- **Body:** `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif`
- Always put a **known-installed font first** — classic Outlook skips the whole
  fallback chain and defaults to Times New Roman otherwise.
- Add `mso-line-height-rule:exactly` and `-webkit-text-size-adjust:none` to text.

### Type scale

| Role | Size / line-height | Weight |
|---|---|---|
| H2 (section) | 22 / 29 | 700 |
| H3 (subsection) | 18 / 24 | 700 |
| Lead paragraph | 18 / 28 | 400 |
| Body | 17 / 27 | 400 |
| Blockquote | 18 / 28 italic | 400 |
| Caption / meta | 13 / 20 | 400 |
| Button label | 16 / 48 (= height) | 700 |

## Dark mode

- Can't rely on `prefers-color-scheme` CSS (beehiiv strips `<style>`).
- Gmail/Outlook force-invert; design colors that survive (off-white + near-black,
  not pure `#FFF`/`#000`).
- Inline `color-scheme: light dark` on the outer wrapper (Apple Mail honors it).
- Give the wordmark a **green halo border** so it stays legible after inversion.

## Buttons

VML `<v:roundrect>` for classic Outlook (inside `<!--[if mso]>`) + inline-styled
`<a>` fallback for everyone else. New Outlook (Chromium) ignores MSO and uses the
`<a>`. Button bg stays `#2E5A1C` in light **and** dark (white-on-green = 8.09:1).
Size 240×48 meets touch-target minimums.

## Pre-send QA checklist

`scripts/render.py` runs the machine-checkable subset automatically (`qa()`); the
rest are manual client tests.

**Automated:**
- [ ] Size < 90 KB (hard fail ≥ 102 KB)
- [ ] No `<style>` / `<link>` / `<script>` / `<iframe>` / `<form>` / `<input>` / `<audio>` / `<video>`
- [ ] All image `src` are absolute `https://`, no `data:` URIs
- [ ] Every `<img>` has `alt`, `width`, `height`
- [ ] No em dashes / double hyphens in body copy (Tank Mix style rule)

**Manual (test send):**
- [ ] Gmail web (light) — no clip warning
- [ ] Gmail Android (forced dark) — colors survive, wordmark legible
- [ ] Apple Mail iOS light + dark
- [ ] Classic Outlook Windows — button shaped, font not Times New Roman
- [ ] New Outlook Windows — no double buttons, no border-radius glitch
- [ ] Forwarded test from Gmail — layout holds, no duplicate button
- [ ] All links work; unsubscribe appears exactly once
- [ ] Subject ≤ 50 chars and doesn't duplicate the preheader

## Open items to verify on first real test send

- Does beehiiv keep `<table role="presentation">` and the MSO comments? (Expected yes.)
- Does beehiiv strip `<meta>`? (We inline `color-scheme` on the wrapper as a fallback.)
- Is the HTML-snippet block available on your beehiiv plan? If not, fall back to
  mapping Markdown onto beehiiv's native UI blocks.
