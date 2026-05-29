# Retrofit Body Registry

Velvet is designed for modular retrofit deployment.

A body is a physical host machine that Velvet can observe, assist, or control through registered capabilities.

The Retrofit Body Registry defines what machine Velvet is connected to, what organs exist, what each organ can do, and what safety restrictions apply.

Velvet must not assume hardware exists simply because a scene, module, or profile references it.

## Body

A body is a registered physical machine or host surface.

Examples:

- vehicle
- 3D printer
- home system
- mobile device
- industrial machine
- sensor node
- subordinate compute node

Each body should have a stable body identifier.

Example:

    body_id: tiburon_v0
    body_type: vehicle
    surface: drive
    status: active

## Organ

An organ is a mapped body capability.

Examples for a vehicle body:

- ignition_state
- door_locks
- windows
- hvac
- seats
- seat_heaters
- steering_sensor
- brake_sensor
- can_interface
- lighting
- camera_front
- camera_rear
- gnss_primary
- gnss_secondary

Examples for a printer body:

- x_axis
- y_axis
- z_axis
- extruder
- hotend
- bed_heater
- chamber_sensor
- filament_sensor
- camera
- emergency_stop

Examples for a home body:

- room_lights
- door_lock
- thermostat
- camera
- motion_sensor
- server_node
- local_storage

## Registry Entry

A body registry entry should include:

    body_id
    body_type
    surface
    display_name
    owner_profile
    hardware_profile
    organs
    safety_profile
    authority_profile
    receipt_policy
    created_at
    updated_at

Each organ should include:

    organ_id
    organ_type
    status
    interface_type
    read_capability
    write_capability
    safety_class
    executor_module
    requires_authorization
    requires_confirmation
    receipt_required
    degraded_behavior

## Read Capability vs Write Capability

Velvet must distinguish between reading and acting.

Reading sensor data is not the same as controlling hardware.

Example:

    seat_pressure_sensor:
      read_capability: true
      write_capability: false

    door_lock_relay:
      read_capability: optional
      write_capability: true

Write-capable organs require stricter enforcement.

## Safety Classes

Organs should be classified by safety risk.

Suggested classes:

    informational
    comfort
    visibility
    access
    mobility
    actuation
    critical
    emergency

Examples:

    outside_temperature: informational
    seat_heater: comfort
    headlights: visibility
    door_locks: access
    cruise_assist: mobility
    brake_servo: critical
    emergency_stop: emergency

Higher-risk classes require stronger authorization, confirmation, validation, and receipt rules.

## Discovery Does Not Equal Trust

Velvet may support hardware discovery.

However:

    discovered != trusted
    detected != authorized
    connected != registered
    reachable != permitted

A newly discovered device must be verified and registered before it becomes a trusted body organ.

Discovery may create a candidate record.

Registration creates a trusted body record.

## Candidate Device Flow

Recommended flow:

    Device detected
      -> candidate record created
      -> interface classified
      -> read-only validation
      -> safety class proposed
      -> human or policy review
      -> body registry update
      -> receipt recorded
      -> capability token policy assigned

A candidate device should default to no actuation.

## Body Migration

A Velvet instance may move between bodies or support multiple bodies.

Migration must preserve:

- identity lineage
- body registry history
- active body selection
- retired body records
- safety restrictions
- authority bindings
- receipts

A body being removed or retired should not erase its historical receipts.

## Retrofit Principle

Velvet is not limited to factory-installed systems.

A retrofit body may include:

- stock controls
- aftermarket modules
- custom relay boards
- sensor pads
- CAN adapters
- local compute boards
- external displays
- handmade harnesses
- subordinate nodes

Retrofit flexibility does not remove the need for safe mapping.

The more custom the body, the more important the registry becomes.

## Doctrine Rules

1. A body is a registered physical host.
2. Organs are mapped capabilities.
3. Discovery does not equal trust.
4. Read capability and write capability must be separate.
5. Write-capable organs require authorization.
6. Safety class determines enforcement level.
7. Candidate devices default to no actuation.
8. Registry changes require receipts.
9. Retrofitted systems must be explicit, not assumed.
10. Velvet may be modular without becoming careless.