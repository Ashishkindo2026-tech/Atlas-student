# Atlas Student

**Local-first AI assistant built for students.**

Atlas combines a local language model with memory, reasoning, voice, education tools and student workflows while keeping the core experience on the user's machine.

## Current foundation

- Python 3.12 runtime
- Ollama-compatible local LLM client
- Persistent memory and conversation history
- Voice input/output
- Education-library ingestion
- Student/project/task workflows
- Automated pytest verification
- GitHub Actions CI
- Central runtime configuration

## Quick start

1. Install Python 3.12.
2. Install dependencies with `python -m pip install -e ".[dev]"`.
3. Install and start Ollama locally.
4. Pull the model configured by `ATLAS_OLLAMA_MODEL` (default: `qwen2.5:1.5b`).
5. Run `python atlas.py`.
6. Run tests with `python -m pytest`.

## Configuration

Atlas is local-first by default. Optional environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `ATLAS_OLLAMA_URL` | `http://127.0.0.1:11434` | Local Ollama endpoint |
| `ATLAS_OLLAMA_MODEL` | `qwen2.5:1.5b` | Local model |
| `ATLAS_HISTORY_LIMIT` | `50` | Conversation context size |
| `ATLAS_REQUEST_TIMEOUT` | `120` | LLM request timeout in seconds |
| `ATLAS_LIBRARY_DIR` | `education/library` | Local study-library location |

## Engineering roadmap

Atlas is being developed against a measurable 10/10 standard across ten phases:

**A Foundation → B Intelligence → C Student → D Interaction → E Performance → F Reliability → G Privacy → H Distribution → I Benchmark → J 10/10 loop.**

A phase is not considered complete merely because code exists. It must be tested, measured and documented.

## Architecture

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for subsystem boundaries and dependency rules.

## Privacy

Do not commit passwords, API keys, private tokens, personal databases or generated user-history files. Atlas's default model endpoint is loopback/local.
