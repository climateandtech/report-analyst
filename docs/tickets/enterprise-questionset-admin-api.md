# Push question sets to enterprise instances

**GitHub:** [climateandtech/report-analyst#203](https://github.com/climateandtech/report-analyst/issues/203)

## Background

- Custom question sets today require an app **deploy** (or manual files on the server) to reach a running installation.

## Goals

- Allow **pushing a question set** to **enterprise** instances without a full redeploy for content changes.
- Store pushed sets on the instance’s **existing persistent database** (same storage as analysis cache on production hosts like Actwyser), not as the primary copy on the container filesystem. Built-in frameworks in the image stay as they are; pushed sets **add to** the list users see.

## Acceptance criteria

- An **enterprise** operator can use the **API** to push a question set to a **deployed** instance.
- The pushed set appears in the app’s **question set** selection alongside built-in frameworks.
- Pushed sets **survive redeploy** when the instance uses normal persistent storage (not ephemeral disk-only installs).