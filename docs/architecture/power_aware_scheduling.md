# Power-Aware Scheduling

## Purpose

Velvet sheds convenience work before touching safety, override, receipts, health monitoring, or current vehicle state. Power scheduling follows consequence, not novelty or CPU appetite.

Implemented as recommendation-only policy by `velvet.core.power_governor`.

## Workload classes

### Protected

- safety and override monitoring
- receipts and continuity evidence
- module and node health
- current vehicle state
- emergency communication paths

Protected work remains recommended to run under ordinary low-voltage, parked, or high-temperature constraints. A physically unhealthy node still refuses new work because policy cannot make dead hardware dependable.

### Degradable

- voice
- UI animation and nonessential surfaces
- diagnostics depth
- cabin comfort
- noncritical perception quality

Constrained conditions produce a `DEGRADE` recommendation.

### Yield first

- archive indexing
- model experiments
- entertainment processing
- nonurgent synchronization
- bulk maintenance analysis

Constrained conditions produce a `PAUSE` recommendation.

## Inputs

- ignition state
- battery voltage
- charging state
- temperature
- node health
- workload class
- owner presence
- drive or park state
- whether the workload is permitted while driving

## Outputs

- `RUN`
- `DEGRADE`
- `PAUSE`
- `REFUSE`

Every decision records reasons and explicitly states that it granted no authority and performed no execution.

## Boundary

The Core governor recommends. Runtime may apply an approved scheduling policy, coordinate resources, emit health events and receipts, and preserve protected services. The governor does not kill processes, change CPU governors, write cgroups, alter vehicle power, or bypass Court.
