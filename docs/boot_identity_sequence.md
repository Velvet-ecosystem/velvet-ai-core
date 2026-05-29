# Boot Identity Sequence

Velvet must establish identity before action.

The boot identity sequence verifies what system is waking, which body it is attached to, which surface is active, which profile context applies, and what capabilities are allowed.

Boot is not just startup.

Boot is identity re-entry.

## Purpose

The boot identity sequence protects against:

- wrong body assumptions
- stale hardware mappings
- unauthorized profile activation
- corrupted configuration
- unsafe actuator availability
- missing receipt ledger state
- degraded sensor state
- accidental direct-control paths
- identity drift after restore or migration

Velvet should know where she is before she acts.

## Recommended Boot Flow

1. Load local configuration
2. Verify system version and doctrine version
3. Verify receipt ledger availability
4. Load instance identity
5. Load surface identity
6. Load active body registry
7. Verify body fingerprint
8. Load profile bindings
9. Establish current user/session context
10. Check hardware organ availability
11. Classify degraded or missing organs
12. Load capability token policy
13. Start event bus / safe publish layer
14. Start modules in observe-only mode
15. Enable authorized interactions
16. Record boot receipt

## Identity Layers

Boot should distinguish:

    system_lineage
    instance_identity
    surface_identity
    body_identity
    profile_identity
    session_identity
    capability_context

These layers should not be collapsed into one value.

For example:

    system_lineage: Velvet ecosystem
    instance_identity: local AI instance name
    surface_identity: Drive
    body_identity: tiburon_v0
    profile_identity: primary_owner
    session_identity: current verified session
    capability_context: drive_surface_owner_present

## Observe-Only First

Modules should start in observe-only mode unless explicitly authorized otherwise.

Observe-only means modules may:

- read safe configuration
- subscribe to allowed events
- report presence
- report degraded state
- emit non-actuating status events

Observe-only modules may not:

- actuate hardware
- send CAN control frames
- trigger relays
- change bindings
- alter safety policy
- bypass gatekeeping
- assume owner presence

## Body Fingerprint

A body fingerprint helps confirm that the expected machine is present.

A vehicle fingerprint may include:

- body_id
- known CAN identifiers
- known sensor set
- GNSS module identity
- local compute identifier
- registered relay board identifiers
- display identity
- storage identity
- configured hardware profile

A printer fingerprint may include:

- controller board identifier
- bed size
- motion profile
- toolhead identity
- firmware signature
- known sensors

Fingerprint mismatch should trigger degraded or protected mode, not blind execution.

## Degraded Boot

If boot verification fails, Velvet should degrade safely.

Examples:

    receipt ledger unavailable -> block protected actions
    body fingerprint mismatch -> observe-only mode
    critical organ missing -> disable related executors
    profile unresolved -> guest or locked mode
    capability policy missing -> deny write actions
    sensor conflict -> require review

Failure should be visible, recorded, and recoverable.

## Boot Receipt

A boot receipt should record:

    receipt_type: boot_identity
    system_version
    doctrine_version
    instance_id
    surface_id
    body_id
    body_fingerprint_status
    active_profile_context
    available_organs
    degraded_organs
    blocked_capabilities
    ledger_status
    timestamp
    previous_hash
    hash

Boot receipts help prove continuity across restarts, migrations, restores, and hardware changes.

## Startup Identity Presentation

Velvet may present a startup identity screen or scene.

This may include:

- instance name
- surface name
- active body
- boot status
- degraded mode warning
- owner/profile state
- safe greeting
- visual scene load

The startup presentation should never imply that restricted capabilities are available before the gate has authorized them.

## Forbidden Boot Patterns

The following are forbidden:

    Start executors before identity verification
    Assume body from last run without checking
    Enable write-capable modules before policy load
    Treat wake phrase as authority
    Treat passenger presence as owner identity
    Ignore missing receipt ledger
    Silently continue after body mismatch
    Skip degraded state receipts

## Doctrine Rules

1. Velvet establishes identity before action.
2. Boot begins in safe verification mode.
3. Modules start observe-only unless authorized.
4. Body fingerprint mismatch must degrade safely.
5. Missing policy means deny write actions.
6. Missing receipts mean protected actions are blocked.
7. Startup scenes are presentation, not authorization.
8. Boot should create a receipt.
9. Identity layers must remain separate.
10. Velvet should wake carefully before she moves.