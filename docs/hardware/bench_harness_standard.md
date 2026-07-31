# Bench Harness Standard

## Purpose

Every hardware organ must be testable, observable, and safely power-cycled on the bench before vehicle installation. Bring-up should be repeatable engineering, not ritual magic with loose wires and selective memory.

## Required bench features

- known, keyed power connector
- documented voltage range and polarity
- fuse or current limit
- UART header
- CAN access where applicable
- I2C or SPI breakout where applicable
- status LED with documented meaning
- reset control
- labeled test points
- expected boot log
- safe default output state
- mount orientation and airflow note
- strain relief
- receipt and log capture method

## Harness record

Each harness receives:

- harness ID
- target module IDs
- connector pinout revision
- maximum current
- fuse value
- supply type
- communication adapters
- safe power-up sequence
- safe shutdown sequence
- known hazards
- evidence receipt location

## Safe defaults

Outputs remain de-energized until a governed test explicitly requests otherwise. Relay, motor, light, heater, and actuator lines must not twitch during boot, reset, cable insertion, software crash, or debugger attachment.

Vehicle-facing plugs should be mechanically impossible to confuse with bench-only power where practical.

## Test sequence

1. visual and continuity inspection
2. current-limited power-up
3. capture boot log
4. verify default output state
5. verify sensor packet and health-event emission
6. inject malformed and stale input
7. test disconnect and recovery
8. verify safe shutdown
9. archive logs, measurements, photos, firmware hash, and receipts

A bench pass proves bench behavior only. Vehicle permission remains a separate interface-contract and authority decision.
