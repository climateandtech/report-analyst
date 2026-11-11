# Bug: LLM chunk scoring always returns 0.0

Branch: `fix/llm-chunk-scoring-achat-messages`

## How it should be

With LLM scoring on, each retrieved chunk gets a real score between 0 and 1. Higher-scoring chunks move to the top of the pool and drive the answer.

## What happens

The scorer calls `achat(prompt=...)`, but the client needs `achat(messages=...)`. The error is caught and replaced with `0.0`, so every chunk looks useless. Enabling LLM scoring in the UI does nothing.

Example: on Continental GB 2025 / `tcfd_11`, the intensity targets sit around embedding rank 18. A working scorer would promote them to #1. With this bug they stay buried.

## Steps to reproduce

1. Open OSA, upload Continental GB 2025.
2. Question set TCFD, question `tcfd_11`.
3. Enable LLM scoring.
4. Check scores: all `0.0`. Logs show `missing a required argument: 'messages'`.
