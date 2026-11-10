---
name: forge-search-gap-dossier
description: Use when asked to find a missing search mechanism for the Forge chess engine, to write an ideas-only spec or research dossier, or to decide whether a search idea is already built, queued, gated, rejected or listed, while gates, self-play and NNUE training are live on grok-pc and the engine source must stay unchanged.
---

# Forge search-gap dossier

## Overview

Freeze by hash, dedupe by what the code does, measure before you spec. "NO QUALIFIED GAP" is a valid result; a winner picked to fill the slot is not.

Status: written from one job (fable52, 2026-11-09). Not pressure-tested with baseline agents, because that job allowed no extra agents. Treat as a reference until tested.

## Quick reference

| Step | Do | Tool (branch `fable52-search-gap-20261109`, `fable_search_gap/tools/`) |
|---|---|---|
| Pin every run | CPU cores and Idle priority set on the launcher, children inherit | `pin.ps1`, `pinguard.py`; test with `whoami_pin.py` |
| Freeze the lock | hash exe and source, re-run bench and perft pins yourself | `uci_probe.py pins` |
| Find the real source | match files by git blob id across all branches | `tree_index.py` |
| Clone safely | blob-less clone, then fetch only text blobs | `fetch_corpus.py` |
| Dedupe | keyword AND code-shape search over the corpus, then diff live candidates | corpus + `git diff --no-index` |
| Read failures | verdict classes, repeats, NOT CLEAN rows, terminations | `gate_table_summary.py`, `gate_log_miner.py` |
| Measure a candidate without touching the engine | separate harness linking unmodified lock sources; count on the identical tree first | `etc_probe/` |

## Order of work

1. Read the crew's own inventories before the lock source: `opus_deepres/notes/RANKING_FINAL.md`, `opus_deepres/notes/T04F/DIFF.md`, `opus_r15/cands/INDEX.md`, `FORGE_RESULTS.csv`.
2. A row the crew listed and dropped is not new. Only something absent from notes, branches, gates, receipts and live candidate folders is.
3. For a survivor, get a number from Forge code before writing a spec.
4. Write the strongest case against, and reject criteria, before the proposal.

## Common mistakes

| Mistake | Fix |
|---|---|
| Trusting the `tree` field of `CURRENT_LOCK.json` | Hash `search.cpp`; the pointer can name an older tree |
| "The lock lacks it, so it is new" | Options live on job branches; search all of them |
| Full clone | The repo is several GiB; check free space on D: first |
| Calling `forge-uci` bench or perft | They run on CPU 0-1; use the pinned launcher on your own cores |
| Looking for gate PGNs | Mirrored gate folders keep logs only; many logs are pruned |
| Judging a search change by node ratio on a few positions | Single positions swing 0.2x to 2x. Count on the identical tree, add an A/A timing run, use 90+ positions |
| Piping object ids to `git` from Python text mode on Windows | Send bytes with `\n`; a `\r` makes an invalid refspec |
| Compiling with the installed clang and the MSVC library | Use the compiler named in the lock's build receipt and check its hash |
| Reading a capped gate as a loss | Most rows are capped without a decision; a cap is no decision |
