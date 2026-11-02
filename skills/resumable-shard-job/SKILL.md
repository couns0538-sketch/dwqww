---
name: resumable-shard-job
description: Use when implementing or qualifying a restartable Forge training-data shard pipeline, validating checkpoints and per-shard hashes, or proving an interrupted owned job resumes to the same output bytes as an uninterrupted run.
---

# Resumable Shard Job

Preserve every source, completed shard and failed attempt. Reuse the existing converter/checkpoint implementation where suitable; add failure tests rather than another parallel pipeline. On grok-pc use `grok-pc-safe-run` and never terminate production, NPT, gates or another process.

## Define the immutable run

Record source order and full hashes/counts, tool/source/config hashes, seed, format, chunk/shard boundaries, decoder state, compression settings and output order. The same run must reproduce the same output bytes, not merely the same row count. Nondeterministic headers/timestamps, RNG state or unordered parallel output can invalidate MD5 identity.

Use new sealed outputs and append-only checkpoint generations. A checkpoint identifies the exact source offset/state, last fully committed shard, emitted row counts and that shard's SHA-256 and MD5. Publish data before its checkpoint with flush/fsync and an exclusive atomic publication primitive suitable for the actual filesystem. On Windows sync a writable descriptor. Keep interrupted staging files; never overwrite them as if they were complete.

Resume validates configuration, every committed shard hash and original source identity, acquires exclusive ownership, then continues from the last valid commit boundary. Refuse changed inputs/tools, corrupted shards, ambiguous orphan commits or simultaneous ownership. Keep disk capacity for old indexes/partials **plus** resumed work; check before each shard and during long index/output loops.

## Required interruption proof

First run the bundled disposable selftest as a harness check; see [the recipe](references.md). It starts and terminates only its newly created fixture child, preserves a partial next shard, resumes, and compares MD5 **and** SHA-256 against an uninterrupted run. This proves only that fixture.

Then repeat the same protocol on the **actual production adapter and formats**, using frozen copied test inputs in isolated new directories and an owned test worker. Inject interruption before publication, after shard publication/before checkpoint, and after checkpoint; test corrupted output, changed input and repeated resume. Never use a live worker or an arbitrary PID. Compare the exact final `.pos`, `.hce`, sidecars and every sealed output role, not a reserialized reconstruction. Differences are FAIL; unrun production replay is UNVERIFIED.

## Report

Return each shard's source SHA-256, output SHA-256/MD5, rows, checkpoint identity and completion status; preserve original commands, child exit/termination evidence and raw output. Report uninterrupted/resumed MD5s side by side, the exact fault-injection point and whether the real adapter was exercised. A successful fixture is not production qualification. Checkpoint and push only the authorized isolated work; no source deletion or live-trainer changes.
