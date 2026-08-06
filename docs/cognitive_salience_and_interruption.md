# Cognitive Salience and Interruption

Status: Gate 4 implementation contract

Velvet continuously evaluates whether new evidence deserves to interrupt the current cognitive event.

This layer redirects cognitive attention. It does not authorize safeing, select an executor, touch hardware, retry an action, or replace source evidence.

## Purpose

The current-event workspace may be observing, proposing, tracking an externally authorized action, or supporting language generation when more important evidence arrives.

Examples include:

- collision-like acceleration
- driver-unresponsive evidence
- seizure indicators
- impact or distress audio
- thermal, smoke, or electrical anomalies
- sudden CAN faults
- loss of a critical organ during action tracking
- authority-context changes
- resource failure

The salience path must remain active regardless of whether the language organ is speaking, waiting, unavailable, or overloaded.

## Flow

```text
trusted observation or organ signal
  -> validated SalienceSignal
  -> bounded score contribution
  -> candidate accumulation and decay
  -> threshold comparison
  -> cognitive.interrupt.candidate
  -> cognitive.interrupt.accepted when threshold is met
  -> accepted evidence joins current-event workspace
  -> interruption boundary proposed
  -> any safeing request begins separately through Runtime and Court
```

The accumulator does not close a physical control loop.

## Signal Contract

A salience signal declares:

```yaml
signal_id: sig-impact-1
interrupt_key: possible-impact
cognitive_event_id: cog-driving
source: imu
body_id: tiburon
node_id: up2-founder
reason: collision-like acceleration
observed_at: 100.0
monotonic_time: 50.0
severity: 0.95
rate_of_change: 0.90
novelty: 0.80
confidence: 0.99
source_trust: 0.99
persistence: 0.40
cross_sensor_agreement: 0.75
safety_critical: true
requires_immediate_safeing: true
source_refs:
  - obs-imu-1
correlation_ids:
  - drive-1
```

All ratio fields are bounded from `0.0` to `1.0`.

Signals are immutable and reject commands, capability tokens, executor handles, hardware targets, policy overrides, safeing claims, retry requests, and authority-bearing nested fields.

## Workspace Binding

Every signal is evaluated against a validated open `CognitiveWorkspaceContext`.

The signal, workspace, and accumulator must agree on:

- body
- node
- cognitive event
- replay posture
- correlation where both sides declare correlation identifiers

Stale, wrong-body, wrong-node, replay-mismatched, and unrelated signals are not accumulated.

An interrupt key already associated with another cognitive event cannot silently migrate into the new event.

## Scoring

The initial deterministic scoring model combines:

- severity
- rate of change
- novelty
- confidence
- source trust
- persistence
- cross-sensor agreement
- authority-context change
- resource failure
- safety-critical posture
- immediate-safeing relevance

The score is intentionally inspectable. It is not a learned black box.

Default thresholds:

```text
ordinary candidate: 0.85
safety-critical candidate: 0.65
```

Thresholds are configuration, not authority.

## Accumulation and Decay

One moderate signal may remain below threshold. Repeated, persistent evidence may accumulate until it crosses.

Older accumulated evidence decays according to elapsed monotonic time. This prevents a scattering of ancient weak signals from eventually assembling themselves into a fresh emergency.

The record preserves:

- instantaneous priority
- accumulated score
- threshold
- contributing signal references
- contributing source identities
- source and correlation references
- outstanding physical-effect references
- last update time

## Low Novelty Versus Persistent Risk

Low-priority novelty should not interrupt ordinary work.

Persistent moderate risk may cross threshold after repeated corroborating evidence.

A high-confidence safety-critical signal may cross the lower critical threshold immediately.

These are cognitive-attention decisions only.

## Rate and Capacity Limits

A valid organ may become noisy or greedy without publishing malformed data.

The accumulator therefore limits:

- total active candidates
- signals retained per candidate
- signals accepted from one source for one candidate

A source that floods one candidate is rate-limited rather than allowed to manufacture priority through repetition.

Duplicate signal identifiers are idempotent.

An accepted interrupt cannot be accepted repeatedly.

## Candidate Event

Every accepted signal contribution emits a candidate record:

```yaml
event_type: cognitive.interrupt.candidate
interrupt_id: interrupt-1
priority: 0.58
accumulated_score: 0.58
threshold: 0.85
requires_immediate_safeing: false
safe_state_reached: unknown
safeing_authorized: false
safeing_performed: false
```

A candidate does not claim that the current event was interrupted.

## Accepted Event

When accumulated score meets threshold, an accepted record is emitted:

```yaml
event_type: cognitive.interrupt.accepted
interrupt_id: interrupt-1
interrupted_event_id: cog-driving
priority: 0.96
accumulated_score: 0.96
threshold: 0.65
requires_immediate_safeing: true
safe_state_reached: unknown
safeing_authorized: false
safeing_performed: false
```

The accepted event preserves the candidate as its parent emission.

`requires_immediate_safeing` states that a separate authority path may be urgently required. It is not permission and does not claim safeing occurred.

## Workspace Application

`apply_accepted_interrupt()` may:

1. convert the accepted interrupt into immutable workspace evidence
2. associate it with the current event using the `INTERRUPTING` role
3. preserve the interrupt reference
4. propose an `INTERRUPTION` boundary recommending `INTERRUPTED`

It does not automatically perform safeing and does not invoke Runtime.

The caller may later close the cognitive event through the normal recorded boundary process.

Any physical safeing request must begin separately:

```text
accepted cognitive interrupt
  -> bounded safeing proposal
  -> Runtime identity and context verification
  -> Court policy
  -> safety gate
  -> approved executor
  -> outcome receipt
```

## Outstanding Effects

An interrupt arriving during action tracking may name outstanding effects such as:

- actuator state unknown
- steering command lifecycle unresolved
- door motor still moving
- resource lease still held
- audio warning still active

These references remain attached to the interruption record. They cannot be erased merely because attention moved elsewhere.

## Language Independence

The salience accumulator imports no language model, conversation scheduler, voice generator, or persona component.

Language may describe an accepted interruption after the fact, but language generation is not in the critical evaluation path.

A long response, blocked model, or unavailable voice organ must not prevent candidate accumulation or accepted-interrupt emission.

## Replay

The accumulator supports:

- `live`
- `fixture`
- `replay`

Signal, workspace, and accumulator replay postures must match.

Fixture and replay interrupts cannot become live physical authority.

## Tests

The initial test pack proves:

- low novelty does not interrupt
- persistent moderate risk crosses threshold
- critical evidence can cross immediately
- duplicate signals are idempotent
- stale and unrelated evidence is rejected
- wrong body and wrong node remain distinct
- replay posture must match
- nested authority and safeing smuggling is rejected
- one-source flooding is rate-limited
- accepted interrupts cannot be accepted twice
- candidate and accepted emission order is preserved
- read-only records are immutable
- an accepted interrupt becomes workspace evidence
- the workspace receives an interruption-boundary proposal
- a non-accepted candidate cannot interrupt the workspace

## Scope Boundary

This gate does not add:

- automatic physical safeing
- emergency authority policy
- Court logic
- executor selection
- language-generated priority
- learned salience weights
- episode consolidation
- memory promotion
- online plasticity

## Core Law

> Salience may demand attention. Attention may form a proposal. Neither is permission to move the body.
