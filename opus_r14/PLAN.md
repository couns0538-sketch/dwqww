# R14 (Opus) - plan, block 1: setup + Phase A items 1-3 (+ the P4 CR patch Couns asked for)

Started 2026-11-02 ~09:40 PC clock (PC clock = PT + 9 h, so ~00:40 PT). Next blocks get their own short plan here.
No sub-agents (Couns, 2026-11-02): every review is a structured self-review, written down as NOT independent.
Everything is UNPROVEN; only crew gates decide strength, QA does official timing.

## Skipped (already done) and why - from a read-only survey at the start
| item | state found | action |
|---|---|---|
| all eight `opus-r13-*` branches | remote head = local head; the crew pushed nothing to them | build on the R13 tips |
| P5 tool files | already committed + pushed (0be1d80a, 2026-11-02 09:35 PC clock, 9 files) | skip the commit; RESULTS.md (said RUNNING) is rewritten |
| P6 CR + QA + gates | `CR_PASS_p6syzygy_{path,pd4}_al1_ltopgo_150374ff.ok` (2026-11-01 12:12 PC clock): QA precheck OFF pins, perft, ON benches, uci = lock 61 + Syzygy lines, 4-game smoke; gates `uhoP6syz_path_1503`, `uhoP6syz_pd4_1503` + HELD 8moves confirms in the gate list | no handoff / gate prep / rebuild; only the evidence goes into RESULTS |
| P3 singles | CR PASS (3 .ok files, 2026-11-01 10:29); gates `uhoSF26S_{nmpprior,lmrgap,mccorr}_029d` + HELD 8moves confirms queued | no SPSA, no rebuild; only the combined line is prepared (A5) |
| E3 hand lines | crew gates uhoE3a/b/c; uhoE3c (Rule50Damp 30) running since 05:18 PC clock | no gate work |
| `.git/info/exclude` | already has `__pycache__/` and `*.pyc` | nothing to add |
| AGENTS.md | none on main or any opus branch; the crew's AGENTS.md files on astra-* branches are Astra-specific | new `AGENTS.md` on this branch (policy verbatim + Opus R14 rules) |

CR fix files: `C:\Users\Administrator\qa_crfix_astra_r10\r13_patches\` holds p4_v2nets_crfix.patch (md5 1e7b5d20),
p4_v2nets_delta_crfix.patch (cc826b0a), p7_e3fit_crfix.patch (129d440e) and p4_final_delta_ports_crfix.patch (d884c23b,
written 2026-11-02 09:52). My first survey searched only `grok-pc\`, `D:\grok-pc-data`, `F:\forge_push` and `C:\o13` and
wrongly called them unreachable; Couns pointed at the folder. The P6 LOW crfix (4b537823, test tooling) is not in it.

## Block 1 order
0. **P4 CR patch (Couns, 2026-11-02 ~09:55)**: on opus-r13-p4-v2nets (df79fb6e) `git apply p4_final_delta_ports_crfix.patch`
   (d884c23b); result md5 parity_v2.sh 9c124cc3, GPU_REQUEST.md 4246dfd5, main.rs 9ede6e56; full cargo build (fresh target dir,
   offline, mock backend); H256 parity rerun in a fresh dir with a legal-only FEN file (10000/10000 exact, AVX2 + SSE) + planted
   bug; commit + push. 1e7b5d20 / cc826b0a do not apply in either direction on df79fb6e (their items are in e23fca30; d884c23b
   ports the rest).
1. **Setup**: this file, `opus_r14/TOOLS.md`, `AGENTS.md`, `opus_r13/STATUS.md` (real state; stray untracked copies listed).
   Scratch `D:\o14a\` (<= 10 GB; D: had 61.6 GB, floor 50), F: write-forbidden (44 GB < its reserve), load gate
   `opus_r13/tools/pc_gate.ps1` before heavy steps, CPUs 2-3 (0xC), BelowNormal/Idle, <= 2 threads.
2. **A1 P5** (opus-r13-p5-nnue-data): RESULTS = what job1 did (r13p5-20261101-a, Astra's 9,206,371-row forge_filtered.pos,
   20k nodes, 1 worker, CPU 3, Idle, 11:10-12:25:07 PC clock = 02:10-03:25 PT, 22/461 shards = 440,000 rows, 353,917 pos/h)
   and that its FENs were RECONSTRUCTED (no castling, no en passant, halfmove 0). Fix: Astra's original FEN sidecar
   (`completed/full10m/forge_filtered.fen`, sha256 beb3c31d..., from the archive parts in `D:\grok-pc-data\r11_nnue\astra_dl\`)
   through the existing `--sidecar ... --sidecar-origin original_full_fen` path + a guard against mixed origins in one job;
   proof on 1,000 positions (origin, engine FEN echo, rights counts, label diff vs job1 with control rows identical) and a full
   sidecar/.pos alignment audit. Old labels stay; Engine NNUE decides.
3. **A2 P6** (opus-r13-p6-syzygy): RESULTS gets the kit pass (pc1 = pc2 = 150374ff, OFF/ON compares), the `N WDL and M DTZ`
   load line, bench 16 OFF/path/path+PD4, T1/T4 smoke, mate probe OFF/ON, CI 41295841377 log, CR notes quoted.
4. **A3 P7** (opus-r13-p7-e3fit): apply p7_e3fit_crfix.patch (129d440e) if not in; 6 gate-PGN sha256 into inputs.sha256;
   `fit_e3.py --bounds`, one refit at 50,400,100; candidate lines EvalRule50Damp 60 and EvalOptimism 150 strictly separate.
5. **20-minute review** (Couns): structured self-review of everything pushed in block 1, fix what is wrong, record it.
Then block 2 (A4 rest = H768+ parity, A5 P3 combined line, A6 STATUS) and the main items.

## Block 2 (written 2026-11-02 ~10:35 PC clock, after block 1's pushes) - A4 rest, A5, A6, then the main items
- **A4 P4, parity above H256**: the R3 tree's embedded default net (src/nnue_weights.inc) static-asserts H = 256, so the
  H768 / 1024 / 1536 harnesses build from a copy without that file (D:\o14a\p4\r3_h, otherwise byte-identical; the v2
  loader / features / output code is the same source). Per H: fresh dir, random nets of width H with the R13 seeds, CR's
  parity_v2.sh unchanged (9c124cc3), AVX2 + SSE 10000/10000 exact; planted bug once at H1536. Then commit + push.
- **A5 P3 combined line**: on the handoff exe 029d58e8, `lp_check.py run` (kit v2.3 tool) with Sf26NmpPrior=1,
  Sf26LmrGap=1, Sf26MulticutCorr=1 must give the Sf26Bundle=14 numbers 335098 / 727853 / 2415447 / 9334814 / 29426126; plus
  T1/T4 smoke and mate probe (cand_checks.py) and a CI ASan+UBSan config for the combined line if the P3 workflow lacks it.
  Used only if 2+ singles reach H1.
- **A6**: STATUS.md = real state of every branch.
- **Main 1** (opus-r13-p4-v2nets): `opus_r14/b/GPU_REQUEST.md` with exact commands, minutes per run, staged a -> b -> c,
  L1 768 / 1024 / 1536, >= 2 fresh seeds each, outputs on D: (F: write-forbidden), save rate kept small for the 10 GB
  scratch cap. GPU state at 10:31 PC clock: npt line `npt_k32h3_l1024_bs16k_e8x152m5_g072_lam10_w4_s24` training, keeper
  window to 2026-11-08 with ~132 h of npt lines queued -> no window; never start next to it. Blocker written down if none comes.
- **Main 2** (opus-r13-p2-sparse-l1): `FORGE_SEARCH_SPEED2` build switch (default 0) = TT prefetch at make_move on every path
  (main search, null move, qsearch) + the speedmp MovePicker / piece_type hoist (crew source
  `grok-pc\forge_push\src_speedmp2_h256e12`, CR PASS 2026-10-24), one form only; node-identical at 0 and 1 vs the lock pins;
  kit pc1 = pc2; advisory ABBA >= 10 pairs on one Idle core; CI ASan+UBSan.
