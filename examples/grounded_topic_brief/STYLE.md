Same content as the Agent Skill reference: `.claude/skills/osa-library-host-app/references/style.md`.
# Style (shadcn-flavoured, illustrative)

Not a full shadcn/ui install. Steal the ideas: neutral surface, clear type, small primitives.

## Tokens

| Token | Example | Use |
|-------|---------|-----|
| `--background` | `#f4f0e7` | Page |
| `--card` | `#fffdf8` | Brief panel |
| `--foreground` | `#14221c` | Body |
| `--muted` | `#4a5c52` | Secondary text |
| `--border` | `#d5cdc0` | Dividers |
| `--primary` | `#0f6b4c` | Primary button |
| `--primary-foreground` | `#ffffff` | On primary |
| `--accent` | `#d8eee4` | Soft badges |
| `--warning` | `#f3e6c8` / `#8a5a12` | Gaps |

Radius: ~12–16px on cards; pill only on badges/buttons. One soft shadow on the brief card.

Type: one serif for the page title (e.g. Fraunces), one sans for UI (e.g. IBM Plex Sans).

## Primitives

- **Button**: primary filled, ghost outline. Labels: `Generate brief`, `Sample`.
- **Card**: brief container (title, report name, findings).
- **Badge**: sample / answered / evidence / gaps counts.
- **Separator**: between findings.
- **Callout**: evidence = left border + soft green; gaps = soft warning fill.

Optional later: `npx shadcn@latest add button card badge separator`. Until then, plain HTML/CSS is fine.

## Copy

- One short lede under the title.
- No em dashes.
- Labels: `Evidence`, `Gaps`.
- Status: one sentence.

## Layout

```
eyebrow
title
one-line lede
[ upload | Generate | Sample ]
brief card
  title + report
  badges
  finding x N
  <details> JSON
```
