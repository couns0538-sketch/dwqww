---
name: forge-bitexact-speed-lane
description: Use when asked for node-identical (bit-exact) NPS or speed patches for the Forge chess engine on a published lock, for an ALL-ON speed bundle, or for a handoff to Engine QA's quiet ABBA, while gates, self-play and training are live on grok-pc and only a few CPU cores are yours.
---

# Forge bit-exact speed lane

## Overview

A bit-exact speed patch is a claim about every input the engine can reach. Prove it in layers, cheapest first; time it last; never call your own timing the ABBA.

Status: written from one job (fable2, 2026-11-10). Not pressure-tested with baseline agents (that job allowed one reviewer only). Treat as a reference until tested.

## Order of work

1. Freeze by hash: lock exe, source snapshot, compiler, PGO workload. Rebuild the untouched source as a control and compare **byte ranges** with the lock.
2. Duplicate check before any code, and again every time a candidate joins the pool.
3. Profile for exact call counts (`llvm-profdata show` on the lock's own PGO profile) and self time; rank candidates by counted work, not by intuition.
4. Per candidate: switch default 0, lock text verbatim under `#else`, a test-only `=2` verify mode where old and new can be compared in place. Mutant first, then the patch.
5. Identity ladder, then the bundle, then INDICATIVE timing. Hand QA patches, packs and a protocol; QA times and locks.

## Quick reference

Tools: branch `fable52-speed-lane-20261109`, `fable_speed_lane/tools/` and `tests/`.

| Step | Tool |
|---|---|
| Pin every process (Idle, own cores) | `pin.ps1`, `pinguard.py`, `env.ps1` |
| Lock-recipe build, receipt | `spd_build.ps1` |
| Switch-0 exe vs lock | `bytecmp.py` |
| Pins, cold rows, warm, soak, perft, A/B | `spd_uci.py` |
| Differential harness, targeted positions, mutants | `tests/prim_dump.cpp`, `tests/targeted_fens.txt`, `tests/mutants.ps1` |
| One candidate, one stage | `cand_step.ps1`, `qualify.ps1` |
| Whole ladder, restartable | `qualify_all.ps1` |
| Bundle from singles, two apply orders | `make_bundle.ps1` |
| Patch = work tree = build source | `check_consistency.ps1` |
| Exact work counters per build | `work_counters.py` (reads each build's PGO profile) |
| Evidence tables, QA packs, manifest | `collect_evidence.py`, `make_packs.ps1`, `make_files_md.py` |

## Which skill, connector or tool for which step

| Need | Use | Note |
|---|---|---|
| Plan and rulings before any write | superpowers:brainstorming, plan mode | get the novelty and byte-identity rulings approved |
| Pinning, dedupe method | forge-search-gap-dossier | its tools are reused |
| Each patch | superpowers:test-driven-development | the mutant is the failing test |
| Any abort or identity difference | superpowers:systematic-debugging | find the position and move first |
| Before any PASS claim | superpowers:verification-before-completion | read the log line, not memory |
| Review | one read-only subagent on another model (AGENTS.md) | Read tool only; a subagent's shell is unpinned |
| PC state | forge-uci `pc_status` | its bench, perft and pin tools run on CPUs 0-1: do not use them in a 3-6 lane |
| Compiler and linker facts | Context7 or web search | no project details in queries |

## Common mistakes

| Mistake | Fix |
|---|---|
| Promising sha256 identity of a switch-0 build | The exe embeds a PDB hash and path. Report differing byte ranges: debug record only = code and data identical, sha UNRESOLVED |
| Trusting the core-lane file | Measure each lane CPU with the lock exe at Idle; a running gate keeps its old mask until it restarts |
| Duplicate search run once | Re-run it when the pool changes, with a mechanism pattern per candidate, and read commit messages: a built-before commit was found only on the re-run |
| A shortcut that is exact "for legal moves only" | Remove the precondition instead of documenting it (leave the odd case, here king moves, on the lock path). Then let the harness play every generated move, legal or not, and compare with a direct computation |
| Code added in a branch the lock configuration never compiles | It is untested by construction. Take it out and refuse the other configuration with `#error` |
| Mutant "not caught" on a sample | Rare events (checkmate, stalemate with a pinned pawn, double check) need a position aimed at them: keep a targeted FEN file, one position per branch |
| Mutant verdict without a control | Run the unchanged tree with the same switches first; count only a transcript difference, a reported self-check or a verify abort as CAUGHT, any other exit as ERROR |
| Changing a patch after results exist | Set aside every result of the changed source and of anything built from it (bundles), rerun; never carry a result over |
| Only noisy timing to show a gain | Read the exact PGO counters of each build's instrumented stage (`work_counters.py`): calls removed per fixed workload, load-independent |
| PowerShell parameter named `$out`, `$t`, `$j` | Names are case-insensitive: it hides the global from `env.ps1` inside that function |
| `"$id: text"`, `'a' + $x + 'b', 'c'` in PowerShell | Use `${id}`; the comma binds tighter than `+` |
| Killing your own long run | Not allowed here. Let the chain end through its done-list, then restart; finished steps are skipped |
| Reading single-CPU Idle timings as results | Block ratios swing by several percent. Report wall and CPU-cycle ratios, A/A first, label INDICATIVE |
| Timing singles only | One switch moves PGO and ThinLTO layout; time the bundle as one exe |
