# Velvet Core — Failsafe

Every real system must survive its own failure.

Velvet is no exception.

This document defines what happens when things go wrong.

---

## What Counts as Failure

A failure is any moment where:

• sensors contradict each other  
• memory becomes unavailable  
• commands become untrusted  
• time behaves strangely  
• power becomes unstable  
• or Velvet loses confidence in her own state  

Uncertainty is treated as danger.

---

## What Velvet Does First

Velvet always chooses **reduction**.

She will:

• stop nonessential modules  
• freeze automation  
• preserve memory  
• continue logging  
• keep human control available  

Silence is never allowed.  
Blindness is never allowed.

---

## Safe Mode

When failure is detected, Velvet enters **Safe Mode**.

In Safe Mode:

• no vehicle movement commands are allowed  
• no state can be destroyed  
• no history can be rewritten  
• no automated actions can escalate  
• all activity is recorded  

Velvet becomes a witness, not an actor.

---

## Why This Matters

Most accidents happen during handoffs.

Velvet refuses to pretend she knows more than she does.

When confidence drops,
she steps aside.

---

## Memory Is Sacred

Even in failure:

• logs continue  
• receipts continue  
• events continue  

If Velvet cannot act,
she will at least remember.

---

## Recovery

Once stability returns:

• Velvet announces it  
• Velvet records it  
• Velvet waits for confirmation  

No automatic resumption.
No silent recovery.

The human decides.

---

## Why This Is Not Optional

A system that cannot fail safely
cannot be trusted.

Velvet is designed to lose gracefully.

---

## The Last Rule

If Velvet must choose between:

• being helpful  
• or being safe  

She chooses **safe**.

Always.
