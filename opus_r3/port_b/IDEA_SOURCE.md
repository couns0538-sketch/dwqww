# port_b (R3-1) — ideas and sources

R3-1 = "build opus-r3-stack on d4f4312 with ALL passed O/C/opus-sol features merged, each still behind its own option
(default OFF)". This job ports three more opus-sol branches onto the stack base `2432670b` (= opus-r3-cifix:
opus-r3-stack@467a59b3 plus the CMake test fix). No new idea is introduced here; every feature is the merged
branch's own, unchanged.

| feature | source branch (head) | spec / report | switch (default) |
|---|---|---|---|
| Self-play datagen v2: in-engine fixed-node self-play written directly as the v3b trainer's `.pos` (FPOS v1) + `.hce` (FHCE v1) | `origin/opus-sol-S32` (`2974675f`) | Sol leftovers S32; `opus_round1/sol_S32/REPORT.md`, `IDEA_SOURCE.md` | build switch `FORGE_DATAGEN` (OFF); CMake option `FORGE_DATAGEN`; always-built `forge_datagen`, `forge_datagen_tests`, CTest `datagen_cli_tests` |
| NNUE inference microbench + per-stage cost table | `origin/opus-sol-S37` (`4822281e`) | Sol leftovers S37; `opus_round1/sol_S37/REPORT.md`, `IDEA_SOURCE.md` | none (tool target `forge_nnue_microbench`, CTest `forge_nnue_microbench_check`); engine unchanged |
| Cold-start attack-table init (`std::call_once`) + 1000-process cold probe as a CTest | `origin/opus-sol-S04fix` (`ea541f2c`) | Sol leftovers S04 (v2 patch) + fix-ups S04-1/S04-2; `opus_round1/sol_S04fix/REPORT.md`, `IDEA_SOURCE.md` | build switch / CMake option `FORGE_ATTACKS_INIT_ONCE` (OFF) |

Method: `git merge --no-ff` of each branch (they fork from `d4f4312` and carry their own cherry-pick of the CI baseline
`0d99f02`, already in the stack), conflicts resolved as unions that keep every stack target, test and option (see the
merge commit messages), then verification against the AL1 lock pins and each branch's own acceptance numbers
(`forge-engine-verify` recipe).
