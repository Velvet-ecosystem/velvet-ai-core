# Body-relative resource capacity

## Principle

Velvet is not sized to one board model.

The current body is the verified topology that exists now: local compute, local memory, directly attached storage, and resources hosted by other trusted Velvet organs. A UP Squared Founder with a 1 TB attached drive is a different body-capacity state from the same Founder without that drive. Moving the drive to Velour changes the hosting organ, not Velvet's identity.

Hardware names are deployment facts, not reasoning policy.

## Capability versus resource

A capability answers what an organ can do, for example `library.retrieve`, `audio.filter`, or `vision.observe`.

A resource advertisement answers how much bounded capacity that organ currently exposes, for example:

- memory in bytes;
- storage in bytes;
- compute capacity in an explicitly declared unit;
- accelerator capacity in an explicitly declared unit.

These are intentionally separate. Founder may consume `library.retrieve` from Velour without claiming Velour's attached disk is physically local to Founder.

## Resource scopes

- `local`: inherent to the host, such as RAM or board-local eMMC;
- `attached`: directly attached to the host, such as SATA, NVMe, USB storage, or another local device;
- `body_shared`: explicitly exposed by that host as a body-shared resource.

Scope describes access posture. It does not grant authority.

## Current-body snapshots

Core may aggregate verified resource advertisements into a read-only `BodyCapacitySnapshot`. The snapshot is observational and non-canonical. It answers questions such as how much verified storage or memory the current body advertises now.

Only the newest verified advertisement from each node participates. Offline resources are ignored. Unverified or continuity-unverified resource advertisements do not contribute capacity.

## Placement

`ResourceAwareDistributedBodyPlanner` is a gate around the existing `DistributedBodyPlanner`, not a replacement planner.

For work with no resource requirements, behavior delegates unchanged to the existing planner.

For work that declares resource requirements, nodes that cannot satisfy those bounds are filtered before the existing health/load/capability planner ranks candidates.

This preserves the existing rules for:

- body and continuity verification;
- health and load;
- specialist preference;
- overflow and temporary absorption;
- Queen fallback;
- degradation posture;
- Runtime placement ownership;
- Court authorization for consequential work.

## Dynamic topology

Resource advertisements are expected to change during operation.

Examples:

```text
Founder + 1 TB USB drive
    -> Founder advertises attached storage

drive removed
    -> later Founder advertisement omits or marks that resource offline

drive attached to Velour
    -> Velour advertises the storage instead

Home server joins verified body
    -> server advertises its own memory/storage/compute resources
```

No board-specific rule needs to change.

## Resource units

This layer deliberately does not guess conversions between arbitrary units. A requirement and matching resource must use the same declared unit.

Initial deployment convention should use `bytes` for memory and storage. Compute and accelerator units must be explicit rather than inferred from product names.

## Identity and authority

More hardware permits more local work. It does not change Velvet's identity, truth rules, privacy rules, or authority.

Resource advertisements, capacity snapshots, and resource-aware placement proposals all remain authority-free.