"""Phase 31: protected boundaries for Atlas self-extension."""
PROTECTED_PATH_PREFIXES = ("security/", "privacy/", "permissions/", "memory/", "extension/")
PROTECTED_FILES = {"extension/protected_core.py", "extension/self_extension.py"}

def is_protected(path: str) -> bool:
    p = path.replace("\\", "/").lstrip("./")
    return p in PROTECTED_FILES or any(p.startswith(x) for x in PROTECTED_PATH_PREFIXES)
