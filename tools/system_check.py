"""Atlas Student local runtime diagnostic.

Safe to run without Ollama: unavailable external services are reported rather
than crashing the diagnostic. This is intentionally dependency-light so it can
also help diagnose installation problems.
"""
from __future__ import annotations

import importlib
import json
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Running ``python tools/system_check.py`` puts ``tools/`` on sys.path instead
# of the project root. Add the root explicitly so package imports work from a
# normal Windows command prompt without requiring PYTHONPATH.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def _module(name: str) -> Check:
    try:
        importlib.import_module(name)
        return Check(name, True, "imported")
    except Exception as exc:
        return Check(name, False, f"{type(exc).__name__}: {exc}")


def _ollama() -> list[Check]:
    try:
        from atlas_core.config import CONFIG
        base = CONFIG.ollama_base_url.rstrip("/")
        model = CONFIG.ollama_model
    except Exception as exc:
        return [Check("Ollama configuration", False, str(exc))]

    try:
        request = Request(f"{base}/api/version", method="GET")
        with urlopen(request, timeout=3) as response:
            data = json.loads(response.read().decode("utf-8"))
        version = data.get("version", "unknown") if isinstance(data, dict) else "unknown"
        service = Check("Ollama service", True, f"online ({version})")
    except (URLError, HTTPError, TimeoutError, OSError) as exc:
        return [Check("Ollama service", False, f"unavailable at {base}: {exc}")]
    except Exception as exc:
        return [Check("Ollama service", False, f"invalid response: {exc}")]

    try:
        request = Request(f"{base}/api/tags", method="GET")
        with urlopen(request, timeout=3) as response:
            data = json.loads(response.read().decode("utf-8"))
        models = data.get("models", []) if isinstance(data, dict) else []
        names = {item.get("name") for item in models if isinstance(item, dict)}
        if model in names:
            model_check = Check("Ollama model", True, f"{model} available")
        else:
            model_check = Check("Ollama model", False, f"{model} not found")
    except Exception as exc:
        model_check = Check("Ollama model", False, f"could not inspect models: {exc}")
    return [service, model_check]


def run_checks() -> list[Check]:
    checks = [
        Check("Python", sys.version_info >= (3, 10), platform.python_version()),
        _module("atlas_core.config"),
        _module("brain.agent"),
        _module("memory.memory_manager"),
        _module("gui.usage_tracker"),
        _module("gui.atlas_customizer"),
    ]
    checks.extend(_ollama())
    return checks


def main() -> int:
    print("ATLAS STUDENT SYSTEM CHECK")
    print("=" * 30)
    checks = run_checks()
    for check in checks:
        mark = "PASS" if check.ok else "WARN"
        print(f"[{mark}] {check.name}: {check.detail}")
    passed = sum(check.ok for check in checks)
    print("-" * 30)
    print(f"RESULT: {passed}/{len(checks)} checks passed")
    print("Note: Ollama warnings do not prevent this diagnostic from completing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
