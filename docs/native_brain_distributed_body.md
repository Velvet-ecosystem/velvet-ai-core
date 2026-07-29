# Native Brain Distributed Body Foundation

## Foundation rule

Velvet's Native Brain must never assume that the Queen performs every task directly.

Velvet is one accountable body made from distributed organs:

- microcontrollers handle deterministic reflexes, timing, sensors, relays, and actuators;
- small specialist Linux nodes handle narrow work such as audio, security, logging, filtering, sensor fusion, and local pattern detection;
- larger Linux nodes handle heavier local cognition and related service groups;
- the Queen maintains whole-system awareness, reasoning, planning, authority context, and final coordination.

Hardware size does not determine importance. Suitability, timing, verified identity, health, and available capacity do.

> Velvet rejects the agent swarm. She is built as Unified-Organ AI: distributed specialties, shared concrete reality, dynamic workload cooperation, one authorization spine, and one accountable body.

## Native Brain and Runtime boundary

Native Brain may:

- describe bounded work requirements;
- understand verified node advertisements;
- identify suitable, fallback, partial, or unavailable organs;
- preserve why a node was included or excluded;
- maintain whole-body awareness of degradation;
- escalate important results to the Queen.

Native Brain may not:

- assign live work directly;
- create execution leases;
- transfer capability tokens;
- select an actuator path;
- bypass Runtime placement;
- bypass Court authorization;
- treat a workload proposal as authority.

The governing path is:

```text
Native Brain describes needed work
  -> verified organs advertise capability and condition
  -> Native Brain may form an authority-free placement proposal
  -> Runtime verifies current state and owns placement or handoff
  -> Court authorizes consequential work
  -> the selected organ performs its bounded contract
  -> Event Protocol carries state and results
  -> Receipts preserve what happened
  -> the Queen retains whole-body awareness
```

## Node advertisements

Every schedulable Linux node should advertise:

- verified node identity and organ name;
- body and continuity binding;
- node tier;
- capabilities;
- accepted and refused work classes;
- current load;
- health;
- availability;
- current and maximum concurrent tasks;
- overflow capability;
- fallback capabilities;
- temporary duty-absorption capabilities.

Availability is explicit:

```text
available
busy
saturated
degraded
draining
offline
quarantined
```

A microcontroller may be represented through a supervising Linux organ when it cannot advertise safely by itself. The proxy does not gain the microcontroller's actuation authority.

## Work requirements

A bounded work requirement declares:

- work identity and class;
- required and preferred capabilities;
- minimum health and maximum acceptable load;
- whether overflow, temporary absorption, partial results, Queen fallback, or observe-only fallback are permitted;
- whether the work is whole-system coordination, safety relevant, or consequential.

A work requirement is not an execution request. It carries no token, executor selection, hardware handle, or authority.

## Cooperation outcomes

A capable organ may be proposed as:

- `primary`: its normal bounded role;
- `overflow`: compatible fallback capacity;
- `temporary_absorption`: safe temporary coverage for another organ;
- `queen_fallback`: Queen coverage when permitted and no better specialist is available;
- `partial`: useful but incomplete replacement;
- `observe_only`: sensing remains available while stronger capability is unavailable.

Degradation is named rather than hidden:

```text
none
full_replacement
partial_replacement
observe_only
capability_unavailable
```

When one node fails, the planner reports the affected capability. It does not declare the complete body dead merely because one organ is absent.

## Queen reservation

For narrow work, a healthy specialist should normally rank ahead of the Queen. This protects the Queen's capacity for whole-system awareness and coordination.

For whole-system planning or final coordination, the Queen is the required organ.

The Queen may absorb narrow work as a fallback when policy permits, but this is explicitly marked as replacement behaviour rather than normal architecture.

## Refusal is healthy

A node may refuse or defer work because:

- its body or continuity binding is unverified;
- its health is below the work minimum;
- its load or task limit is exceeded;
- it is saturated, draining, offline, or quarantined;
- the work class is outside its accepted limits;
- the work requires a capability it does not possess.

A truthful refusal is healthier than silent overload or fabricated completion.

## Authority boundary

Load sharing never transfers authority implicitly.

A placement proposal always reports:

```text
requires_runtime_placement: true
authority: none
canonical: false
```

Consequential work additionally reports:

```text
requires_court_authorization: true
```

A substitute organ must independently satisfy body membership, capability compatibility, health, capacity, Runtime placement policy, safety gates, and Court requirements. Authority cannot hitchhike with a handoff.

## Determinism and future work

The first planner is deterministic and model-free. Identical requirements and advertisements produce identical ranked proposals.

This PR establishes the Native Brain contract only. Follow-on layers belong in:

1. `velvet-runtime`: verified node registry, live advertisements, leases, handoff, overflow, dead-owner recovery, and placement receipts;
2. `velvet-event-protocol`: node-health, work-offer, acceptance, refusal, handoff, completion, and degradation events;
3. `velvet-receipts` and Riven: placement evidence, temporary duty absorption, replacement, and continuity history.

Distributed cooperation is a foundation rule, not a later performance optimization.
