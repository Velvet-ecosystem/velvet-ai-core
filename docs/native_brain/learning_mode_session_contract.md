# Learning Mode Session Contract

**Status:** Draft  
**Version:** 0.1.0  
**Classification:** Core architecture contract  
**Scope:** Native Brain and cognitive orchestration  
**Authority:** none

## Purpose

Learning Mode is the bounded orchestration layer that lets Velvet revisit unresolved evidence, compare what she already knows, reduce uncertainty, and prepare candidate understanding without silently changing authority, doctrine, identity, physical behavior, or trusted memory.

Learning Mode is not a second brain.

It does not replace the Native Brain, cognitive workspace, Dream State, memory lifecycle, Runtime distributed work, Persona Continuity admission, Event Protocol, Receipts, Court, or Continuity Spine.

Its job is to coordinate those existing systems into one finite study session.

## Core Law

> Learning Mode decides what deserves bounded study and coordinates the study. Existing cognitive systems still perform the thinking, evidence handling, placement, admission, and governance they already own.

A Learning Mode session must always remain explainable, interruptible, bounded by available resources, and unable to promote its own conclusions into authority.

## Historical Continuity

The older White Room, Learning Mode, Dream Layer, curiosity, self-LM, and related learning concepts are preserved as architectural lineage.

The modern implementation must recover their intent without recreating parallel stores, private buses, duplicate reasoning loops, or hidden authority paths.

The White Room is best represented by the existing bounded cognitive workspace machinery rather than a new `WhiteRoomEngine`.

Dream State already owns quiet-time eligibility and consolidation policy. Governed plasticity already defines bounded adaptation proposals and rollback-oriented promotion constraints. Curiosity already produces quiet watch, correlation, and question candidates. Learning Mode therefore sits above these systems as an orchestrator.

## Existing Components Reused

Learning Mode should reuse, not duplicate:

- `velvet/core/cognition/event_workspace.py` for bounded event-centered working context
- `velvet/core/cognition/workspace_context.py` for non-canonical workspace context
- `velvet/core/cognition/episode_consolidation.py` for bounded consolidation work
- `velvet/core/cognition/governed_plasticity.py` for evidence-gated adaptation proposals
- `velvet/core/cognition/prediction_outcomes.py` for prediction and expectation evidence
- `velvet/core/cognition/salience_interruption.py` for interruption and salience handling
- `velvet/core/native_brain/curiosity.py` for quiet uncertainty reduction and question candidates
- `velvet/core/native_brain/integrated_cycle.py` for finite Native Brain cognitive heartbeats
- `velvet/core/native_brain/distributed_body.py` for proposal-only workload suitability
- `velvet-runtime` distributed-work services for verified node placement, short-lived workload leases, handoff, degradation, and result return
- canonical AI Core memory lifecycle and association contracts for candidate evidence and links
- Persona Continuity admission and conflict handling for persona-facing memory promotion
- Velvet Event Protocol for shared lifecycle transport
- Velvet Receipts for durable evidence where required
- Continuity Spine and Runtime for verified identity/body/session context

No Learning Mode component should own a second copy of these responsibilities.

## Native Brain Family Boundary

AI Core currently contains two Native Brain code families:

- `ai_brain/native_brain/`
- `velvet/core/native_brain/`

The earlier family contains a decision spine, receipt reflection, and proposal-only learning contracts. The newer family contains the current curiosity, working-state, pattern, expectation, judgment, intent, distributed-body, and integrated-cycle architecture.

Until ownership and migration are explicitly resolved, Learning Mode must not cross-wire these families by importing from both in one runtime path.

For the first implementation:

- orchestration should target `velvet/core/native_brain/` and `velvet/core/cognition/`
- concepts from `ai_brain/native_brain/` may be reviewed as compatibility and lineage evidence
- useful older semantics should be migrated deliberately into the current family rather than creating a permanent dependency on both families
- existing tests for the earlier family must not be deleted merely because a newer family exists

This prevents Learning Mode from becoming an accidental compatibility bridge that freezes duplicate architecture forever.

## Ghost Boundary

Ghost is for fake-car specifications, synthetic vehicle behavior, replay fixtures, and simulated vehicle testing.

Ghost is not a general-purpose Learning Mode sandbox, worker framework, or cognitive execution environment.

Learning Mode may consume synthetic vehicle observations produced through Ghost during tests, exactly as it may consume other clearly marked simulated evidence. It must preserve that provenance and must never allow simulated evidence to masquerade as physical evidence.

Learning Mode must not:

- repurpose `GhostHandlerSpec` as the production learning-worker contract
- describe ordinary Library study, local-model inference, or memory reflection as Ghost work
- loosen Ghost's synthetic/read-only restrictions merely to make Learning Mode easier to run
- use Ghost terminology for non-vehicle cognitive maintenance

If Learning Mode later needs reviewed Library-backed or local-model worker handlers, those require their own explicit, bounded contract.

## Session Ownership

A Learning Session owns coordination only.

It may:

- select an unresolved subject or bounded study objective
- collect references to existing evidence
- open or associate existing cognitive workspaces
- request proposal-only Native Brain work
- request Runtime placement for bounded distributed work
- pause when safety, owner interaction, resource pressure, degraded health, or higher-priority work takes precedence
- collect bounded results and evidence references
- produce candidate explanations, candidate questions, candidate confidence revisions, and candidate memory/adaptation proposals
- close with an inspectable outcome

It may not:

- write trusted memory directly
- declare a candidate true
- change model weights directly
- change prompts, policy, thresholds, doctrine, identity, or authority directly
- grant Runtime placement to itself
- authorize speech, execution, or actuation
- select hardware executors
- open CAN writers, GPIO, relays, actuators, or other physical-control surfaces
- bypass Persona Continuity admission
- bypass memory lifecycle review
- create a private event bus
- create a second canonical evidence store

## Proposed Session Lifecycle

The first implementation should keep the lifecycle small and finite:

```text
PROPOSED
  -> ELIGIBILITY_CHECK
  -> OPEN
  -> STUDYING
  -> REVIEW_PENDING
  -> COMPLETED
```

A session may instead move to:

```text
PAUSED
ABORTED
INSUFFICIENT_EVIDENCE
DEGRADED
```

These are Learning Session lifecycle labels only. They do not replace Runtime execution state, memory lifecycle state, cognitive workspace state, Dream State, or node-health state.

Every session must either complete, pause with a reason, or terminate. It must not remain an invisible perpetual background process.

## Eligibility

Learning Mode may begin or continue only when explicit eligibility evidence permits it.

The first deterministic implementation may accept an injected eligibility decision from fixtures.

A later live policy bridge may consider:

- safety state
- emergency state
- owner requests and active interaction
- vehicle/body operating state
- available electrical power
- node health
- CPU, memory, storage, and thermal pressure
- higher-priority specialist work
- Dream State eligibility
- local model availability
- Library availability

No single signal such as `ignition_off` should be treated as sufficient proof that background learning is appropriate.

## Work Placement

Native Brain may describe bounded work and indicate suitable capabilities.

Runtime owns actual placement, node verification, workload leases, reassignment, degradation, and recovery.

Learning Mode therefore must not invent a second scheduler.

The intended chain is:

```text
Learning Session
  -> bounded study objective
  -> Native Brain proposal-only work description
  -> Runtime distributed-work placement
  -> verified specialist result
  -> Queen / Learning Session review
```

A Runtime workload lease is coordination only. It grants no Court authority and no physical execution permission.

## Resource Budgeting

Learning Mode needs explicit resource budgeting, but it must not misuse Runtime's execution-oriented exclusive Resource Coordinator merely to account for cognitive maintenance.

Initial implementations may use conservative local limits supplied to the session, for example:

- maximum session duration
- maximum work items
- maximum concurrent distributed tasks
- maximum local-model invocations
- maximum candidate outputs
- maximum evidence references

A future general maintenance-resource policy may become a shared Runtime service if multiple non-execution subsystems need it.

## Evidence Intake

Learning Mode works from references to evidence that already passed through its owning intake path.

Possible sources include:

- verified observations
- conversations and owner corrections
- receipts
- Library documents and knowledge packs
- historical memory records
- unresolved contradictions
- prediction errors
- repeated patterns
- specialist findings
- clearly marked simulated vehicle evidence

Learning Mode must preserve source type, provenance, freshness, confidence, and simulation status where available.

External web access is not part of this contract. If future Web Leash policy supplies downloaded evidence, that material enters through the normal evidence/library intake path before Learning Mode studies it.

## White Room Mapping

The historical White Room is a controlled learning environment, not an Internet sandbox.

Its modern mapping is:

```text
Learning Session
  -> one or more bounded cognitive workspaces
  -> existing Native Brain cognitive passes
  -> evidence comparison / contradiction / prediction review
  -> candidate understanding
```

The White Room name may remain as user-facing or architectural lineage terminology, but it must not become a duplicate persistence layer or parallel reasoning engine.

A White Room session may be entirely offline.

## Dream State Mapping

Dream State is a quiet-time policy and consolidation opportunity, not a synonym for Learning Mode.

Learning Mode may run some sessions during Dream State, while Dream State may also perform consolidation tasks that are not Learning Mode sessions.

Dream State can therefore be one eligibility source or operating context for Learning Mode without owning Learning Mode itself.

## Candidate Outputs

A Learning Session may finish with zero or more bounded candidates such as:

- explanation candidate
- unresolved-question candidate
- revalidation request
- association candidate
- confidence-revision candidate
- memory-admission candidate
- governed-plasticity candidate
- negative-learning candidate
- no-change conclusion

Every candidate must retain evidence references and must remain non-authoritative until its owning promotion path accepts it.

`no-change` is a valid and important Learning Session outcome.

## Memory Boundary

Learning Mode does not own canonical memory.

Candidate knowledge follows existing memory and persona admission rules.

The intended principle is:

```text
study result
  -> candidate evidence
  -> conflict/provenance review
  -> existing admission path
  -> existing memory lifecycle
  -> reviewed promotion when justified
```

There must be no `learning_memory` database or White Room truth store.

## Associations and Memory Veins

The current deterministic association/backlink layer is sufficient for v1 Learning Mode evidence linking.

A richer typed concept graph, multi-hop traversal, or explainable concept-path system may be added later, but Learning Mode must not build a private concept graph in the meantime.

## Event and Receipt Boundary

Learning Mode lifecycle should travel through Velvet Event Protocol rather than a private bus.

A future event family may include bounded lifecycle facts equivalent to:

- `LEARNING_SESSION_PROPOSED`
- `LEARNING_SESSION_OPENED`
- `LEARNING_TASK_PROPOSED`
- `LEARNING_TASK_COMPLETED`
- `LEARNING_SESSION_PAUSED`
- `LEARNING_SESSION_COMPLETED`
- `LEARNING_SESSION_ABORTED`

These events report what happened. They do not grant permission or create canonical memory.

Existing Runtime distributed-work lifecycle receipts must be reused rather than duplicated inside Learning Mode.

## Interruption and Safety

Learning Mode always loses to safety and critical body work.

A session must be pausable or abortable when:

- safety handling takes ownership
- an emergency begins
- the owner needs immediate interaction
- a node degrades or disconnects
- available power falls below policy
- resource pressure exceeds limits
- required evidence becomes invalid or stale
- continuity or body verification fails

Paused work must preserve enough evidence to explain why it stopped, but restart must not silently assume an old workload lease or stale execution context remains valid.

## Offline-First Requirement

Learning Mode must remain useful without Internet access.

Its core loop should be able to study:

- local memory
- local Library content
- local receipts
- local observations
- local model output when available
- local deterministic cognitive machinery

Cloud or web-derived evidence may be optional inputs, never a required foundation.

## v1 Implementation Target

The first implementation should be intentionally boring and auditable.

It should prove that a session can:

1. accept a bounded study objective and evidence references
2. reject or pause when explicit eligibility is false
3. open or associate existing cognitive workspace state
4. run a finite number of existing Native Brain/cognition operations
5. optionally submit proposal-only distributed work through Runtime
6. collect results without granting authority
7. produce non-canonical candidate outputs
8. terminate cleanly with a reason
9. preserve provenance and simulated-versus-physical distinctions
10. pass tests showing no direct memory promotion, network access, hardware access, execution authority, or actuation authority

No local-model training, autonomous code modification, web browsing, doctrine modification, or physical behavior change is required for v1.

## Open Architecture Questions

The following should be resolved before expanding beyond the v1 contract:

- final migration/ownership status of `ai_brain/native_brain/` versus `velvet/core/native_brain/`
- exact maintenance-resource budget owner
- exact Event Protocol schema names for Learning Session lifecycle
- exact receipt retention requirements for low-value versus important sessions
- reviewed handler contract for Library-backed and local-model distributed study
- live eligibility bridge from body power/health/runtime context into Dream State and Learning Mode
- richer concept-graph requirements beyond deterministic associations

These are integration questions, not permission to create duplicate subsystems.

## Final Principle

> Learning Mode does not make Velvet smarter by letting her change herself freely.
>
> It makes Velvet smarter by giving her a governed place to revisit evidence, discover better explanations, admit uncertainty, and earn better understanding over time.
