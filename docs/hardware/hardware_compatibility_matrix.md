# Hardware Compatibility Matrix

## Purpose

Track what has actually been tested, where it was tested, how it behaves under load, and what slow degradation looks like. A purchase listing or successful boot is not compatibility evidence.

## Required columns

| Field | Meaning |
|---|---|
| Part name | Exact board, sensor, adapter, actuator, or assembly |
| Interface type | USB, UART, CAN, I2C, SPI, GPIO, Ethernet, analog, audio, video |
| Driver status | native, packaged, custom, blocked, unknown |
| Tested OS | Exact distribution and release |
| Tested host | UP², Luckfox, ESP32, bench node, other |
| Supported features | Features proven in tests |
| Known limitations | Missing, unstable, or unsupported behavior |
| Test date | Date of the evidence |
| Receipt or document link | Stable test evidence |
| Operating sweet spot | Stable temperature and workload range, not merely maximum temperature |
| Condition signals | Vibration, contamination, current drift, packet errors, throttling, stale packets, frame loss, noise-floor shift |
| Power draw | Idle, normal, and peak where known |
| Heat behavior | Temperature rise, throttling, enclosure effect |
| Mounting notes | Orientation, strain relief, airflow, isolation |
| Replacement candidate | Known alternative or `none` |
| Consumable chemistry | Fluid or coolant type, material compatibility, disposal, leak plan |

## Initial evidence rows

| Part | Interface | Current posture | Host / OS | Notes |
|---|---|---|---|---|
| UP Squared Founder | SATA, USB, Ethernet, GPIO | verified development host | UP² / Ubuntu 20.04 | Runtime and interface boot proven; long-term AGL target remains separate |
| Luckfox Lyra Ultra nodes | Ethernet / PoE split | planned specialist nodes | Linux | capability manifests and role-specific testing still required |
| NEO-M9N GNSS | UART / USB adapter dependent | purchased, integration pending | UP² or specialist node | must publish standard sensor packets and stale timing |
| Roof microphone modules | audio interface dependent | received, integration pending | audio node / UP² | track noise floor, frame loss, gain drift, and mounting resonance |
| Advertised 20 TB USB stick | USB storage | unverified capacity | bench first | destructive capacity and sustained-write test required before trust |

## Rules

- Record failures and partial support, not only successful tests.
- Retesting creates new dated evidence rather than overwriting history.
- Vehicle suitability is separate from bench compatibility.
- Thermal stability, packet quality, current draw, and mounting serviceability are first-class evidence.
- Consumables and fluids require chemistry, disposal, and leak plans before promotion.
