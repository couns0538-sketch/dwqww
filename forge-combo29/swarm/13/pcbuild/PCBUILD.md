# PC r15 build: applied, built, verified (seat 13, FABLE_TO_swarm_5)

## What I did
1. Fetched `handoff/fable-opus-combo29-all-20261114`, read files 2, 3, 4 and 5 in full (file 1 read earlier).
2. Extracted the patch block from file 5 (lines 56..2374 of the saved text) to `/tmp/pc_r15.patch`.
   **sha256 of the saved patch, from its first `diff` line to its last line, starts `d6bd72c531f785f4`** —
   it matches the prefix file 5 states, so I am building the intended text and not a transcription.
3. Applied it in a SEPARATE worktree (`git worktree add ../pc 6b98f217`), never in my base build:
   `cd forge-combo29 && patch -p1 < pc_r15.patch` — all 11 files patched, **no fuzz, no rejects**:
   b4.hpp, board.hpp, nnue.hpp, nnue_v3.hpp, search.hpp, board.cpp, eval_params.cpp, nnue.cpp,
   nnue_v3.cpp, search.cpp, uci.cpp.
4. Built with the PC's extra flag:
   `cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1`, g++ 13.3.0, -march=x86-64-v4.
   `MateAlphaGuard` appears in the exe's own `uci` list (92 options advertised), so the flag took effect.

## Known numbers: ALL MATCH
Fresh process per line, interactive (read to the bench/nodes line, never close stdin mid-command),
and **`Threads 1` + `Hash 16` sent explicitly in every regime** per the swarm rule on scores.

| settings | bench 11 | bench 13 | bench 16 | go perft 5 | verdict |
|---|---|---|---|---|---|
| none (Threads 1, Hash 16) | 312866 | 862329 | 3024920 | 4865609 | all four MATCH |
| S14 | 242796 | 656517 | — | — | both MATCH |
| PC20 = S14 + the six | 278024 | 587276 | — | — | both MATCH |

`id name Chess Engine Forge 6.4.24 candidate`. Exe sha256 `068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4`.
Raw output: `pc_build_check.txt`. Script: `check_pcbuild.py` (it checks every option name against the
exe's own `uci` list first and dies on `unknown option`/`invalid value`/`ERROR`).

## One thing worth recording
My first run of the checker FAILED loudly: `option 'HistPruneMultiplier' is NOT in the exe's uci list`.
That was **my typo** — the option is `HistoryPruneMultiplier`. The check caught it because it validates
names against the engine's advertised list instead of trusting my transcription; had it not, the
`setoption` would have been silently ignored and S14/PC20 would have been measured with one setting
missing. This is the same failure class the swarm has been burned by twice, so I am recording that
the guard worked.

## Consequence for my work
- Both builds now exist side by side: base at `/home/ubuntu/b/rel/forge`, PC r15 at `/home/ubuntu/b/pc/forge`.
- Every finding line from now on names the build AND the settings.
