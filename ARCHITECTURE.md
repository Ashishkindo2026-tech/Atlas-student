# Atlas Student — Architecture

## Boundary rules

- `atlas.py` is the CLI composition root. It coordinates subsystems; it should not contain subsystem implementation details.
- `brain/` owns orchestration, reasoning, context and decision logic.
- `llm/` owns model-provider communication. Provider-specific details stay behind its client interface.
- `memory/` owns persistent memory and conversation history.
- `voice/` owns speech input/output.
- `education/`, `student/`, `planning/` and `Study/` own student-facing capabilities.
- `tools/` owns explicit system/tool integrations.
- `tests/` verifies contracts between these boundaries.
- `atlas_core/` contains cross-cutting foundation code that must remain dependency-light.

## Dependency direction

`composition root -> feature/orchestration -> domain services -> infrastructure adapters`

Infrastructure modules must not import the CLI entry point. Cross-cutting configuration
must come from `atlas_core.config`, not duplicated constants.

## Runtime configuration

Environment variables are optional and local-only:

- `ATLAS_OLLAMA_URL`
- `ATLAS_OLLAMA_MODEL`
- `ATLAS_HISTORY_LIMIT`
- `ATLAS_REQUEST_TIMEOUT`
- `ATLAS_LIBRARY_DIR`

No secrets belong in source control.

## Definition of done for Phase A

- [x] Central configuration exists.
- [x] Configuration is environment-overridable.
- [x] Defaults are deterministic and local-first.
- [x] Architecture boundaries are documented.
- [x] Dependency metadata is declared in `pyproject.toml`.
- [ ] All legacy entry points are consolidated.
- [ ] All modules satisfy the boundary rules.
- [ ] Static quality gates are enforced in CI.
