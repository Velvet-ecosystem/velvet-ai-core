# Standard Sensor Packet Schema

## Purpose

Every physical or simulated sensor publishes the same immutable packet shape before its observation enters Event Protocol. GPS, microphones, LD2410, CAN-derived signals, cameras, seat sensors, radar, voltage monitors, and future hardware must not invent private envelope formats.

The packet carries evidence and provenance only. It cannot grant capability, select an executor, or authorize physical action.

## Contract

Implemented by `velvet.core.schemas.SensorPacket`.

Required fields:

- `module_id`
- `node_id`
- `owning_handmaiden`
- `timestamp`
- `monotonic_time`
- `sensor_type`
- `interface_type`
- `health_state`
- `confidence`
- `payload`
- `receipt_id`
- `source_clock`
- `stale_after_ms`
- `calibration_version`

Optional fields:

- `degraded_reason`
- `raw_reference`

Health states are `ONLINE`, `DEGRADED`, `FAILED`, `RECOVERING`, `RECOVERED`, and `UNKNOWN`.

`confidence` is bounded from 0.0 through 1.0. `stale_after_ms` must be positive. Wall-clock time records chronology; monotonic time determines local freshness so clock changes do not make old evidence look new.

## Event and receipt path

`SensorPacket.to_event_protocol()` creates a `SENSOR_PACKET_OBSERVED` record. Hardware and simulation must pass that record through the same Event Protocol normalization, reasoning, health, receipt, and authority boundaries.

The packet receipt identifies the evidence record. It is not an execution receipt and does not imply trust beyond its declared health, confidence, calibration, and freshness.

## Rules

- Unknown calibration is explicit, never silently assumed.
- Raw references point to local evidence; large raw media stays outside the event payload.
- Stale packets remain available for provenance but must not be treated as current evidence.
- Simulated packets must retain their simulated origin at the adapter or Event Protocol metadata layer.
- Payload fields may not carry authority-bearing keys such as executor names, capability tokens, shell commands, or hardware targets.
