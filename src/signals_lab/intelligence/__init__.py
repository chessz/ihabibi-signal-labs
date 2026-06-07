"""Intelligence pipeline — dedup, credibility, orchestration."""

from signals_lab.intelligence.config_loader import get_intelligence_config
from signals_lab.intelligence.credibility import apply_credibility_penalties, score_credibility
from signals_lab.intelligence.dedup import assign_dedup_keys, merge_confirmations
from signals_lab.intelligence.engine import IntelligencePipeline
from signals_lab.intelligence.novelty import score_novelty_batch

__all__ = [
    "IntelligencePipeline",
    "assign_dedup_keys",
    "apply_credibility_penalties",
    "get_intelligence_config",
    "merge_confirmations",
    "score_credibility",
    "score_novelty_batch",
]
