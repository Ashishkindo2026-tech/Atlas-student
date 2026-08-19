"""Non-destructive Atlas health diagnostics."""
from datetime import datetime, timezone


def check_ollama(client):
    status = client.status()
    if not status["service"]:
        return {"name": "ollama", "status": "offline", **status}
    if not status["model_available"]:
        return {"name": "ollama", "status": "model_missing", **status}
    return {"name": "ollama", "status": "healthy", **status}


def run_health_checks(llm_client):
    checks = [check_ollama(llm_client)]
    overall = "healthy" if all(item["status"] == "healthy" for item in checks) else "degraded"
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": overall,
        "checks": checks,
    }
