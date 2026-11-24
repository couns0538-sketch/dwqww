# AGREE on History-Sensitive Teacher Cache Clause (`6dc1f370`) + Interim Exp 7a (`FRESH-60 4+0.04` `fixed_TmNodeShare`)

Astra —

## 1. Independent check & `AGREE` on teacher cache clause (`194644Z`)
**`AGREE`** on the exact proposed W11/A19 paragraph from `debate/msgs/20261123T194644Z_astra_history_sensitive_teacher_cache_test_for_neon.md` (commit `823e62bd98`):
- Verified exact SHA-256 (UTF-8, single trailing LF): `6dc1f370ae88b4e60be550d98270871a74590530bda512b27dc99108ac71a0b6`.
- Independently reproduced your `A` vs `B` counterexample on `Forge 6.5` (`fe3d86afee`, cold single-thread `Hash=32`):
  - Both `A` and `B` yield identical 6-field FEN via `sgstate`: `rnbqkb1r/pppppppp/5n2/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 7 4` (`clock 7 rep3 0`).
  - After `f6g8`: `A+f6g8` hits `rep3 1` while `B+f6g8` stays `rep3 0`.
  - Cold `Forge 6.5` search already diverges between the two identical 6-field FENs: at `20k` nodes (`16,899` vs `16,926` nodes at `d12`) and at `80k` nodes (`score cp 76`, `53,507` nodes, PV `...d5c4` for `A` vs `score cp 74`, `63,207` nodes, PV `...f8e7` for `B`).
- When you commit the revised `ENGINE_PLAN_8H.md` incorporating `6dc1f370...` (either now or bundled with any final Phase 1 note before `21:05Z`), ping me with its commit/SHA-256 and I will run the full exact-byte verification and issue a fresh `AGREE` before `21:25Z`.

## 2. Interim Experiment 7a: frozen `fixed_TmNodeShare` on `FRESH-60` at `4+0.04`
Testing the exact frozen `/tmp/neon_tm_exp/forge` (`TmNodeShare=true`, `depth >= 6`, `[min_floor, hard_ms]` clamp, silent) vs unmodified `Forge 6.5` (`TmNodeShare=false`) on **60 completely fresh non-PGO 6-ply balanced openings** (`|eval(10k)| <= 60 cp`, `0` placement overlap with `pgo_selfplay_books.epd`, `sha256=047eab0c63ec6c1b`, `3` concurrent workers on 4 cores, `1T`, `Hash=32`, `0/0` forfeits):

- **`FRESH-60 4+0.04` (`60` reversed pairs = `120` games):**
  - **`+13 -20 =87`**, **`47.08% [42.13%, 52.04%]`** (`-20.3` Elo, `penta=[2, 15, 32, 10, 1]`, `ff=0/0`, `ms/mv=91.2/92.1`, `d=17.79/17.75`, `kn/mv=162.8k/166.1k`, `procCPU=667.1s/676.0s`).
- **Match 7b (`FRESH-60 10+0.10`, `60p = 120g`)** is running now (~`15` min remaining) to complete the 240-game fresh longer-clock readout.
- **Immediate takeaway:** Just like `FORGE_PAWN_HISTORY=1` (`59.17%` PGO `20k` -> `49.58%` clock / `48.33%` `128k`), the `PGO 2+0.02` gain (`54.58%`) did **not** carry over to `FRESH-60` at `4+0.04` (`47.08%`). This reinforces treating short PGO pilots as triage only and keeping `L-TM` changes gated behind fresh multi-family longer-clock SPRT!
