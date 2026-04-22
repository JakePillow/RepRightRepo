from __future__ import annotations

import os


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def demo_mode_enabled() -> bool:
    return _env_flag("REPRIGHT_DEMO_MODE", False)


def demo_force_stub() -> bool:
    return demo_mode_enabled() and _env_flag("REPRIGHT_DEMO_FORCE_STUB", True)


def openai_key_present() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def coach_runtime_label() -> str:
    base_mode = (os.getenv("REPRIGHT_COACH_MODE", "auto") or "auto").strip().lower()

    if demo_force_stub():
        return "Stub (demo-safe)"
    if base_mode == "stub":
        return "Stub"
    if base_mode == "gpt":
        return "Live GPT"
    return "Live GPT" if openai_key_present() else "Stub fallback"


def demo_banner_text() -> str:
    coach_label = coach_runtime_label()
    return (
        f"Demo mode is on. Coach replies are running in {coach_label}. "
        "Use short, known-good clips for live presentation, and on iPhone upload from Photos or Files after recording."
    )
