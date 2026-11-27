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

## Local CI parity

```bash
./scripts/ci-parity.sh before-push   # packaging tests + pip in python:3.12-slim
./scripts/ci-parity.sh pytest        # full suite (CI test job)
./scripts/ci-parity.sh docker-build  # optional
```

Full QG runs `tests/test_dockerfile_packaging.py`; set `QG_CI_PARITY=1` (or change `Dockerfile` / `requirements*.txt`) to run slim deps inside QG.

### Why `main` is green but your PR is red

`main` stays green because it does not contain your branch’s files yet. CI on the PR applies **repo-wide** `black --check .` and full pytest (including `tests/test_linting.py`). Unformatted or new code in **your diff** fails those checks — that is correct post-merge behavior, not a regression on `main`.

Session **quality gate** is intentionally narrower (ruff + affected pytest on paths you touched vs `BASE_REF`) so parallel agents do not fix each other’s unrelated dirty files. That scope is **not** the same as CI `lint` / full `test`. Local QG green + CI red on the same branch is expected until you run CI-shaped checks (`black --check .`, `./scripts/ci-parity.sh pytest`) before push.