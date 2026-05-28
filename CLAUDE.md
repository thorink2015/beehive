# Newsletter Ops — Claude Code Playbook

This repo runs a **semi-automated newsletter on beehiiv**. Claude drafts and
renders issues here; the human publishes via the beehiiv web app (or via API on
Enterprise). Read this file before doing newsletter work.

## The hard constraint (read first)

Programmatic **create / schedule / send** of beehiiv posts via the API is
**Enterprise-plan-only** (Send API, in beta). On Launch (free) / Scale / Max,
`POST /posts` returns **403**. That is expected, not a bug.

Therefore the default workflow is **render-then-paste**, which works on ANY plan:

1. Write/edit the issue as Markdown in `drafts/`.
2. Run `python scripts/render.py drafts/<file>.md`.
3. Open the `*.preview.html` to eyeball it; paste the `*.html` body into the
   beehiiv Post Builder's HTML/source block; copy Subject/Preview/Display-date
   from the script output into the matching fields.
4. The human clicks Send/Schedule in beehiiv.

Only switch to the API path (`scripts/publish.py`) if the user confirms they are
on **Enterprise with Send API access**.

## Backfilling old issues (building an archive)

To add past issues without emailing current subscribers:
- Set `web_only: true` and a past `displayed_at` in the draft frontmatter.
- In beehiiv: **uncheck all Email Audience options**, keep Web Audience, then
  Web tab → Advanced settings → **Custom display date** → set the historical date.
- You can NOT make subscribers receive an email with a past timestamp. The only
  clean backfill is web-only. Never email an old issue to the whole list.

## Files

| Path | Purpose |
|---|---|
| `drafts/*.md` | Source issues. Markdown + YAML frontmatter (see example). |
| `rendered/*.html` | Generated. Body to paste + browser preview. Gitignored. |
| `scripts/render.py` | Markdown → paste-ready beehiiv HTML + QA lint. **Works on any plan.** |
| `scripts/publish.py` | Markdown → API post. **Enterprise only** (else 403). |
| `scripts/verify.py` | Read-only connection check; lists recent posts. |
| `scripts/beehiiv_client.py` | Thin REST client. Reads work on any paid plan. |
| `scripts/md_to_beehiiv_html.py` | Bulletproof template renderer + `qa()` linter. |
| `scripts/brand.yaml` | **Brand tokens** (name, colors, fonts, logo). Edit to restyle. |
| `docs/email-template.md` | Full template spec: constraints, palette, fonts, QA. |
| `.mcp.json` | Wires the official beehiiv MCP (read-only analytics) into Claude. |

## The HTML template (Tank Mix)

`md_to_beehiiv_html.py` renders a **bulletproof body fragment**: table-first,
single-column, 600px, 100% inline styles, MSO ghost table + VML buttons for
classic Outlook, dark-mode-resilient palette. Full spec in `docs/email-template.md`.

- **Restyle the whole newsletter** by editing `scripts/brand.yaml` — never
  hand-edit styles in the Python.
- **Buttons:** write a Markdown link with the title `button`:
  `[Read the full issue](https://... "button")`.
- **Headings** start at `##` (beehiiv supplies the H1 post title).
- `render.py` prints QA errors/warnings (size, stripped tags, non-HTTPS images,
  missing alt/dimensions, em dashes). Fix errors before sending.
- The machine checks are a subset; still do the manual client tests in
  `docs/email-template.md` (Gmail, Apple Mail, classic + new Outlook) on a real
  test send before a big send.

## Draft frontmatter keys

```yaml
title:        "Issue #N — ..."     # required
subject:      "..."                 # email subject; defaults to title
preview:      "..."                 # inbox preview text (fallback for preheader)
preheader:    "..."                 # hidden inbox preview line; ≤100 chars
slug:         "issue-n-..."         # web URL slug
issue_number: 1                     # shown in the wordmark meta line
displayed_at: "2026-05-01T13:00:00Z" # ISO-8601 UTC; visible date (backfill)
scheduled_at: "2026-06-04T13:00:00Z" # future send time (API path only)
web_only:     true                  # true = no email sent (use for backfill)
tiers:        ["free"]
tags:         ["intro"]
```

## HTML rules beehiiv enforces

- `<style>` and `<link>` are stripped; CSS classes do nothing. **Inline styles only.**
- Keep total email under **~102 KB** or Gmail clips it. Host images on a CDN and
  reference by absolute HTTPS URL; don't base64-embed large images.
- A blank styled **Post Template** in beehiiv (`BEEHIIV_POST_TEMPLATE_ID`) gives
  consistent fonts/colors when using the API path.

## Secrets

- API key + publication ID live in `.env` (gitignored). Never commit them.
- The beehiiv MCP uses OAuth; no key is stored in the repo.
- API write access requires API key created at: beehiiv → Settings → Workspace
  Settings → API (Owner/Admin; may require Stripe Identity Verification).

## The MCP (analytics only, v1)

`.mcp.json` wires `https://mcp.beehiiv.com/mcp`. It is **read-only**: great for
"analyze my last 10 subject lines for open-rate patterns", useless for publishing.
Authenticate with `/mcp` in Claude Code (browser OAuth).

## Plan reference

- **Launch (free):** drafting + paste-publish + MCP reads. No API writes.
- **Scale (~$43/mo annual):** + subscriber/segment/webhook API, MCP. No post writes.
- **Enterprise (custom):** + Send API (create/schedule/send posts). Required for
  `scripts/publish.py`.
