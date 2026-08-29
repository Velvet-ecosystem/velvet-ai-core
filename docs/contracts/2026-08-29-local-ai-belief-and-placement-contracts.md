# Local AI belief and placement contracts

Date: 2026-08-29
Status: contract draft
Owner repo: velvet-ai-core

## Purpose

Velvet's AI layer should reason with uncertainty, request capabilities instead of vendor models, and treat compute placement as a runtime decision bounded by authority, latency, power, and evidence.

## 1. Belief State Layer

Velvet should preserve uncertainty before committing world facts.

Canonical path:

```text
observation -> candidate interpretations -> confidence -> corroboration -> committed state
```

Suggested fields:

```yaml
belief_id: string
source_observation_ids: [string]
candidate_interpretations:
  - label: string
    confidence: number
    supporting_evidence: [string]
    contradicting_evidence: [string]
committed: boolean
commit_threshold: number
commit_reason: string | null
requires_corroboration: boolean
expiry_time: string | null
```

Use cases:

- person presence
- object location
- vehicle faults
- medical observations
- environmental events
- sensor disagreement

Rule: Velvet may internally hold probable states without chiseling them into permanent truth too early.

## 2. Model Capability Adapter

Modules must depend on capabilities, not vendor model names.

Capability examples:

```text
reasoning-small
reasoning-large
vision-local
code-review
speech-transcription
speech-synthesis
memory-summarizer
safety-classifier
document-parser
local-embedding
```

Suggested fields:

```yaml
capability_name: string
preferred_provider: string
fallback_provider: string | null
offline_available: boolean
cloud_permission_required: boolean
max_authority_level: propose | advise | classify | none
data_retention_rule: string
receipt_required: boolean
refusal_behavior: string
```

Rule: no model provider gains physical authority by being selected.

## 3. Execution Placement Contract

The organ that decides does not have to be the silicon that sweats.

Execution placement values:

```text
local-required
local-preferred
handmaiden-eligible
movable
cloud-optional
cloud-forbidden
```

Suggested fields:

```yaml
capability_name: string
execution_location_policy: string
allowed_nodes: [string]
forbidden_nodes: [string]
data_may_leave_origin_node: boolean
max_latency_ms: integer | null
fallback_location: string | null
power_cost_class: low | medium | high | unknown
thermal_cost_class: low | medium | high | unknown
authority_changes_if_moved: boolean
```

Rule: authority remains with Court and runtime even when compute moves between Queen, a handmaiden, an accelerator, or a future vision box.

## 4. Inference Cost Receipt Requirements

AI work should be measurable.

Required receipt data:

```yaml
capability_requested: string
model_provider: string
model_name_or_local_id: string
execution_location: string
processor_class: cpu | gpu | npu | dsp | fpga | memory_side | unknown
input_units: integer | null
output_units: integer | null
cache_hit: boolean | null
runtime_ms: integer
estimated_energy_j: number | null
estimated_heat_class: low | medium | high | unknown
fallback_invoked: boolean
fallback_reason: string | null
larger_model_reason: string | null
result_confidence: number | null
```

## 5. Reflex Compute Contract

Safety-relevant perception needs a deterministic lane before high-level reasoning.

Canonical ladder:

```text
raw sensor -> deterministic reflex perception -> fused observation -> slower reasoning/world model
```

Suggested fields:

```yaml
reflex_path_id: string
sensor_sources: [string]
processor_location: string
max_latency_ms: integer
deterministic_status: deterministic | bounded_nondeterministic | nondeterministic
reserved_resources: [string]
fallback_behavior: string
high_level_ai_allowed_in_critical_path: boolean
observation_output: string
receipt_type: string
```

Rule: conversational AI, archive work, and large-model reasoning must not displace reflex perception.

## 6. Observation Latency Contract

Perception quality is not only FPS. Measure when truth becomes actionable.

Suggested timings:

```yaml
capture_timestamp: string
bridge_ingress_timestamp: string | null
preprocess_start_timestamp: string | null
inference_start_timestamp: string | null
inference_complete_timestamp: string | null
event_emitted_timestamp: string
actionable_observation_timestamp: string
end_to_end_latency_ms: integer
jitter_ms: integer | null
dropped_frame_correlation: string | null
```

## 7. Activation Ladder Contract

Always-on perception should escalate only when evidence earns it.

Stages:

```text
passive sensor -> ultra-low-power trigger -> deterministic reflex -> normal perception -> high-level reasoning
```

Suggested fields:

```yaml
ladder_id: string
current_stage: passive | trigger | reflex | normal | reasoning
wake_threshold: string
sleep_threshold: string
minimum_dwell_ms: integer
energy_mode: sentinel | normal | diagnostic
allowed_stage_jump: boolean
receipt_on_escalation: boolean
```

Use cases:

- parked sentry mode
- Home presence
- seat monitoring
- medical observation
- workshop-machine monitoring

## 8. Useful Work per Watt/GB Score

Future compute should be evaluated by validated work, not glamour.

Suggested score:

```text
validated workload throughput / electrical watts / memory footprint
```

Track:

```yaml
node_or_board: string
validated_workload: string
throughput_metric: string
sustained_watts: number
peak_watts: number
ram_required_mb: integer
idle_memory_mb: integer
thermal_throttling_observed: boolean
score_notes: string
```

## 9. Working World Representation

Separate raw evidence from the compact live world model.

```text
raw_world_evidence != working_world_representation
```

Rules:

- preserve raw evidence when safety, replay, or debugging demands it
- live reasoning may use compact derived geometry or summaries
- derived representations must link back to source observations
- discarded bulky intermediates must be intentional, not accidental

## Non-goals

- No cloud-first dependency.
- No direct physical authority for models.
- No model-specific architecture lock-in.
- No replacement of Court, Runtime, or receipts.
