# Module Lab Promotion Gates

## Purpose

Module Lab is a safety gate, not merely a staging directory. A module may be offered for human promotion review only after every required gate passes and each result is linked to an evidence receipt.

Implemented by `velvet.core.module_promotion`.

## Required gates

- lifecycle behavior
- standard health-event emission
- receipt emission
- malformed-input handling
- authority-bypass resistance
- dependency-failure behavior
- stale-timestamp handling
- simulated-adapter coverage
- degraded-mode behavior
- safe shutdown

A missing result, missing receipt, or failed gate blocks promotion readiness.

Passing all gates does not promote the module automatically. Human review, CI, public/private boundary review, Runtime compatibility, and any vehicle-specific safety approval remain separate requirements.

## Initial fuzz targets

- CAN parsers
- UART packet handlers
- GNSS NMEA sentences
- seat JSON messages
- Event Protocol messages
- receipt payloads
- configuration files

## Evidence rules

Each gate stores a stable receipt identifier. Raw logs, captures, malformed samples, and hardware traces may be stored separately and referenced by that receipt.

Results are append-only. A repaired failure receives a new test result and receipt; the old failure remains part of the module's history.

## Promotion law

```text
Module Lab candidate
  -> all deterministic gates
  -> receipt set complete
  -> human promotion review eligible
  -> CI and boundary review
  -> explicit merge or promotion decision
```

No module may self-promote, rewrite its failed evidence, or claim readiness because its happy path worked once.
