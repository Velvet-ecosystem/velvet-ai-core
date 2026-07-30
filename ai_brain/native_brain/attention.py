"""Doctrine of Silence attention arbitration for completed decision receipts."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from .models import (
    AttentionDecision,
    AttentionDisposition,
    AttentionProfile,
    DecisionReceipt,
    Importance,
    Recommendation,
    Urgency,
)


@dataclass(frozen=True)
class AttentionArbiter:
    """Decide whether a receipt should remain quiet, wait, surface, or interrupt.

    The result is an append-only attention recommendation. This class does not
    deliver a notification, grant authority, publish commands, or execute work.
    """

    def decide(
        self,
        receipt: DecisionReceipt,
        profile: AttentionProfile | None = None,
    ) -> AttentionDecision:
        active = profile or AttentionProfile()
        evaluation = receipt.judgment.evaluation
        recommendation = receipt.recommendation

        critical_attention = (
            recommendation is Recommendation.ESCALATE
            or evaluation.importance is Importance.CRITICAL
            or evaluation.urgency is Urgency.IMMEDIATE
        )

        if critical_attention:
            disposition = AttentionDisposition.INTERRUPT
            rationale = (
                "Critical importance, immediate urgency, or governed escalation "
                "requires immediate attention even during ordinary quiet modes; "
                "attention is not authority."
            )
        elif recommendation is Recommendation.NOTIFY:
            defer_reasons: list[str] = []
            if active.repeated_notice:
                defer_reasons.append("the notice repeats a recent finding")
            if active.quiet_mode:
                defer_reasons.append("quiet mode is active")
            if active.focus_protected:
                defer_reasons.append("the current focus is protected")
            if not active.audience_available:
                defer_reasons.append("no intended audience is currently available")

            if defer_reasons:
                disposition = AttentionDisposition.DEFER
                rationale = (
                    "Notification should wait because "
                    + ", ".join(defer_reasons)
                    + "; the receipt remains visible and may be reconsidered later."
                )
            else:
                disposition = AttentionDisposition.PRESENT
                rationale = (
                    "The receipt recommends notification and no bounded silence "
                    "condition requires deferral."
                )
        else:
            disposition = AttentionDisposition.SILENT
            rationale = (
                "Observe and ignore recommendations remain quiet while their receipt "
                "is preserved for continuity and review."
            )

        return AttentionDecision(
            attention_id=str(uuid4()),
            receipt_id=receipt.receipt_id,
            disposition=disposition,
            rationale=rationale,
        )
