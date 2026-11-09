# Install on Mac (Apple silicon)

## Why macOS says the app is damaged

Builds that are not signed with an Apple **Developer ID** and **notarized** get a quarantine flag when someone downloads them. On Apple silicon, Gatekeeper then shows:

> “Open Sustainability Analyst” is damaged and can’t be opened. You should move it to the Trash.

That message is misleading. The download is usually fine. **System Settings → Privacy & Security → Open Anyway** often does nothing for this case. Ad-hoc signing (what we can do without Apple) does not remove the quarantine. The durable fix is a notarized Developer ID release.

## Fast path (no Terminal)

1. Open the DMG and drag **Open Sustainability Analyst** to Applications.
2. Double-click **Clear Quarantine.command** (ships next to the DMG/zip).
3. Confirm the macOS prompts. The app should open. You only need this once per download.

If macOS blocks the `.command` file the same way, right-click it → **Open**, or run the Terminal line below once.

## Terminal fallback

```bash
xattr -cr "/Applications/Open Sustainability Analyst.app"
open "/Applications/Open Sustainability Analyst.app"
```

If the path is wrong, type `xattr -cr ` (with a trailing space), drag the app into the Terminal window, then press Return.

## Requirements

- Apple silicon Mac (arm64). An Intel build is a separate download.
- First launch needs network if the remote update/notice check is enabled; analysis still needs your own API keys in the app.
