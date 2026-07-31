# Dependency and Supply-Chain Policy

## Purpose

Velvet must not import poison because a person or coding tool sounded confident. Dependencies are executable trust decisions and require provenance, purpose, review, isolation, and receipts.

## Required dependency record

- canonical project name
- pinned repository or package source
- owner or maintainer
- exact reason it exists
- importing module or workstream
- version or commit pin
- license
- network behavior
- file, shell, hardware, and secret access
- update method
- rollback method
- review date
- approval receipt

## Rules

- Verify a project exists before adding it.
- Prefer official repositories and primary documentation.
- Never auto-execute fetched code during discovery.
- Pin URLs, versions, or commits where practical.
- Keep AI-generated dependency suggestions behind human review.
- Isolate Module Lab dependencies from promoted runtime dependencies.
- Review install scripts, workflow files, native extensions, and post-install hooks.
- Remove dependencies whose purpose is no longer documented.
- Do not grant secrets or hardware access merely because a package requires them.

## HalluSquatting

AI coding tools may invent plausible package, module, repository, or maintainer names. Attackers may register those hallucinated names later.

Therefore:

- never install a dependency directly from an AI suggestion
- verify spelling, ownership, release history, documentation, and community use
- compare the package source with the project named in primary documentation
- treat a newly registered near-match as hostile until proven otherwise

## Promotion law

```text
suggested dependency
  -> existence and source verification
  -> license and behavior review
  -> isolated Module Lab test
  -> deterministic tests and receipts
  -> explicit promotion decision
```

A passing import test is not sufficient evidence. Network, filesystem, shell, hardware, secrets, updates, and failure behavior must be understood.
