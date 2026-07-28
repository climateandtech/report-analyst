# Git Hooks

These hooks run automatically when using this repository.

## Setup

After cloning, run once:

```bash
git config core.hooksPath .githooks
```

## Hooks

- **prepare-commit-msg**: Strips `Co-authored-by` trailers from commit messages.
