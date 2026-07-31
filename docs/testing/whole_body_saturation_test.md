# Whole-Body Saturation Test

## Purpose

Benchmark Velvet as one living distributed body under pressure, not as isolated services that each look impressive in an empty room.

## Services to run together

- camera capture or simulated camera load
- CAN observation or replay
- receipt appends
- voice capture and recognition
- interface rendering
- storage writes
- health monitoring
- network-node heartbeat
- simulated GNSS
- simulated seat and presence sensors

## Required measurements

- missed deadlines
- dropped events
- receipt delay
- stale sensor packets
- CPU load
- memory pressure
- disk latency and throughput
- temperature
- clock throttling
- degraded services
- recovery behavior

`velvet.core.saturation` supplies dependency-free sample and threshold contracts. It names every threshold breach rather than compressing a run into one opaque score.

## Pass law

A run is not evidence unless it contains at least one sample. Default acceptance requires:

- no dropped events
- no stale packets
- no throttling
- no undeclared degraded service
- CPU, memory, receipt delay, disk latency, and temperature within the declared thresholds

Vehicle and hardware profiles may set stricter thresholds. Looser thresholds require a documented reason and new receipt set.

## Recovery phase

After overload is removed, the test must continue long enough to prove:

- paused workloads remain paused until policy permits restart
- degraded services recover deliberately
- receipt delay returns to normal
- stale evidence is not revived as current
- no duplicate launcher or recovery storm appears
- authority posture remains unchanged

## Evidence

Archive the workload profile, code revision, node manifests, thresholds, time-series metrics, failure injections, recovery observations, and final report receipt.
