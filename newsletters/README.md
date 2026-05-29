# Tank Mix — rendered newsletters

Final, paste-ready HTML for every issue, generated from `drafts/*.md` by
`scripts/render.py`. Two files per issue:

- `*.html` — the body to paste into beehiiv's Custom HTML block.
- `*.preview.html` — open in a browser to eyeball the design (adds a page shell;
  beehiiv supplies its own header/footer on a real send).

Regenerate any issue with `python scripts/render.py drafts/<file>.md`.

| # | Display date | Audience | Subject | File |
|---|---|---|---|---|
| 1 | Apr 21, 2026 | Web-only backfill | Corn went in 3 weeks early. Here's your week. | `issue-1-corn-went-in-early.html` |
| 2 | Apr 28, 2026 | Web-only backfill | Answer the FAA's email or lose your exemption | `issue-2-answer-the-faa.html` |
| 3 | May 5, 2026 | Web-only backfill | Rates hit $13. The money moved. | `issue-3-rates-hit-13.html` |
| 4 | May 12, 2026 | Web-only backfill | Dicamba just got banned from your drone. | `issue-4-dicamba-banned.html` |
| 5 | May 19, 2026 | Web-only backfill | Your DJI just got 2 more years of updates. | `issue-5-dji-two-more-years.html` |
| 6 | May 26, 2026 | Web-only backfill | The "drones cost more" myth just died. | `issue-6-cost-myth-died.html` |
| 7 | Jun 4, 2026 | **Live email** | Part 108 is about to land. Here is what it means for you. | `issue-7-part-108.html` |

## Before sending

- Issues 1–6 are web-only archive backfills: uncheck all Email Audience options,
  set the Custom display date, publish.
- Issue 7 is the first live send and embeds the Sentera sponsor card. Refresh the
  crop data (June 1 report), confirm the Part 108 rule status, and host the two
  Sentera images on beehiiv (or merge so the GitHub raw URLs resolve).
- Run one real test send (Gmail + phone + Outlook) before any live blast.
