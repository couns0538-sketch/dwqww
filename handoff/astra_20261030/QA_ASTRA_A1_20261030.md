# QA: Astra A1 data work (dwqww @ 110f0c4a, branch astra-a1-data) — 2026-10-30 ~01:35 PT

Scope: docs/ASTRA_A1_WINDOWS.md, docs/ASTRA_A1_DATA.md, release astra-a1-data-results-20261030 (6 assets),
tools/data/*.py + run_idle_spare.ps1, tools/nnue/train_resid_v3b.py, docs/ASTRA_A1_BLEND_PLAN.md / _ARTIFACTS.md.
Method: read-only. Release downloaded to box /workspace/astra_a1 (box disk: 20 GB free after, 4.8 GB used by this review).
grok-pc: only read-only listing/hash/Python-in-memory reads at BelowNormal. Astra's pipeline NOT run; nothing changed on the PC.

## What the dataset is
- Source: shard forge_selfplay_003 (10,000,000 Forge self-play rows, .pos sha d322089c…, .txt sha ccab2719…).
  Both hashes re-verified on grok-pc (D:\grok-pc-data\forge_push\nnue_data\pos\forge_selfplay_003.pos and
  D:\grok-pc-data\selfplay_out\forge_selfplay_003.txt): MATCH. So this is our own data, one shard of the ~305M.
- Output: forge_filtered.pos (FPOS v1, 9,206,371 rows), forge_filtered.hce (FHCE v1, Forge HCE at engine 926c55),
  forge_filtered.fen (full 6-field FEN, same order), kept_rows.tsv (provenance: input row, 1024-node teacher depth/score/bestmove).
- Labels: score = ORIGINAL self-play score (STM cp, clipped ±3000), result = White result. NOT relabelled.
  The 1024-node Forge probe was used only to filter. Relabelling exists only as a 256-row pilot (4 budgets).
- Filters (first-drop order): holdout(013 head) 52, disagreement 5,477, exact dup 835, near dup 307,691,
  in_check 0, terminal 0, teacher_incomplete 857, bestmove capture 467,148, promotion 11,569 → 793,629 dropped (7.94%).

## Checks I ran (independent)
- All 6 release assets: sha256 == GitHub server digests == transport_manifest; joined archive sha 148803c5… == manifest. PASS.
- Extracted forge_filtered.pos/.hce/.fen: sha 2019bf8e… / 9c5f4e6d… / beb3c31d… == doc. PASS.
- Format: headers FPOS/FHCE v1, n=9,206,371, file sizes exact (16+35n, 16+2n); meta ∈ 0..5. PASS.
- FEN vs .pos board+STM: 1,111,799 rows checked (every 9th + 100k random) → 0 mismatches.
- python-chess on 100k random rows: 0 illegal, 0 in check.
- Exact board+STM duplicates in output: 0. HCE range −2415..2454, no −32768 sentinel, corr(score,HCE)=0.961.
- Stats: STM black 50.0%; White result W/D/L 43.4/30.5/26.2%; castling rights present 22.2%; fullmove median 36,
  ≤8 = 7.2%; halfmove ≥50 = 2.3%. Score bins vs STM outcome are monotone/sane (no sign flip).
- Leakage (board+STM key):
  - 013 head 1.5M: 0 overlap (confirms Astra).
  - FULL 013 (10M) + 014 (6.39M) .pos on grok-pc (hashes 904e6527…, 255afc00…): 339 shared keys with 003;
    **281 kept rows** overlap (160 with 013, 121 with 014). 101 are 32-piece openings, ~150 are ≤6-piece endings. 0.003%.
  - fens_12k (R10 parity set): 160 overlap (self-play-derived simple endings). wac300, microbench wac300, forge-10000
    openings, S08 BENCH/OPENING/WAC corpora: 0 overlap.
- resid_v3b compatibility: trainer (sha 7379d1fc…) reads FPOS 16/32/34-offset layout + <stem>.hce in --hce-dir; the
  output names pair correctly (forge_filtered.pos ↔ forge_filtered.hce). Compatible as-is.
- Provenance: labels are Forge's own self-play scores + Forge HCE; probe is Forge source (926c55, src/ unchanged on branch).
  No Stockfish/other-engine labels, no copied code (IDEA_SOURCE lines present). OK.

## Findings (severity-ranked)

HIGH-1  It is NOT new data for the main (AMD nnue-pytorch) trainer. The running AMD run trains on
        F:\forge_j1_data\forge_train_001-039_ex013-014_j2.binpack, built 10/29 17:18–17:24 PT from all 39 .pos shards
        **including all 10M rows of 003**. Astra's 9.2M is a filtered subset of 003. Adding it on top double-weights 003.
        Fix: use it to REPLACE shard 003 in a new binpack (ablation: 003-raw vs 003-filtered), not to append.
HIGH-2  No FPOS/FEN → binpack path for Astra's output exists on the branch or opus-r6-amd-nnue. The J1/J2 converter on the PC
        (exe sha C3672C3D…, F:\forge_j1_data\convert.log) converts .pos only (no castling/EP; 34 B/record). Fix: convert
        forge_filtered with the same verified J2 converter (VERIFY OK + loader_check like J2), or better a FEN-aware
        converter so the 22% castling / 3.6% EP state Astra preserved isn't thrown away. Flip White result → STM, keep
        score STM cp, and keep the same score scaling the J2 run uses (Forge cp, not SF internal units).
HIGH-3  ASTRA_A1_WINDOWS.md paths are wrong for grok-pc: it expects D:\grok-pc-data\selfplay_out\forge_selfplay_003.pos and
        013/014 .pos there; that folder has only .txt. The .pos live in D:\grok-pc-data\forge_push\nnue_data\pos\.
        As written it fails closed ("Missing input"), so harmless, but it can't run. Fix: separate $PosDir and $TxtDir.
        (We don't need to rerun it anyway — the 10M output is sealed and verified.)
MED-1   Holdout claim is scoped to the 013 head only (Astra says so honestly). Full 013+014 check (done here): 281 kept rows
        overlap. Fix: drop those 281 rows (keys list reproducible from this note's method) before any training that is
        evaluated on 013/014. Low impact, but our rule is zero overlap.
MED-2   Disk blow-up if anyone scales the filter to the full 305M: PosWriter keeps all .part columns (2× data) plus
        kept_rows.tsv (~117 B/row), position_index.sqlite (~86 B/row), FEN (~53 B/row), probe logs. 10M input → ~5.0 GB;
        305M → ~150 GB. D: has 65 GB free. Fix: shard-by-shard runs with a free-space guard, delete .part/logs only after
        seal+check (needs Couns's yes), or don't scale it.
MED-3   CPU pick in the Windows doc ($SpareCpus 12,13,14) is a placeholder; grok-pc has 16 logical CPUs and runs self-play
        (5 workers), gates (4×2 threads) and two trainers (~85% CPU). Idle priority limits harm, but 3 workers would barely
        progress. Fix: 1 worker, or run only when gates are idle. Doc also demands PowerShell 7: pwsh exists on the PC
        (WindowsApps), system Python is 3.14 (Astra tested 3.12; stdlib-only so likely fine), MSYS2 GCC 15.2 present.
MED-4   HCE column is from engine 926c55 (OFF bench d11 312866). It must equal the HCE of the lock the residual net runs on.
        If B4 (or any eval change) gets locked, the .hce must be regenerated. Not relevant to nnue-pytorch (no HCE).
LOW-1   fens_12k shares 160 positions with the training set. Fine for bit-exact parity; never use fens_12k as a
        generalization/loss holdout.
LOW-2   Filter-induced label bias: disagreement rule removes every "−400 cp but won" row (STM win rate in the ≤−400 bin = 0.0%).
        Intended, but it makes the result signal look cleaner than real games; keep the ablation in BLEND_PLAN stage 2.
LOW-3   Bestmove-capture filter used a 1024-node teacher (median depth 5); 15/256 capture/quiet choices flip at 65k nodes.
        nnue-pytorch also does its own smart skipping, so the two filters overlap; fine, just don't double-count.
LOW-4   Exact-dup key is board+STM only (castling/EP ignored), so a few castling-different positions were merged. Negligible.
LOW-5   Release archive contains duplicate .part copies and the unsealed attempt-1 archive (evidence only — must NOT be trained on).
        Docs say so correctly. Archive ~2.3 GB; extracting only the 3 data files needs ~0.83 GB.
LOW-6   Doc wording: trainer "cosine blend" log text is misleading (blend is linear) — Astra flagged it correctly; no fix needed in data.

Claims checked and correct: 9,206,371 kept; waterfall counts; output/asset hashes; 0 overlap vs 013 head; FEN/pos alignment;
no engine/trainer changes (src/ untouched vs 926c55); no Elo claim made.

## Verdict
Data is clean, correctly formatted and honestly documented. resid_v3b: usable as-is (pos+hce pair).
nnue-pytorch: NOT feedable right now (no binpack yet), and it would only duplicate shard 003 already in the J2 training set.
Steps first:
 1. Drop the 281 rows that overlap full 013/014.
 2. Convert to binpack with the verified J2 converter (or a FEN-aware one to keep castling/EP), with VERIFY + loader_check.
 3. Build an ablation binpack = J2 train set with 003 replaced by the filtered 003; train matched vs the current J2 run
    (same seed/steps, eval on 013/014 binpack). Only if it wins, apply Astra's filter to the other 37 shards
    (shard-by-shard, disk-guarded, 1 Idle worker).
 4. Do not run ASTRA_A1_WINDOWS.md on grok-pc until its .pos paths are fixed; there's no need to rerun the 10M job.
