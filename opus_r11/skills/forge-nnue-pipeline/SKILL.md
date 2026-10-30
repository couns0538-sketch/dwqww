---
name: forge-nnue-pipeline
description: The R11 automated NNUE pipeline for Forge (branch opus-r11-nnue-pipeline) - one command from our self-play data (forge_push FPOS/FHCE, R8 v5 .dedup.pos, Astra's filtered set) to deduplicated nnue-pytorch binpacks with a 013/014 holdout, yield-only GPU training with auto-resume and checkpoint rotation, export, exact HalfKA parity, ON/OFF benches, WAC and a gate-ready package; its Code Review rules (Idle + background mode on 3 cores, no STOP/PAUSE files, 40 GB D: floor, full sha256 inputs, .part->verify->rename, holdout proof before training) and its pitfalls. Use for any task that converts self-play data to binpack, trains / exports / checks / packages a K32H3^ net, resumes or extends R11, or reviews it.
---

# R11 NNUE pipeline (2026-10-30)

Rules first: [[forge-pc-rules]]. Trainer facts: [[forge-nnue-pytorch-amd]]. Data map: [[forge-nnue-data]].
Parity method: [[forge-halfka-parity-test]].

## Where
- Branch `opus-r11-nnue-pipeline` (base 7f79c349 = qa-r10v2-fix1; engine source unchanged). Worktree
  `D:\grok-pc-data\dwqww\.claude\worktrees\opus-r11-nnue-pipeline`. `NOTES_R11.md` = status / next / resume.
- Code: `opus_r11/pipeline/` (r11_pipeline.py one command, r11_data, r11_check, r11_train, r11_package, r11_astra,
  r11_hold, r11_common, r11_config.json), GPL run-only tools in `tools/nnue_pytorch_amd/r11/` (r11_pos2binpack.cpp +
  build_r11_tools.py, r11_train_entry.py), tests in `opus_r11/tests/`.
- Output root `D:\grok-pc-data\r11_nnue\` (data/, runs/, nets/, checks/, gate_ready/, smoke_packages/, build/, bin/,
  hce_gen/, astra/, logs/pipeline.log, run/<stage>.pid.json).

## One command
`python -I -B opus_r11/pipeline/r11_pipeline.py --config opus_r11/pipeline/r11_config.json run --profile smoke|full`
(or `run --ckpt <file> --l1 N`, `run --net <file> --l1 N`, `status`, `selftest <new dir>`). Exit 0 PASS, 1 FAIL,
3 WAIT (production holds the GPU, disk floor, incomplete data for a full run): rerun later, everything resumes.
Stop it by its PID (`<root>\run\pipeline.pid.json`); hold it with `r11_hold.py hold [--minutes N]`.

## Stages and what they guarantee
- data: inventory (forge_push `.pos.info` ready rule, r8v5 `.dedup.json` marker, Astra supersedes forge_push 003),
  append-only registry (013/014 holdout first), FULL sha256 of every input (verified before each read), hce generation
  for r8v5 (S20 hce_dump qualified against production .hce first: 200,000/200,000), multi-pass bounded-RAM dedup on
  (32-byte board, stm) keys (first occurrence in registry order wins), conversion in value order under the disk floor,
  writer `.part` -> verify (loader reader square by square + .hce) -> rename; writer_bad > 0 = FAIL.
- holdout proof (`opus_r11/tests/test_r11_holdout_real.py`): 013/014 are #0/#1 and the only holdout, no TRAIN code in
  them, no TRAIN row shares a position with ANY 013/014 row (full scan), dedup order on a key-space slice; PASS writes
  HOLDOUT_TEST.json with the hashes of registry/decisions/file lists. The train stage refuses without it or after a
  change.
- train: yield-only (never next to a production trainer; exit 76 when one appears; the check runs before `import torch`),
  RAM floors (exit 75 / 97), disk floor before each checkpoint, rotation newest 2 + best by val_loss across restarts,
  exact resume (`r11_next_epoch`), checkpoints zip-checked before rename.
- export: serialize.py `--features=K32H3^ --l1=N` on the CPU; the `.part.nnue` must load in the HalfKA tool.
- check: AVX2 x86-64-v3 build of 7f79c349 from `git archive` (FMA 0, zmm 0; never znver5, never exe 9b7e2fcd),
  fens_12k parity 12000/12000 exact vs nnue-pytorch float64, OFF uci_check --full ALL OK (d11 312866), ON bench
  d11..d22 stable over repeat + reload, WAC 300 at 200 ms (ON and OFF).
- package: gate_ready/<net>_<sha8>/ (net, exe, SHA256SUMS, bench.txt, parity.log, wac.txt, check.json, provenance,
  README, GATE_EXE.txt = the EXE SHA256, never the commit); smoke runs go to smoke_packages/ (not candidates).
  Nothing is ever queued: QA queues after Code Review.

## Numbers to reproduce
- Writer = J1 bytes: shard 001 all-train md5 9bd30944 (466,506 records, 0.27 s). Real inventory 67 shards / 344.4M rows.
- Astra: whole archive sha256 148803c5... 2,329,781,152 bytes; forge_filtered.pos 2019bf8e, .hce 9c5f4e6d;
  9,206,371 rows = rows of forge_push 003 (score/meta/hce equal, order kept on 9,206,203 unique triples).
- ep20 (npt_line104, md5 ceaf1837): parity 12000/12000, ON d11 346013 d13 908618 d16 4091355 d20 23371918 d22 39606328,
  WAC ON 270 / OFF 272; re-export from epoch=19-step=186140.ckpt byte-identical. QA queued it as gates 97/98.
- Check exe GATE_EXE ed6a0b189ee0a456baade51c39d05857922efbab8e12e408cb471d1011da12ad.

## Pitfalls seen
- Background mode resets the priority class: `SetPriorityClass(PROCESS_MODE_BACKGROUND_BEGIN)` after Idle gives Normal
  (base 8) and Normal children; set background FIRST, Idle second (then class Idle, I/O very low, both inherited).
- psutil AccessDenied: a SYSTEM kernel child (ppid 4, no name) has an unreadable command line; count unreadable python
  (or unnamed non-kernel) processes as production, skip kernel children, or the wait never ends.
- A `comment*` key in `limits` broke `Limits(**...)` for every stage (selftests use their own configs): use
  `limits_from(cfg)` and keep a test that loads the SHIPPED config.
- Bash heredocs eat backslashes in Python/C++ patch text (`'\\'` became `'\'`, `\\\n` became a literal `\n`): patch with
  the Edit tool or a script file written with the Write tool.
- Killing processes is denied (even R11's own): QA stops R11 by PID; R11 itself only lowers a process (Idle, mask 0x700).
- D: free space moves with other jobs (67 -> 39 -> 45 -> 42 GB in two hours): the conversion stops before 40 + 2 GB and
  resumes later; small state files (< 64 MiB) only need 1 GB free.
- The permission settings' ask rule `Bash(git push *)` prompts on every push; changing settings is blocked for the agent.

## Tests
`opus_r11/tests/test_r11_tools.py <new dir>` (Astra staging/pins, hold event, priority, psutil, disk, sha256, GPL
boundary, yield-only, check before torch), `test_r11_data.py <writer exe> <new dir>` (dedup/holdout/supersede/resume/
writer drop/.part/holdout test + gate on synthetic data), `test_r11_train.py <new dir>` (the one command end to end on
the CPU: gate, train 2 epochs, resume to 4, rotation, export, parity, benches, WAC, smoke package, yield).
