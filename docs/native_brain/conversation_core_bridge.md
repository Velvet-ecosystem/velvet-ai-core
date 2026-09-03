# Native Brain Conversation Core Bridge

Status: first grounded conversation integration boundary.

## Purpose

`velvet-language` now emits a normalized `velvet.language.conversation.turn` event for typed text and speech transcripts. Native Brain consumes that event through a read-only bridge so one conversation path can reach Core without creating a second chat engine or a hidden execution lane.

```text
keyboard / UI / Vosk
        |
        v
velvet-language
        |
        | velvet.language.conversation.turn
        v
conversation_ingress
        |
        +--> ObservationEnvelope (read only)
        |
        +--> grounded resolver supplied by trusted Core/body/memory integration
        |
        v
velvet.core.conversation.meaning
        |
        v
velvet-language realization
```

## Ownership

Core owns verified meaning, evidence relationships, reasoning, and bounded interpretation. Language owns human wording and conversational presentation. Runtime and Court own authorization and execution.

The bridge therefore returns structured meaning, not finished prose. A fact result may contain a fact identifier, scalar value, unit, confidence, qualifiers, and source references. Language decides how that meaning is expressed to the human.

## Authority Boundary

Conversation ingress is never an execution path.

- incoming turns must carry `authority_granted=false`
- action-like turns may preserve `requires_authority_check=true`
- Core meaning always carries `authority=none`
- Core meaning always carries `grants_authority=false`
- Core meaning always carries `grants_execution=false`
- Core meaning always carries `grants_actuation=false`
- Runtime remains required for any consequential action

A resolver cannot return arbitrary dictionaries. It must return `GroundedConversationMeaning`, whose constructor enforces the authority boundary and bounds fact values to scalar data.

## No Resolver Behaviour

When no trusted grounded resolver is connected, the bridge returns `response_kind=unavailable` with the qualifier `no-grounded-resolver`. It does not invent an answer and it does not ask an optional language model to manufacture one.

## Next Integration

The next layer should bind a resolver to verified body state, memory/context projections, and other trusted Core truth sources. The resulting `velvet.core.conversation.meaning` event can then be realized by `velvet-language` and carried to the Founder interface, terminal chat, or audio output without changing the underlying conversation contract.
