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
