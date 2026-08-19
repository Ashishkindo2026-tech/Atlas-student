# Atlas Reliability Contract

Atlas is designed to degrade safely instead of crashing when a peripheral service fails.

## Guarantees

- Ollama failures are isolated from Atlas core.
- Persistent state is written atomically where supported.
- Corrupt state is preserved before recovery is attempted.
- Unknown tools are denied by default.
- High-risk tool operations require explicit confirmation.
- Runtime state is not intended to be committed to Git.
- Voice is allowed to fail without destroying the text interface.

## Failure hierarchy

1. Detect the failing component.
2. Record a useful diagnostic.
3. Retry only when the operation is safe to retry.
4. Fall back to a degraded capability when possible.
5. Preserve user data.
6. Keep the main application alive.

## What a 10/10 reliability target means

A perfect score is a target, not a claim. Atlas should earn it through tests that prove failure recovery, data integrity, permissions, concurrency behavior, and interface fallbacks rather than through feature count alone.
