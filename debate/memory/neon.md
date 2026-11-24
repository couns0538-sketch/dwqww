# Neon Memory (8h Continuation — Phase 2: Server-Day Plan)

Updated: 2026-11-24T00:21:30Z (UTC).
Active branch: `debate/server-plan-20261123` (HEAD pushed `fc6cbfd880`).

## Phase & Schedule (`232555Z`, `FABLE OUT` `001806Z`)
- **Phase 0 COMPLETE (`17:25Z`):** `FORMATS.md` 2.9 (`ac566296`), `SETUP_PLAN.md` 2.7 (`4100b2a5`), 7 `scripts_v2/` files **3/3 YES**.
- **Phase 1 COMPLETE (`17:25Z` – `21:25Z`):** Canonical `debate/engine_plan/ENGINE_PLAN_8H.md` (`dfc0a0c2c1`, SHA-256 `f8fb8197...`) holds **2/2 EXACT `AGREE`**.
- **ACTIVE NOW — Phase 2 (Hours 5–8, `21:25Z` – `01:25Z` Nov 24): SERVER-DAY PLAN (`~1h03m` left; Fable checks once at `01:55Z`).**
- **Verified real Linux Forge test binaries:** `/tmp/server_day_bench/build_clean_lto/bin/forge` (GCC 13 PGO+LTO AVX2) plus 4 parity binaries in `/tmp/server_day_bench/avx_cmp/` (`gcc_avx2`, `gcc_avx512`, `clang_avx2`, `clang_avx512` — all 36/36 runs match `known/profile.json` `sg_sha256` `85ac8e75...` bit-for-bit).

## Phase 2 Deliverable Status (`23:18Z`)
1. **`scripts_v2/MANIFEST.sha256` (`89c115b5` / `19b08d01...`, NOW 50 files — Opus added `home/credit.py` + `tests/test_credit.py` at `6500e34a`):**
   - **50/50 audited & voted by Neon (`30 YES`, `20 NOT YET`):**
     - 7 executable/test files **3/3 `YES`** (Phase 0): `engine_lines`, `uciproc`, `record`, `budget` (+ tests).
     - 4 executable/service/test files **2/2 `YES`** (`220400Z`, awaiting Fable): `clockwatch`, `forgeday.service` (+ tests).
     - 19 static inputs **2/2 `YES`** (`225200Z`): ALL 9 `known/*` + ALL 10 `workloads/*`.
     - 18 prior executable/test files **2/2 `NOT YET`**: `launcher`, `bootguard`, `terminal`, `make_control`, `worker`, `packer`, `custody`, `guard`, `content` (+ tests).
     - **NEW (`231800Z`) — 2 files Neon `NOT YET`** (Astra reviewing): `home/credit.py` (`85f07d53d10d...`) and `tests/test_credit.py` (`ea2a32a4ae38...`). Reproduced 6 live Linux bugs (overlapping `not_done`/`never_dispatched_first` -> false `complete`, `done=-1`, unsorted `not_done`; unvalidated `v["piece"]`/`g["state"]`/missing `rows_digest` -> silent `partial` or double-credited repeats; confirmed fork/C1 break -> silent `WAITS` exit 0; corrupt receipt/verdict JSON -> crash exit 1; corrupt `SCHEDULE.1.json.zz` dropped via `Home.ranges()`; `first_index=-2` / empty range ignoring C1 pieces / schema-only DB mutating `meta`).
2. **`debate/server_day/specs/` (all 14 files, set SHA-256 `430a52d6...`) — 2/2 EXACT `AGREE`** (`a12f3e52` Neon, `d98f6ab3` Astra).
3. **`debate/server_day/FINAL_FOR_THE_OWNER.md` (SHA-256 `b7f00182...`) — 2/2 EXACT `AGREE` on the 48-file snapshot** (`80fce008` Neon, `c2d09353` / `7b9303ec` Astra). Will refresh once Astra votes `credit.py` and as Opus's repair drops land!
4. **Published Linux empirical measurements (`231830Z`):**
   - 4-worker full-CPU `clockwatch` kill latency: 20/20 dead before `D` (`1.69–3.23 ms`, `p50=2.10 ms`); 12/12 mid-game tightened-`D` kills (`1.70–3.53 ms`); `SIGKILL` worker double-loss: 12/12 orphaned Forge engines survived without `PR_SET_PDEATHSIG` vs 0/12 survived (`2.76–4.86 ms`) with `PR_SET_PDEATHSIG(SIGKILL)`.
   - 4-variant SIMD+compiler benchmark (`profile.uci`, 4-worker saturation): AVX-512 beats AVX2 by `+9.13%` (GCC 13) / `+8.22%` (Clang 18); Clang 18 ThinLTO beats GCC 13 LTO by `+3.48%`/`+2.62%`; documented Ubuntu 24.04 `--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13` gotcha.

## Next Actions (`00:21Z – 01:25Z`, ~1h03m remaining)
- Standing by actively on `origin/debate/server-plan-20261123` and `origin/debate/server-plan-20261123-astra` (Astra watcher confirmed `8c1c33a5c1` at `70aa73a48f`).
- Automated regression harness `/tmp/server_day_repro/verify_repairs.py` ready for immediate validation of Opus's announced repairs (`guard`, `worker`, `packer`, `custody`, `content`, `credit`, `terminal`, `bootguard`, `launcher`, `make_control`).
- Maintain ~10-minute memory cadence and keep `FINAL_FOR_THE_OWNER.md` synced with 2/2 `AGREE` before `01:25Z`.
