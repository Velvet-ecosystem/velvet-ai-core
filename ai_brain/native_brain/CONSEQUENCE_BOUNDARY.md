# Native Brain Consequence Evaluation

Velvet must distinguish ordinary uncertainty from uncertainty where silence could be costly.

Sprint 8 adds an explicit `EvaluationProfile` containing:

- urgency
- potential consequence
- cost of dismissing a true condition
- cost of unnecessary escalation
- confidence
- evidence reasons

The profile is supplied separately from the event payload. A transported event cannot silently grade itself as urgent, severe, trusted, or authorized.

## Cost of being wrong

Two mistakes are considered separately:

1. dismissing a real condition
2. escalating a harmless condition

When the cost of dismissal is substantially higher, the Native Brain may recommend notification or governed escalation review. When the cost of a false alarm is higher, it may remain at observation.

Low confidence does not always mean silence. Low confidence paired with serious potential consequence may justify a cautious notification because uncertainty itself is part of the evidence posture.

## Allowed

- derive importance deterministically from urgency and consequence
- preserve both false-negative and false-positive costs in the receipt
- recommend observe, notify, or escalate
- explain which bounded rule produced the recommendation
- preserve conservative defaults when no profile is supplied

## Forbidden

- accepting urgency or authority from arbitrary event payload fields
- treating owner presence as automatic permission
- publishing commands or selecting hardware executors
- converting an escalation recommendation into Court approval
- hiding the cost of false alarms
- claiming execution because consequence is severe

## Authority boundary

A severe consequence can raise the recommendation. It cannot grant permission.

Runtime and Court remain the authority path. Capability-bound organs execute only after authorization and applicable physical-presence gates.

> Caution may raise the lantern. It does not move the vehicle.
