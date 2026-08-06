# Cognitive Operational Modulators and Social Turn-Taking

Status: Gate 5 implementation contract

Velvet may adjust attention, conversational timing, silence, and presentation according to bounded operational state.

These mechanisms do not alter identity, authentication, Court policy, capabilities, safety gates, executor selection, or receipt requirements.

## Purpose

The Cognitive Event Layer now knows:

- what appears to be happening
- what outcome is expected
- whether reality agreed
- whether higher-priority evidence interrupted the event
- how a closed event may become an evidence-linked episode proposal

This gate adds two behavioural coordination mechanisms:

1. bounded operational modulators
2. embodied social turn-taking

The goal is not to simulate hormones or claim human emotion. The goal is to let several bounded mechanisms respond consistently to changing context without gaining authority.

## Operational Modulators

The initial set is:

```text
arousal
novelty
uncertainty
urgency
social_engagement
resource_pressure
prediction_stability
```

These are engineering variables, not biological substances and not evidence of consciousness.

## Baselines, Rate Limits, and Decay

Each modulator declares:

- a baseline
- an allowed source set
- a maximum rate of change
- a decay rate toward baseline
- permitted consumers
- forbidden consumers

A single update cannot jerk every variable from calm to maximum without respecting its rate limit. Old temporary state decays instead of remaining permanently dramatic.

`prediction_stability` decays toward a healthy baseline of `1.0`. The other initial modulators decay toward `0.0`.

## Source Allowlisting

Updates are accepted only from named bounded sources.

Examples:

- prediction systems may update uncertainty and prediction stability
- salience may update arousal, novelty, and urgency
- presence and turn-taking may update social engagement
- Runtime resource reporting may update resource pressure
- sensor-health observations may update uncertainty

An unrelated component cannot update a variable merely because it knows the field name.

Every update is bound to:

- one cognitive event
- one body
- one node
- one replay posture
- source and correlation references

Duplicate update identifiers are idempotent.

## Trust Context

`trust_context` is not inferred from mood, memory, or conversational familiarity.

It may be set only from a `velvet-runtime` source reference and uses bounded states such as:

```text
owner_verified
guest_verified
maintenance
unknown
disputed
```

Trust context may shape presentation. It does not itself authenticate anyone or grant privilege.

## Consumer Allowlisting

Consumers receive only the variables they are permitted to use.

Initial permitted consumers include:

- `turn-taking`
- `interface`
- `logging`
- `learning-observer`

Explicitly forbidden consumers include:

- Court
- authentication
- capabilities
- executors
- safety gates
- receipt writers

A modulator snapshot declares:

```yaml
cannot_change_authority: true
authority: none
grants_authority: false
grants_execution: false
grants_actuation: false
```

## Modulator Snapshot Event

A consumer-specific snapshot may be transported as:

```text
cognitive.modulators.snapshotted
```

The snapshot preserves:

- cognitive event
- body and node
- source and correlation references
- replay posture
- trust context
- consumer name
- only the allowlisted values for that consumer

The snapshot is interpretation-only and non-canonical.

## Social Turn-Taking

Social participation is treated as embodied event coordination rather than alternating text messages.

Initial postures are:

```text
LISTEN
HOLD_SILENCE
ACKNOWLEDGE
RESPOND
YIELD
INTERRUPT_FOR_SAFETY
RECOVER_TURN
```

A posture shapes speaking timing and presentation only. It is not authority.

## Listening and Yielding

When Mister is speaking, Velvet listens.

If Mister begins speaking while Velvet is already speaking, Velvet yields rather than fighting for the audio channel.

An incomplete utterance estimate extends the silence window, allowing Mister to finish rather than rewarding every pause with a verbal ambush.

## Silence as a Deliberate Posture

Silence is not a missing response.

Velvet may hold silence when:

- an explicit silence request is active
- no present conversation partner is established
- the owner is speaking
- the utterance appears incomplete
- the pause remains inside the bounded turn-hold window
- driving demand makes nonessential speech inappropriate

Uncertainty may lengthen the hold window. Social engagement may shorten it slightly. Neither can remove the minimum pause.

## Driving Demand

High driving demand suppresses nonessential speech.

If an explicit question is pending, Velvet may issue a brief acknowledgement instead of a long response. Ready responses receive a bounded maximum speaking duration that shrinks as driving demand or urgency rises.

This affects presentation, not physical driving authority.

## Safety Interruption

Urgency, arousal, or a high `safety_severity` value alone cannot produce the `INTERRUPT_FOR_SAFETY` posture.

That posture requires an explicit accepted-interrupt reference from the previously governed salience path.

```text
accepted cognitive interrupt
  -> safety-speaking posture
```

The posture may permit a short urgent warning. It does not authorize safeing, braking, steering, calling emergency services, or any other physical action.

When the accepted safety condition clears, the coordinator may enter `RECOVER_TURN` and return conversation carefully rather than pretending the interruption never happened.

## Proposal-Only Decisions

Every turn decision declares:

```yaml
proposal_only: true
authority_granted: false
```

The decision may describe:

- whether speech is appropriate
- whether Velvet should listen, yield, acknowledge, respond, or remain silent
- whether the posture is interrupting
- an accepted interrupt reference where required
- a bounded maximum response duration

It cannot select hardware, modify policy, or create an execution path.

## Replay

Workspace, modulator update, registry, and turn signals must share one replay posture:

- `live`
- `fixture`
- `replay`

Fixture and replay social behaviour cannot become fresh live authority.

## Tests

The initial test pack proves:

- allowed sources can update only their named modulators
- disallowed sources are rejected
- duplicate updates are idempotent
- later changes obey maximum rates
- values decay toward declared baselines
- wrong event and replay posture fail closed
- trust context must come from Runtime
- Court, authentication, executors, and safety gates cannot consume modulators
- consumer snapshots contain only allowlisted variables
- snapshot events remain non-authoritative
- read-only snapshots are immutable
- active owner speech produces listening
- Velvet yields when the owner begins speaking
- incomplete utterances and short pauses preserve silence
- explicit silence wins
- high driving demand suppresses nonessential responses
- pending questions receive bounded acknowledgements
- ready responses receive maximum durations
- urgency alone cannot manufacture a safety interruption
- accepted interrupt evidence is required for safety posture
- conversational turns can recover after safety clears
- absent partners do not receive unsolicited chatter
- wrong event and forbidden modulator input are rejected
- turn decisions remain immutable and proposal-only

## Scope Boundary

This gate does not add:

- emotional truth claims
- learned modulator weights
- online self-modification
- autonomous preference changes
- authentication
- Court decisions
- safety authority
- executor access
- physical action

Governed plasticity remains a later, separately reviewed boundary.

## Core Law

> Internal state may change how Velvet pays attention and speaks. It may never change what she is allowed to do.
