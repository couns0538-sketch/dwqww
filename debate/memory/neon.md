# Neon Phase 4 Memory (2026-11-23)

## Current State (07:51Z)
- Shared branch `debate/forge-plan-20261123` synced at `6db1be5d66`; Astra branch synced at `ca2f10e906`.
- Fable entered `A16`, `A17`, `N17`, `A18`, `A19` into `debate/FINAL_PLAN.md` (`143249Z`, `3038d688d0`).
- Agreed 2/2 and waiting on Fable's next checks: `A20`, `N18`, `N19`, `N20` (+ Astra `072803Z` 8-game note), `N21` (+ Neon `075114Z` true 16/16 benchmark correction).
- Voted `AGREE` on `A21` (`075114Z`); waiting on Astra's `..._agreed_a21.md`.

## Key Local Artifacts (kept out of repo in `/tmp/`)
- `/tmp/smp_audit/forge_prod` (AVX-512) & `/tmp/smp_audit/forge_prod_avx2` (AVX2)
- `/tmp/smp_audit/padded_1024_r67.fnn3` (`1024 x 8kb`)
- `/tmp/smp_audit/padded_1024_16kb_r67.fnn3` (old `9/16`-reachable, `km_sha = cc098711e4912762`, `-2.71%` / `-1.09%` `bench 15`)
- `/tmp/smp_audit/padded_1024_16kb_full16_r67.fnn3` (TRUE `16/16`-reachable, `km_sha = 86c900cfb89064fb`, `file_sha = dcc857d3364ba5cf`, `-4.77%` AVX-512 / `-3.31%` AVX2 `bench 15`, `-4.30%` / `-5.65%` `sg20`, bit-identical `1,667,608` nodes & `sg20 SHA = 319d4bcb5866b937`)
- `/tmp/prof_audit/`: `SIGPROF` profiler (`nnue::v3` only `15.96%` of `selfgame`) & dropped noise-level micro-opts (`S1`–`S4`: `+0.18%` SG60, `-0.41%` bench 16).

## Active Research Queue
1. Differential correctness audit of `source/src/board.cpp` + `search.cpp` hot paths (`CuckooRep::upcoming_repetition`, `E1` evasions, `is_legal`, `gives_check`, `see_ge`, `sg_insufficient_material`, `is_draw`/repetition/50-move edge cases) across `100,000+` positions.
2. Audit Astra's Stockfish 17.1 independent referee results (`074712Z`/`075008Z`) & 4M forced-move sensitivity once posted.
3. Investigate genuine stronger-engine "For later" topics backed by hard local proof (e.g., search/eval endgame TB probing + self-play endgame adjudication where `38/1,113` `3.41%` of 4–5 piece Syzygy decisive positions ended as raw draws in `074810Z`, and post-1024 search re-tuning / pruning architecture).
