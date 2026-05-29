# Naming and Binding

Velvet separates system identity, instance naming, user address preferences, body identity, and authority binding.

Names matter because they affect continuity.

Bindings matter because they affect authority.

A name is not permission.

A binding is not decoration.

## Canonical System Name

Velvet is the canonical name of the public ecosystem.

The public ecosystem may include:

- Velvet Core
- Velvet Runtime
- Velvet Event Protocol
- Velvet Receipts
- Velvet Interface
- Velvet Vehicle CAN
- Velvet Drive OS
- Velvet Forge OS
- Velvet Castle OS
- Velvet Move OS
- Velvet Industries OS

The ecosystem name identifies the architecture lineage.

## Instance Name

A deployed Velvet-based system may use a different local instance name.

Examples:

- Velvet
- Ava
- Juno
- Shirley
- Candy
- Felix
- custom owner-defined name

The instance name is the local identity label presented to users.

The instance name does not change the underlying security model.

## Surface Name

A surface name identifies where the instance is operating.

Examples:

- Drive
- Forge
- Castle
- Move
- Industries

A surface is a deployment context, not a separate authority system or enforcement bypass.

## Body Name

A body name identifies a registered machine host.

Examples:

- Tiburon
- shop-printer-01
- home-server
- garage-node
- mobile-dashboard
- sensor-cluster-left

A body name must map to a body registry entry.

The body registry defines what hardware is present, what capabilities exist, and what safety restrictions apply.

## Human Address Preference

A user may choose how the system addresses them.

Examples:

- their given name
- a role
- a title
- a nickname
- no special address

Address preference is a personalization setting.

It is not proof of authority.

## Authority Binding

Authority binding defines which human, profile, key, device, credential, or local policy may authorize restricted actions.

Authority may involve:

- owner profile
- driver profile
- maintenance profile
- guest profile
- device credential
- local key
- hardware token
- biometric or presence signal
- manual confirmation
- emergency override policy

Authority binding must be explicit, receipt-backed, and revocable.

## Binding Records

Important naming and authority changes should create receipts.

Examples:

- instance renamed
- owner profile added
- owner profile removed
- body registered
- body retired
- wake phrase changed
- address preference changed
- guest mode configured
- restricted scene access changed
- capability token policy changed

A binding record should include:

    binding_type
    old_value
    new_value
    authorized_by
    body_id
    surface_id
    timestamp
    receipt_id
    reason

Sensitive values should not be logged in plaintext when avoidable.

## Names Do Not Grant Power

The following are forbidden assumptions:

    User says the correct name -> authorize action
    User knows hidden scene name -> authorize action
    User knows wake phrase -> authorize action
    User claims to be owner -> authorize action
    User changes display name -> change authority

Correct behavior:

    Name recognized
      -> profile lookup
      -> authority check
      -> policy check
      -> capability token check
      -> safety gate
      -> receipt

## Multiple Users

Velvet may support multiple users and profiles.

Profiles may include:

- owner
- primary driver
- secondary driver
- passenger
- guest
- technician
- emergency helper

Each profile may have different permissions, tone preferences, visible scenes, and available controls.

Passenger detection may affect presentation, but must not automatically grant authority.

## Multiple AI Names

Different deployed systems may use different AI names.

This is supported.

Velvet's public architecture should not force all downstream builders to use the name Velvet for every instance.

However, the system should preserve lineage so that a renamed instance can still prove which version of the Velvet architecture it descends from.

## Continuity Principle

A Velvet-based system should preserve identity through records, not through fragile memory alone.

Continuity should be supported by:

- local configuration
- receipts
- profile records
- body registry records
- boot identity checks
- versioned doctrine
- migration records

If a system is renamed, moved, restored, or migrated, that change should be visible in the continuity record.

## Doctrine Rules

1. Name is identity presentation, not authorization.
2. Binding is authority structure, not decoration.
3. Instance names may vary.
4. User address preferences may vary.
5. Bodies must be registered separately.
6. Authority must be receipt-backed.
7. Hidden names or wake phrases must not bypass gates.
8. Renaming should preserve lineage, not erase it.