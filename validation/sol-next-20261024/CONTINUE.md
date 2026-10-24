# Continuation checkpoint

Mission branch: forge/sol-next-20261024. Full tested engine source is frozen at 074102419c90c6b3725cd83c172e1ec22a2d8203, based on 3afd230; mission lock f4911f2709bd5ae7e5fca7aea30aac5d87314a05 and network74c4009d unchanged. Accepted integration was not modified. Historical separate WIP e7ae15f remains immutable. Do not reset any branch.

Implemented: deferred-capture capacity256; OFF-default runtime NnueInt16 with signed32 accumulators and output widened to64 before cross-group reduction; gated native Windows PowerShell/oracle helpers. Source ZIP/patch identities in releases/sol-next-20261024/*.json. Every new engine build first ran all-runtime-OFF d11=308972. Original Release/ASan source gates, exact four known CTest FAIL lines, parity100k, overflow extremes, ON5-depth fingerprints, T2 midsearch toggles, d8 null counts and original WAC trials are under int16/. Buffer old and supplemental strict profiles are under buffer/.

NPS: NOISE, 6AA+14ABBA/80samples; median+0.439691%,8positive/14,AAband21.467144%. Full raw outputs and independent root audit retained. No retry, matches, SPRT, training, Elo claim or NnueInt16 gate/lock recommendation is authorized by this mission. Default-OFF representation costs +272KiB/worker for the accumulator stack; unchanged nodes are not unchanged performance.

The first timed WAC failed at193 (492completedrows), original failure remains unresolved/unpooled. Fresh separately preregistered full trial completed900 legal rows274/271/278; the diagnostic and fresh trial do not repair the old one. BufferWAC276/265/279 may be a regression. Do not discard either concern as proven host noise.

Next external action: independent CR review, then owner's native Zen5 Windows qualification via tools/windows/zen5_qualify_sol.ps1 and tools/windows/EXPECTED_OUTPUT.md with exact hashes/build flags. Windows helper EXEs are cross-built, not executed here. Whole-engine phase percentages and unsupported-network runtime coverage are still open. Current int16 native comparison uses float AVX2 (compile flags0), not combined stage3 AVX512; that combined int16 profile remains unqualified.

No task-owned engine/build/benchmark jobs remain after native closure. Check current status before proceeding. Pre-existing untracked .github/workflows/independent-teacher-ci.yml, tools/nnue/, validation/nnue-pipeline-20261023/ belong to older/other work and were preserved untouched; do not stage or delete them inadvertently.
