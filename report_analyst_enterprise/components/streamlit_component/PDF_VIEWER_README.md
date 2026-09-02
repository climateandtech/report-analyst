# PDF viewer

Edit the component in `../../web/src/pdf-viewer.js`. The build writes the bundle and PDF.js worker to `frontend/public`.

```bash
cd report_analyst_enterprise/components/web
npm install
npm test
npm run build
```

Chunk state is derived from the data passed to the component:

- No `question_id`: unmapped
- `question_id` without `is_evidence`: mapped
- `question_id` with `is_evidence`: analyzed
