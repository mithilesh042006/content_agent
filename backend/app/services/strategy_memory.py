"""Strategy Memory — persistent history of past decisions and outcomes.

Enables compounding improvement: each decision is informed by prior performance.
Includes context-aware matching (audience + domain) and exponential decay.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field

from app.constants import MEMORY_DECAY_RATE

logger = logging.getLogger(__name__)

MEMORY_FILE = Path(__file__).parent.parent.parent / "data" / "strategy_memory.json"
MAX_MEMORY_SIZE = 100


class StrategyRecord(BaseModel):
    """One historical strategy decision + outcome."""

    decision_id: str
    timestamp: str
    platform: str
    format: str
    topic_keywords: List[str] = Field(default_factory=list)
    goal_type: str
    audience_segment: str = Field(default="")
    business_type: str = Field(default="")
    predicted: dict = Field(default_factory=dict)
    actual: dict = Field(default_factory=dict)
    outcome_score: float = Field(default=0.0)
    performance_ratio: float = Field(default=1.0)


def _audience_overlap(a: str, b: str) -> float:
    """Simple keyword overlap between two audience descriptions."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    return len(intersection) / min(len(words_a), len(words_b))


def _domain_overlap(a: str, b: str) -> float:
    """Simple keyword overlap between two business domain descriptions."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    return len(intersection) / min(len(words_a), len(words_b))


class StrategyMemory:
    """Persistent memory of past strategy performance with context-aware matching."""

    def __init__(self):
        self._records: List[StrategyRecord] = self._load()

    def save_record(self, record: StrategyRecord) -> None:
        """Append and persist a new record. Trims to MAX_MEMORY_SIZE."""
        self._records.append(record)
        if len(self._records) > MAX_MEMORY_SIZE:
            self._records = self._records[-MAX_MEMORY_SIZE:]
        self._persist()

    def get_memory_boost(
        self,
        platform: str,
        fmt: str,
        goal_type: str,
        audience_segment: str = "",
        business_type: str = "",
    ) -> float:
        """Context-aware memory boost with multi-dimensional matching and decay.

        Matching tiers:
          Tier 3 (full): platform + format + goal + audience + domain → weight 1.0
          Tier 2 (strong): platform + format + goal + audience      → weight 0.7
          Tier 1 (basic): platform + format + goal                  → weight 0.4

        Decay: 0.98^age where age = distance from newest record.

        Returns multiplier in [0.85, 1.15].
        """
        scored_records: list[tuple[float, StrategyRecord]] = []

        for record in self._records:
            if not (record.platform == platform
                    and record.format == fmt
                    and record.goal_type == goal_type):
                continue

            tier_weight = 0.4
            if audience_segment and record.audience_segment:
                if _audience_overlap(audience_segment, record.audience_segment) > 0.5:
                    tier_weight = 0.7
                    if business_type and record.business_type:
                        if _domain_overlap(business_type, record.business_type) > 0.5:
                            tier_weight = 1.0

            scored_records.append((tier_weight, record))

        if not scored_records:
            return 1.0

        total_weight = 0.0
        weighted_ratio_sum = 0.0
        n = len(scored_records)

        for i, (tier_w, record) in enumerate(scored_records):
            age = n - 1 - i
            recency_w = 0.5 + 0.5 * (i / max(n, 1))
            decay = MEMORY_DECAY_RATE ** age
            combined_w = tier_w * recency_w * decay
            weighted_ratio_sum += record.performance_ratio * combined_w
            total_weight += combined_w

        avg_ratio = weighted_ratio_sum / total_weight if total_weight > 0 else 1.0
        return round(max(0.85, min(1.15, avg_ratio)), 3)

    def get_recent_winners(self, limit: int = 5) -> List[StrategyRecord]:
        """Return the most recent N decision records."""
        return self._records[-limit:] if self._records else []

    def _load(self) -> List[StrategyRecord]:
        if MEMORY_FILE.exists():
            try:
                with open(MEMORY_FILE) as f:
                    raw = json.load(f)
                return [StrategyRecord(**r) for r in raw]
            except Exception:
                logger.warning("Corrupted strategy memory — resetting")
                return []
        return []

    def _persist(self) -> None:
        MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(MEMORY_FILE, "w") as f:
            json.dump([r.model_dump() for r in self._records], f, indent=2)


# Module-level singleton
strategy_memory = StrategyMemory()
