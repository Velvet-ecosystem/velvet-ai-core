# Vehicle Interface Contract

## Purpose

Vehicle-specific hardware stays behind stable adapter boundaries so Velvet's shared reasoning, events, receipts, health, and authority laws do not fork for every car or truck.

Implemented by `velvet.core.schemas.VehicleInterfaceContract`.

## Required fields

- interface identity and purpose
- vehicle targets
- authority mode
- owning handmaiden
- physical interface
- data format
- update frequency
- command format when control-capable
- receipt type
- safe failure behavior
- adapter boundary
- simulation-adapter availability
- explicit allowed surfaces

Authority modes:

- `OBSERVATION_ONLY`
- `READ_ONLY`
- `GOVERNED_CONTROL`
- `BENCH_ONLY`

A governed-control interface must declare a command contract, but that declaration is not permission to execute.

## Initial interface inventory

Contracts should be created for:

- CAN
- GNSS
- audio
- lighting
- HVAC
- steering
- brake
- clutch
- throttle
- shifter
- seat sensors
- microphones
- cameras
- power and ignition state

Each contract must state whether it is permitted on the Tiburon, Western Star, Dakota, or bench only.

## Adapter law

```text
physical or simulated adapter
  -> standard sensor / health packet
  -> Event Protocol
  -> Runtime context and Court boundary
  -> approved executor only when authorized
  -> receipt
```

Core logic must not import a Tiburon, Western Star, Dakota, CAN-device, UART-device, relay-board, or actuator-specific implementation.

## Failure law

Read interfaces stop publishing current evidence and emit `STALE` or `FAILED`.

Control interfaces fail closed according to their documented mechanical and electrical safe state. Simulation mode may never unlock a physical actuator. Bench permission may never be promoted into vehicle permission by changing a UI flag.
