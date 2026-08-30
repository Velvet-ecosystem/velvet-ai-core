# Vehicle Encounter Recognition Policy

## Purpose

Velvet may need to recognize that a nearby vehicle appears to be the same physical vehicle seen moments earlier. The primary reason is safety, especially emergency-service awareness. Ordinary-vehicle continuity is a secondary situational-awareness feature and must not become persistent tracking.

This policy applies to passive recognition from local sensing such as vision, radar, audio, motion, lighting, or other bounded observations. Cooperative V2V/V2X communication is governed separately by the Communications layer.

## Priority Order

1. **Emergency-service safety recognition**
2. **Immediate ordinary-traffic continuity**
3. No general-purpose vehicle tracking mission

Emergency recognition may support warnings such as an approaching ambulance, fire apparatus, police vehicle, roadside-response unit, or other clearly identified emergency/safety vehicle.

Ordinary recognition exists only for immediate context such as a vehicle pacing, merging around, reappearing nearby, or remaining relevant to the current driving scene.

## Privacy Laws

Passive vehicle recognition must remain local and bounded.

It must not by default:

- build persistent dossiers of ordinary vehicles;
- infer or research a vehicle owner's identity;
- perform external identity enrichment;
- use a license plate as a persistent cross-session identity key;
- retain passive encounter identity across driving sessions;
- create cross-day travel histories for non-cooperative vehicles;
- promote appearance similarity into certainty;
- treat recognition as authority or permission.

A plate may be perceived incidentally by a sensor, but the passive recognition layer must not use it as a persistent identity key under this policy.

## Retention Classes

### Emergency service

- maximum passive recognition continuity: **6 hours**;
- intended scope: same-trip safety continuity;
- priority: high;
- cross-session linking: prohibited by default;
- persistent identifier creation: prohibited;
- external enrichment: prohibited.

The longer window exists so Velvet can reason that an emergency vehicle encountered earlier in the current trip may be the same responder seen again. It is not permission to create a long-term responder-vehicle registry.

### Ordinary vehicle

- maximum passive recognition continuity: **15 minutes**;
- intended scope: immediate traffic context only;
- priority: low;
- cross-session linking: prohibited;
- persistent identifier creation: prohibited;
- external enrichment: prohibited.

The record should decay or disappear when the vehicle is no longer relevant to the immediate scene.

## Evidence and Confidence

Recognition should be probabilistic. A result should be represented as something like:

> same vehicle candidate, confidence 0.82

not:

> this is definitely vehicle X

Emergency-service classification should prefer multiple independent cues where available, for example:

- authenticated cooperative V2X emergency status;
- visible emergency lighting pattern;
- vehicle class/livery or responder markings;
- siren/audio evidence;
- trajectory and closing behavior;
- local map/road context.

No single weak cue should silently become a high-confidence emergency classification.

## Ownership Boundary

- Sensors and perception components produce observations.
- AI Core may combine those observations into a bounded encounter belief.
- `velvet-event-protocol` carries observations/beliefs as information.
- Runtime/Court remain responsible for consequential action or control.
- `velvet-communications` owns cooperative V2V/V2X delivery and peer transport, not passive visual tracking.
- Receipts may preserve consequential safety evidence, but receipts do not create a permanent vehicle-tracking database.

## Emergency Interaction

Emergency recognition may raise safety salience and propose actions such as:

- warn Mister;
- prepare to yield;
- reduce conflicting nonessential behavior;
- surface direction/approach context;
- preserve a bounded safety receipt when appropriate.

Recognition alone never directly actuates steering, braking, throttle, locks, or other physical controls.

## Design Law

**Emergency recognition serves safety. Ordinary recognition serves only the immediate scene. Neither becomes a surveillance mission.**
