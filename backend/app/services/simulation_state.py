"""Persistent simulation state — multipliers that evolve via feedback."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

STATE_FILE = Path(__file__).parent.parent.parent / "data" / "simulation_state.json"

DEFAULT_STATE = {
    "platform_multiplier": {
        "LinkedIn": 1.0, "X": 1.0, "Instagram": 1.0,
        "TikTok": 1.0, "Facebook": 1.0, "YouTube": 1.0,
    },
    "format_multiplier": {
        "static image": 1.0, "carousel": 1.0, "short-form video": 1.0,
        "long-form video": 1.0, "long-form text": 1.0, "infographic": 1.0,
        "live stream": 1.0,
    },
    "cta_multiplier": {
        "conversion": 1.0, "awareness": 1.0, "lead-generation": 1.0,
        "retention": 1.0, "traffic": 1.0, "engagement": 1.0,
    },
    "time_synergy_multiplier": {},
    "version": 0,
}


class SimulationState:
    """Persistent simulation parameters that evolve via feedback.

    Multipliers are clamped to [0.5, 1.5] to prevent runaway drift.
    """

    def __init__(self):
        self._state = self._load()

    @property
    def platform_multiplier(self) -> dict[str, float]:
        return self._state.get("platform_multiplier", DEFAULT_STATE["platform_multiplier"])

    @property
    def format_multiplier(self) -> dict[str, float]:
        return self._state.get("format_multiplier", DEFAULT_STATE["format_multiplier"])

    @property
    def cta_multiplier(self) -> dict[str, float]:
        return self._state.get("cta_multiplier", DEFAULT_STATE["cta_multiplier"])

    @property
    def time_synergy_multiplier(self) -> dict[str, float]:
        return self._state.get("time_synergy_multiplier", {})

    @property
    def version(self) -> int:
        return self._state.get("version", 0)

    def apply_updates(self, updates: dict[str, dict[str, float]]) -> None:
        """Apply feedback-driven parameter updates.

        Multipliers are clamped to [0.5, 1.5] to prevent runaway drift.
        """
        for category, deltas in updates.items():
            if category not in self._state:
                self._state[category] = {}
            for key, delta in deltas.items():
                current = self._state[category].get(key, 1.0)
                self._state[category][key] = round(
                    max(0.5, min(1.5, current + delta)), 3
                )
        self._state["version"] = self._state.get("version", 0) + 1
        self._save()

    def _load(self) -> dict:
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE) as f:
                    return json.load(f)
            except (json.JSONDecodeError, KeyError):
                logger.warning("Corrupted simulation state file — resetting to defaults")
        return json.loads(json.dumps(DEFAULT_STATE))

    def _save(self) -> None:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(self._state, f, indent=2)


# Module-level singleton
simulation_state = SimulationState()
