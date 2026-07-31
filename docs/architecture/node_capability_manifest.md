# Node Capability Manifest

## Purpose

Every physical compute or microcontroller node carries a durable passport describing what it is, what it can host, what it must never do, who owns its role, and how it fails.

Implemented by `velvet.core.schemas.NodeCapabilityManifest`.

## Required content

- node identity and display name
- hardware model and operating system
- compute, memory, and storage limits
- network interfaces
- attached sensors
- controlled outputs
- allowed capabilities
- forbidden capabilities
- owning handmaiden
- fallback owner
- heartbeat interval
- update method
- emitted receipt types
- failure behavior
- safe shutdown behavior

Allowed and forbidden capability sets may not overlap. Capability absence means not permitted; the manifest is an allowlist, not a wish list.

## Example posture

The UP² may host Runtime, Court-facing coordination, UI, and local cognition while physical write authority remains disabled unless an approved executor is registered and governed.

A Velour node may append receipts and index archives but forbid vehicle control.

An ESP32 seat node may publish presence and health packets but own no shell, network-routing, or actuator capability.

## Rules

- Hardware capacity is descriptive, not authority.
- Capability advertisements must stay within the manifest.
- Updates follow the node's declared method; Velvet's current doctrine is physical-presence approval, not unattended OTA.
- Heartbeat loss triggers health degradation and fallback evaluation, not silent rebinding.
- Safe shutdown removes capability before power disappears whenever possible.
