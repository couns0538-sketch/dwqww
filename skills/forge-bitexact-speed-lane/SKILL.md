---
name: forge-bitexact-speed-lane
description: Use when asked for node-identical (bit-exact) NPS or speed patches for the Forge chess engine on a published lock, for an ALL-ON speed bundle, or for a handoff to Engine QA's quiet ABBA, while gates, self-play and training are live on grok-pc and only a few CPU cores are yours. Also when an A/B timing of two engine exes looks stable but disagrees with a repeat, or a patch that removes work times slower.
---

# Forge bit-exact speed lane

## Overview

A bit-exact speed patch is a claim about every input the engine can reach. Prove it in layers, cheapest first; time it last; never call your own timing the ABBA. Removed work is not gained time until a timing that cannot be fooled by the exe file says so.

Status: written from one job (fable2, 2026-11-10). Not pressure-tested with baseline agents (that job allowed one reviewer only). Treat as a reference until tested.

## Order of work

1. Freeze by hash: lock exe, source snapshot, compiler, PGO workload. Rebuild the untouched source as a control and compare **byte ranges** with the lock.
2. Duplicate check before any code, and again every time a candidate joins the pool.
3. Profile for exact call counts (`llvm-profdata show` on the lock's own PGO profile) and self time; rank candidates by counted work, not by intuition.
4. Per candidate: switch default 0, lock text verbatim under `#else`, a test-only `=2` verify mode where old and new can be compared in place. Mutant first, then the patch.
5. Identity ladder, then the bundle, then INDICATIVE timing **with a new copy of the exe per arm**. Time the first candidate early: a timing surprise can change which bundle is worth qualifying.
6. Hand QA patches, packs and a protocol; QA times and locks.

## Quick reference

Tools: branch `fable52-speed-lane-20261109`, `fable_speed_lane/tools/` and `tests/`.

| Step | Tool |
|---|---|
| Pin every process (Idle, own cores) | `pin.ps1`, `pinguard.py`, `env.ps1` |
| Lock-recipe build, receipt | `spd_build.ps1` |
| Switch-0 exe vs lock | `bytecmp.py` |
| Pins, cold rows, warm, soak, perft, A/B | `spd_uci.py` |
| Differential harness, targeted positions, mutants | `tests/prim_dump.cpp`, `tests/targeted_fens.txt`, `tests/mutants.ps1` |
| One candidate, one stage | `cand_step.ps1`, `qualify.ps1` (`-Nets on` or `off` for one cold run) |
| Whole ladder, restartable | `qualify_all.ps1` |
| Bundle from singles, two apply orders | `make_bundle.ps1` |
| Patch = work tree = build source | `check_consistency.ps1` |
| Exact work counters per build | `work_counters.py` (reads each build's PGO profile) |
| A/B with a new exe copy per arm, alternating order | `timing2.ps1` (`spd_uci.py abba --recopy DIR --alternate`) |
| Does one exe run alike from two files? | `file_effect.py`, `abba_spread.py` |
| Cycles per position, any Hash size | `pos_cycles.py` (`bench` ignores the Hash option) |
| Evidence tables, QA packs, manifest | `collect_evidence.py`, `make_packs.ps1`, `make_files_md.py` |

## Which skill, connector or tool for which step

| Need | Use | Note |
|---|---|---|
| Plan and rulings before any write | superpowers:brainstorming, plan mode | get the novelty and byte-identity rulings approved |
| Pinning, dedupe method | forge-search-gap-dossier | its tools are reused |
| Each patch | superpowers:test-driven-development | the mutant is the failing test |
| Any abort, identity difference or timing that contradicts a repeat | superpowers:systematic-debugging | state one hypothesis, test it, drop it when the test says no |
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
| Timing two fixed exe files | At times an exe file carries its own offset of several percent while it stays loaded (byte-identical copies up to 6 % apart; one pair read -3.65 % over 30 tight blocks, then +0.30 % two hours later). Copy the exe anew for every arm, alternate A B B A with B A A B, take 40 or more blocks, and run lock against lock the same way as the null |
| A tight spread read as a true result | Tight block ratios say the two files behaved the same from launch to launch. They do not exclude an offset that belongs to the file |
| Lock against lock with one file as the calibration | It cannot see a per-file offset. Use two copies |
| Counting removed work as gained time | Work between the TT prefetch and the probe runs while the entry is fetched. A patch that removes it, or moves it behind the probe, can time slower on a loaded machine even though every counter went down. Time each single with the copy-per-arm method before building on it |
| Varying `Hash` with `bench` | `bench` builds its own 16 MB table and clears it per position. Use `go` (`pos_cycles.py`) |
| Reading single-CPU Idle timings as results | Report CPU-cycle ratios with the null next to them, label INDICATIVE |
| Timing singles only, or bundles only | One switch moves PGO and ThinLTO layout, so time the bundle as one exe; but a bundle hides which switch costs, so time the singles too |
| A queue of many small starts behind a disk guard | When free space falls towards the floor, start the long single-process runs first (each cold run, each timing run is one start); a run that has started finishes, a queue of builds does not |
| A guard refusal recorded as FAIL | Make the launcher write "NOT STARTED" where the caller reports from, and show it as not run |
| Deleting a search base to free disk | Save the compact result first (here: the blob lookup of the lock's files); regenerate if it was not |
| PowerShell parameter named `$out`, `$t`, `$j` | Names are case-insensitive: it hides the global from `env.ps1` inside that function |
| `"$id: text"`, `'a' + $x + 'b', 'c'` in PowerShell | Use `${id}`; the comma binds tighter than `+` |
| A function that prints a line and returns an object | Both go to the caller's variable; print with `Write-Host` or return only the object |
| Killing your own long run | Not allowed here. Let a chain end through its done-list (write the ids of the steps to skip, and say so in its log), then restart; finished steps are skipped |
