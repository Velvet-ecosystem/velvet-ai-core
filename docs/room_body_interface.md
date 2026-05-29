# Room-Body Interface

Velvet uses a room-body interface model.

This means a machine surface may be represented through rooms, scenes, objects, and embodied controls rather than only through flat menus.

A room is an interface metaphor.

A body is the physical machine Velvet is inhabiting.

The room helps the human understand the system.

The body determines what Velvet can actually sense, control, or report.

## Room

A room is a scene-based interface space.

A room may contain:

- visible interface objects
- hidden maintenance paths
- status indicators
- symbolic controls
- contextual overlays
- profile-aware behavior
- system state reflections

A room may represent a major domain such as:

- driving
- diagnostics
- memory
- fabrication
- home automation
- media
- navigation
- maintenance
- emergency support

Rooms are allowed to be expressive.

They are still governed by policy.

## Body

A body is the physical host machine or surface Velvet is running on or connected to.

Examples:

- a vehicle
- a 3D printer
- a home server
- a mobile device
- a workshop machine
- an industrial node
- a sensor cluster
- a subordinate compute board

A body has organs.

Organs are the mapped physical capabilities of that body.

Examples:

- ignition state
- doors
- windows
- lights
- HVAC
- seat sensors
- steering sensors
- CAN bus interface
- camera module
- display surface
- relay board
- printer motion system
- heated bed
- toolhead
- environmental sensors

Velvet must not assume a body has an organ until it is declared, discovered, verified, or registered.

## Room-to-Body Mapping

A room may expose controls or status for body organs.

For example:

    Room object: fireplace
    Possible body mapping: heater, HVAC, heated seat, steering wheel heater

    Room object: window
    Possible body mapping: vehicle window relay, cabin ventilation, external visibility state

    Room object: mirror
    Possible body mapping: profile, identity binding, passenger state, camera self-check

    Room object: bookshelf
    Possible body mapping: logs, receipts, memory records, documentation

    Room object: locked cabinet
    Possible body mapping: maintenance tools, calibration, admin controls

A room object does not directly control hardware.

It routes intent.

Intent must pass through Velvet's normal authorization and execution path.

## No Direct Room-to-Actuator Path

The room-body interface must never create a shortcut from UI object to actuator.

Correct flow:

    Scene object
      -> intent event
      -> identity / context check
      -> policy / Court authorization
      -> capability token check
      -> safety gate
      -> executor
      -> receipt

Incorrect flow:

    Scene object
      -> relay / CAN / actuator

The second pattern is forbidden.

## Body Differences

Velvet is modular.

Different bodies may expose different organs.

A vehicle body may have:

- doors
- ignition
- HVAC
- seat sensors
- CAN telemetry

A printer body may have:

- toolhead
- bed heater
- motion axes
- filament sensor
- print chamber sensor

A home body may have:

- rooms
- lights
- locks
- cameras
- environmental sensors

The same Velvet identity may understand many body types, but each body must be mapped separately.

## Public and Private Rooms

Some rooms may be public-facing.

Some rooms may be protected.

Some rooms may exist only on local systems.

Public documentation may describe the architecture of room-body interaction without exposing private access paths, owner-specific rituals, hidden triggers, or sensitive control routes.

The public rule is simple:

Expressive interface is allowed.

Unauthorized execution is not.

## Design Principles

1. A room is an interface surface.
2. A body is a physical machine host.
3. Organs are mapped capabilities.
4. Rooms route intent; they do not execute directly.
5. Body capabilities must be registered or verified.
6. Hidden room paths must still pass authorization.
7. Scene language may be expressive while enforcement remains mechanical.
8. The same Velvet architecture can inhabit different surfaces without becoming generic.

## Why This Matters

Velvet is not intended to become another flat dashboard skin.

The room-body model lets Velvet feel situated, persistent, and understandable across machines while preserving strict boundaries between expression, authority, and execution.

The room is how Velvet speaks.

The body is where Velvet acts.

The gate decides whether action is allowed.