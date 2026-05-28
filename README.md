# beehive — semi-automated newsletter ops

Draft newsletter issues as Markdown, render them to beehiiv-ready HTML with
Claude Code, and publish to [beehiiv](https://www.beehiiv.com).

> **Why "render-then-paste"?** Programmatic publishing via beehiiv's API is
> Enterprise-plan-only. This repo's default flow works on **any plan** (including
> the free Launch plan): Claude renders paste-ready HTML, you click Send.

## Quick start

```bash
pip install -r requirements.txt
python scripts/render.py drafts/2026-05-01-issue-01.md
```

Then open the printed `rendered/*.preview.html` to preview, and paste the
`rendered/*.html` body into beehiiv's Post Builder.

## Layout

- `drafts/` — your issues, Markdown + YAML frontmatter
- `rendered/` — generated HTML (gitignored)
- `scripts/` — render / publish / verify tooling
- `CLAUDE.md` — the full playbook (constraints, backfill flow, HTML rules)

See **CLAUDE.md** for everything: the Enterprise-vs-free constraint, how to
backfill old issues as a web archive, beehiiv's HTML rules, and secret handling.
