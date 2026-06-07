"""Orchestrate normalize → dedup → credibility → novelty → confirmation."""

from __future__ import annotations

import structlog

from signals_lab.domain.intelligence import IntelligenceItem, RawIntelligenceRecord
from signals_lab.intelligence.credibility import apply_credibility_penalties, score_credibility
from signals_lab.intelligence.dedup import assign_dedup_keys, merge_confirmations, raw_to_items
from signals_lab.intelligence.novelty import score_novelty_batch

logger = structlog.get_logger(__name__)

_MULTI_SOURCE_MIN = 2


class IntelligencePipeline:
    """Pure processing pipeline for intelligence items (no I/O)."""

    def process(self, raw_records: list[RawIntelligenceRecord]) -> list[IntelligenceItem]:
        if not raw_records:
            return []

        items = raw_to_items(raw_records)
        items = assign_dedup_keys(items)
        items = merge_confirmations(items)

        scored: list[IntelligenceItem] = []
        for item in items:
            cred = score_credibility(item)
            updated = item.model_copy(update={"credibility_score": cred})
            updated = apply_credibility_penalties(updated)
            scored.append(updated)

        scored = score_novelty_batch(scored)

        logger.info(
            "intelligence_pipeline_complete",
            raw_count=len(raw_records),
            item_count=len(scored),
            multi_source=sum(1 for i in scored if i.cross_source_confirmation_count >= _MULTI_SOURCE_MIN),
        )
        return scored
