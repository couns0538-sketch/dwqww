---
name: forge-relabel-job
description: Run, resume, check and cost a Forge NNUE relabel job with relabel2.py (Opus R14-B, branch opus-r14b-relabel) - self-play text (old selfplay_out files or R8 v5 shards) -> rows.tsv with game ids and a game-level validation split -> fixed-node labels from the R13 lock probe in resumable shards -> train.txt / val.txt / labels.tsv that Forge's fen2bin converts. Covers the commands, the input rules (finished files, name order, one job per dataset), exit codes, kill / resume behaviour, the 1M proof, how to measure rates next to crew load, and the pitfalls of 2026-11-02. Use for any relabel / rescore-with-search job, the 50M relabel, a resume after a stop, or a question about relabel2.py outputs.
---

# forge-relabel-job (Opus R14-B item 2; `opus_r14b/item2/` on `opus-r14b-relabel`)

## What it is
`relabel2.py` (own code, stdlib + python-chess via Astra's unchanged `astra/records.py`) relabels self-play positions with
the R13 probe `C:\o13\p5\forge_data_probe.exe` (sha256 ed76de96..., lock source d4f4312, 1 thread, Hash 1 MB, TT and
histories cleared per search: a label depends only on FEN + nodes + hash). It keeps the ORIGINAL FEN (castling, en
passant, clocks) and splits validation by game. UNPROVEN as training data: Engine NNUE decides. Details and evidence:
`RESULTS.md`, `RELABEL_HANDOFF.md` (cost table) in the same folder. Frozen version (2026-11-02, after the verify chain):
sha256 88454db6e17cf4e72cfa651ea253c9fc8599d1317a553d25d14dd96685570545 - check it before a long run; after any change
run `opus_r14b/checks/refreeze.sh TAG` (branch opus-r14b-status) and update the sha256 in the documents.

## Commands (python = `C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe -I -B`)
```bash
R=<branch>/opus_r14b/item2/relabel2.py
python $R prepare --job C:/<new dir> --run-id <id> --selfplay <files in name order> [--rows N] [--jobs 2]
python $R run --job C:/<dir> --run-id <id> --probe 'C:\o13\p5\forge_data_probe.exe' --nodes 20000 --workers 2 --mask 0xC [--until "YYYY-MM-DD HH:MM"]
python $R assemble --job C:/<dir> --run-id <id>        # final/train.txt, final/val.txt, final/labels.tsv, MANIFEST.json
python $R status --job C:/<dir>                      # one line: shards, rows (%), last rate, ETA, free disk
```
- `--mask 0xC` = CPUs 2-3 = one physical core (SMT pair); choose production CPUs with the crew. `--workers` 1-2.
- Windows renames that hit a transient PermissionError (virus scanner, indexer, a reader of status.json) are retried;
  a status.json that stays locked is skipped with a warning (never fatal).
- The same `run` command resumes (published shards are re-hashed; an interrupted `shard_K.part.N` stays as evidence and
  the shard is redone as `.part.N+1`). Bound a session with `--until` / `--max-shards`: on this PC the session cannot
  end processes and TaskStop only ends the outer shell.
- Exit codes: 2 bad input (names the file:line), 3 configuration differs / job busy (`job.lock`) / target exists /
  disk floor, 4 integrity (a published file changed), 1 anything else - e.g. a probe that died, timed out or answered
  wrongly: `run` writes "run stop ... <error>" to sessions.log first; published shards stay, the interrupted attempt
  dir is kept, and the same command resumes once the cause is fixed. A changed relabel2.py resumes only with
  `--accept-new-tool`.
- Disk floor `--min-free-gb` (default 50 GiB = the PC rule for C: and D:): prepare and assemble refuse a write that would
  cross it, run stops before the next shard (logged); free space and run the same command again.
- Output to FPOS with the converter earlier jobs used (sha256 24cb2e78...; not checked against the live supervisor's):
  `F:\opus_scratch\rescore_d8\bin\fen2bin.exe train.txt train.pos` (checked: the .pos score
  column = the new labels, 1,200 / 1,200; the whole 1M output: 991,077 + 8,844 records, 0 bad);
  `hce_dump.exe train.txt train.hce` (sha256 a88e519d...) for the .hce (whole 1M output: 0 bad FEN, 0 clamped).

## Input rules (each one cost a finding on 2026-11-02)
- Finished files only; the newest self-play file is still being written. prepare hashes each input before and after
  reading it (exit 2 if a read input changed; inputs after a `--rows` cut are marked `"read": false` and may change).
- R8 v5 (`selfplay_out_r8v5_20261029\forge_selfplay_fast_NNN.dedup.txt`, ~0.9M rows each) writes fixed 1M-position
  shards, so games run from one shard into the next: inputs are ONE stream, give them in name order from one folder
  (anything else is exit 2). The frozen proof version (5c88438f) split games at file changes: fine for the old
  `selfplay_out\forge_selfplay_NNN.txt` (game-aligned), wrong for R8 v5.
- One job per dataset: game ids (`s<origin>g<n>`) and the split are per job; never merge two jobs that share an input.
- The same file (or a byte-identical copy) twice is exit 2. Normalized (Astra JSONL) input must be sorted by
  (source, source_row) across all files (`sort_normalized.py`); `--jobs 2` reads `--selfplay` only.
- The 1M sample had 0 duplicate FENs (self-play dedups), so a label cache saves nothing.

## Checks that exist
- `test_relabel2.sh SCRATCH` (every refusal with its exit code AND reason text, --jobs 2 equivalence, a game across two
  files, disk floor, status line, rename retry under simulated Windows handle contention, missing python-chess,
  sort_normalized round trip + RAM check, mini kill / resume with byte-identical output). Run it after any change;
  it refuses to start without relabel2.py, python, the self-play sample or the probe (`PY` / `SRC` / `PROBE`).
- A probe before a long run (10 s): `probe_bench.py run --exe <probe> --req probe_ref_500.tsv --out new.jsonl`, then
  `probe_bench.py compare probe_ref_500_r13.jsonl new.jsonl` (exit 0 = the R13 probe's answers on all 500).
- `build_probe_opt.sh <new dir>` rebuilds the probes from the branch alone (lock source via `git archive d4f4312`,
  committed `pgo_train_2k.tsv`): plain = R13's command, lto, pgo (tested PGO exe 08299f9f).
- `prove_resume.sh` (1M rows, A uninterrupted vs B hard-exited twice via `--test-kill-after-seconds`), `bridge_check.sh`
  (new code vs the proof's outputs), `fn_diff.py` (function-level diff of two versions), `label_stats.py` (descriptive
  label statistics), `measure_rates.sh workers|nodes|prepare` (cost numbers), `build_probe_opt.sh` + `probe_bench.py`
  (LTO / PGO probe builds, label identity, ABBA).

## 50M runbook
RELABEL_HANDOFF.md "50M runbook" has the commands for R8 v5 shards 001-057 (50,524,643 rows; `--rows 50000000` ends
in 057), per-phase times (prepare ~0.8 h, run ~79 h on CPUs 2-3 with 2 workers, assemble minutes) and the checks
before use. Its prepare command was run as written with `--rows 3000` (exit 0). Not started: Engine NNUE decides.

## Costs measured 2026-11-02 (details: RELABEL_HANDOFF.md; labels identical in every comparison)
- Mask 0xC = the two SMT threads of ONE physical core. 20k nodes, 2 workers: R13 probe ~663k rows/h, LTO+PGO probe
  `C:\o14b\pgo2\pgo\forge_data_probe.exe` (08299f9f, reproducible build) ~691k rows/h -> 50M rows in 75.4 h / 72.4 h
  (7-minute light-load windows); 1 worker ~373k rows/h. 10k nodes 1 worker ~737k rows/h, 5k nodes ~1.19M rows/h.
- Plan with the whole-1M run (PGO probe, 2 workers, 18:49-20:24 through real crew load incl. the npt trainer's Idle
  python on CPUs 0-3): 635,344 rows/h -> **78.7 h for 50M**; its train / val / labels files were byte-identical to
  the proof's (R13 probe): all 999,921 labels equal.
- prepare `--jobs 2` ~66M rows/h (50M in ~0.8 h), `--jobs 1` ~43M rows/h; disk ~341 MB per 1M rows (~17 GB / 50M).
- Path.resolve() costs ~77 us on this PC: never call it per row (R27 doubled the one-process prepare time).

## Measuring next to crew work
- Run `opus_r14b/tools/cpu_users.ps1 -Mask 0xC` (branch opus-r14b-status) before every timing and write its output next
  to the rate. Crew jobs at BelowNormal on all CPUs (Astra's profile_corpus.py, 2026-11-02) starve Idle work on CPUs
  2-3: proof shards went from ~105 s to 140-188 s, an Idle test prepare got 0.7 s of CPU in 150 s.
- Do not run tests next to a long proof on the same two CPUs (it breaks the 2-thread budget and the proof's timing).

## Pitfalls
- Never edit the code a running proof uses: freeze it (sha in run_config.json), change a dev copy, promote with a bridge.
- Never edit a bash driver while it runs; run drivers from private copies.
- Writing text with backslashes through a bash heredoc + inline Python turned `\r \b \f` into control bytes in a
  committed file: write such scripts with the Write tool, then scan (`ctrl_scan.py` idea: bytes < 32 other than LF/TAB).
