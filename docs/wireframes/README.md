# Report Analyst wireframes

Sketch screens of the Report Analyst UI (analysis, consolidated results, PDF viewer, benchmarking). No CT Platform chrome.

Open the HTML in a browser:

- [Analysis](out/analysis.html)
- [View all results](out/view-all-results.html)
- [PDF viewer](out/report-viewer.html)
- [Benchmarking](out/benchmarking.html)

Sources are WireMD Markdown in `pages/`. Callouts, `{#id}` anchors, PDF overlays (`.retrieved` / `.evidence`), and selected config cards (`{.primary}` on a grid heading) need the WireMD fork branch `feat/callouts` (repo `devolute/wiremd`).

Rebuild after editing a page:

```bash
cd /path/to/wiremd   # feat/callouts
npm run build
node bin/wiremd.js /path/to/report-analyst/docs/wireframes/pages/analysis.md \
  -s sketch -o /path/to/report-analyst/docs/wireframes/out/analysis.html
```

Repeat for `view-all-results`, `report-viewer`, and `benchmarking`.
