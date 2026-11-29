# Combined Monday Placement Compatibility Audit (`2026-11-28` / `2026-11-29`)

**Audience:** Fable & Opus (Monday `2026-11-30` placement review and execution)  
**Scope:** Compatibility, ordering, line-ending safety, verification, follow-up toggles, and rollback audit for the **4 Monday placement draft patches** (`P1`–`P4`) across **6 live target files** in `C:\nnue-lab`.  
**Execution Status:** Audited and tested exclusively on isolated temporary copies (`_tmp_apply_check/`, removed after testing). **Zero live files in `pipeline/`, `runs/`, or `forge/r15dsg/` were modified.**

> **Evidence & Wording Rules:**
> - All SHA-256 checksums, byte sizes, line counts, CRLF checks, and `git apply` / `apply -R` outcomes below are **directly verified on disk** against the current files in `C:\nnue-lab`.
> - Offline filter/diagnostic metrics (e.g., `r0202` audit counts, holdout loss, node probes) are **strictly diagnostic — never Elo claims**. Match strength is decided only by pre-declared `fastchess` games.
> - Where prior match or audit results are cited, **"Opus verified"** vs **"Neon's count"** is labeled explicitly; any H1-stopped SPRT run (e.g., `OPUS_R1_skip_vs_R1_keep_SPRT_0_10_250k`) carries **SPRT early-stopping upward bias** (point estimate `+15.49 [+6.12, +24.89]` Elo at `1,526g`, true effect `~+10..+15` Elo).
> - Note on Time Management (`TM`): `UNIFIED_SEARCH_TREE.patch` (`P4`) includes `ForcedRootClockStop` and `TmAspFailLowGuard` (both default `false`). A separate unplaced draft (`teamwork_wave15/TM_SCALE_FIX_DRAFT.patch`, `TmSoftCapPercent`) is **not** part of these 4 patches; if `TmSoftCapPercent=200` is later evaluated, note its **mid-iteration fail-low abort risk** when a deep fail-low re-search hits the mid-iteration soft cap before resolving.

---

## 1. Executive Summary

| Check | Result | Detail |
|---|---|---|
| **Combined `git apply` compatibility (`P1 -> P2 -> P3 -> P4`)** | **PASS (0 conflicts)** | All 4 patches apply cleanly sequentially with zero fuzz and zero rejected hunks. |
| **Commutativity (`P3 -> P1 -> P2 -> P4` vs `P1 -> P2 -> P3 -> P4`)** | **PASS (byte-identical)** | Both orders yield identical post-apply SHA-256 checksums across all 6 target files. |
| **Canonical order recommendation** | **`P1 -> P2 -> P3 -> P4`** | `P1` has net `0` lines at `config.forge.toml:357`, so `P3` (`328..337`) applies with exact unshifted line numbers (preserving compatibility even for naive line-pinned Python appliers). |
| **Critical Windows line-ending hazard (`core.autocrlf=true`)** | **CRITICAL — FLAG REQUIRED** | System Git (`C:/Program Files/Git/etc/gitconfig`) sets `core.autocrlf=true`. Plain `git apply` silently exits `0` while rewriting LF files to CRLF (`620` CRLF lines on `config.forge.toml`). **`-c core.autocrlf=false` is mandatory** on both `apply` and `apply -R`. |
| **Non-git directory hazard** | **CRITICAL — NO `.git`** | Neither `C:\nnue-lab`, `pipeline/`, `forge/`, nor `forge/r15dsg/` is a Git repo. `git checkout` / `git restore` are invalid. Use Step-0 file backups + `git -c core.autocrlf=false apply -R`. |
| **P4 path-prefix requirement** | **`-C forge\r15dsg` or `--directory=forge/r15dsg`** | `P4` uses `a/include/...` and `a/src/...` relative to `forge/r15dsg/`, whereas `P1`–`P3` are relative to `C:\nnue-lab`. |
| **`src_tree` byte-exact parity (after `P4`)** | **PASS (3/3 identical)** | Patched `search.hpp`, `search.cpp`, and `uci.cpp` match `neon/forge_fixes/unified_search_tree/src_tree/` byte-for-byte. |
| **Full reverse rollback (`P4 -> P3 -> P2 -> P1` with `apply -R`)** | **PASS (6/6 identical)** | All 6 target files return byte-for-byte to their exact pre-apply SHA-256s with `0` CRLF. |

---

## 2. Exact Patch & Target File Inventory

### 2.1 The 4 Monday Placement Draft Patches

| ID | Patch Path (under `C:\nnue-lab\`) | Target File(s) | Bytes | Lines | CRLF | SHA-256 | Placement Role & Gate Context |
|---|---|---|---:|---:|---:|---|---|
| **P1** | `neon/forge_fixes/loop_place/config_forge_skipnoisy_DRAFT.patch` | `pipeline/config.forge.toml` | 2,847 | 28 | 0 | `c43172ebce23d7654fd08f104a7df97a6fb8329b9dec7f0cae162db502fd31d2` | Removes `--keep-noisy` from `[train] train_cmd` (`line 357`); preserves `max_window_positions = 388000000`. Gate: Opus-verified `R1` Seed-1 (`+15.49 [+6.12, +24.89]` Elo @ `250k` `1,526g`, H1-stopped — note SPRT early-stopping upward bias) + declared Seed-2 `250k` rule (`OPUS-2811-R1-H1-VERIFIED`). |
| **P2** | `neon/forge_fixes/patches/datagen_uci_parity_7_8_minimal.patch` | `pipeline/nnloop/datagen_uci.py` | 5,771 | 111 | 0 | `184c6d2b8f880a7a22d23667e5b9ab38df53037c9736e14a115c84b9efa556c7` | Adds `_random_count_for_game(g, game_idx)` so odd `game_idx` uses `[datagen] random_move_count_alt` (e.g., `7`) and even `game_idx` uses `random_move_count` (`8`) when `random_move_count_alt >= 0`; keeps `write_min_ply` matched to `k`. |
| **P3** | `neon/forge_fixes/teamwork_wave15/filterqc_monday_fixes_DRAFT.patch` | `pipeline/nnloop/filterqc.py`, `pipeline/config.forge.toml` | 2,318 | 50 | 0 | `da9c3c1620d2999c248f190827a484e1e78f6f9eb529e443266595bdae9da069` | Adds `draw_conflict_score` predicate (`F-03`) in `filterqc.py` and updates `[filter]` in `config.forge.toml`: `max_abs_score = 1200` (`F-08`), `conflict_score = 300` (`F-03b`), `draw_conflict_score = 400` (`F-03`), `min_pieces = 2` (`F-06`). Motivation from Neon's count on `r0202` (`FILTER_DEEP_AUDIT_R0202_2811.json`, strictly diagnostic — not Elo). |
| **P4** | `neon/forge_fixes/unified_search_tree/UNIFIED_SEARCH_TREE.patch` | `forge/r15dsg/include/forge/search.hpp`, `forge/r15dsg/src/search.cpp`, `forge/r15dsg/src/uci.cpp` | 25,163 | 442 | 0 | `a7b59ec6c1f4c7e87539e2fbb34f0eae44dfbcd1abf08efb70919de0df4ec5ee` | Adds 8 default-`false` UCI options (`MinorCorrHist`, `AspScoreScale`, `BadCapLmr`, `LmrFracCapHist`, `LmrTtPvCutExt`, `ContHist6PlyRead`, `ForcedRootClockStop`, `TmAspFailLowGuard`). With all 8 at default `false`, search matches `r15dsg` (`UNIFIED_SEARCH_TREE_GATES_AND_NPS.json`: bench 11/13/perft 5 = `312866`/`862329`/`4865609`, `0` diffs on 50 pos d9 & 10 pos d12). |

### 2.2 All 6 Target Files — Before Patching (Baseline)

| Target File (under `C:\nnue-lab\`) | Patch(es) | Bytes | Lines | CRLF | Baseline SHA-256 |
|---|---|---:|---:|---:|---|
| `pipeline/config.forge.toml` | `P1`, `P3` | 54,328 | 620 | 0 | `d3c4f4eec16eeda71318476cb4d031c252529f77e491e294ddc49fc79c2fd488` |
| `pipeline/nnloop/datagen_uci.py` | `P2` | 58,740 | 1,100 | 0 | `58a69bd651e50d6a78ed1827ad5f2bbd6c7619d28327641cfdf249b2efb669ad` |
| `pipeline/nnloop/filterqc.py` | `P3` | 9,442 | 209 | 0 | `d48fa8a358bbc6b18ff963c47a17f288ca7ed6f6fe95d53214e89ae2a4494140` |
| `forge/r15dsg/include/forge/search.hpp` | `P4` | 33,146 | 667 | 0 | `07af2ca6290fc019be33ebbc2b88cd30ecd56f7ba94eefefa271c83ca01a7e7f` |
| `forge/r15dsg/src/search.cpp` | `P4` | 167,417 | 3,426 | 0 | `174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4` |
| `forge/r15dsg/src/uci.cpp` | `P4` | 57,105 | 1,249 | 0 | `2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013` |

### 2.3 All 6 Target Files — After Patching (`P1 -> P2 -> P3 -> P4` and `P3 -> P1 -> P2 -> P4`)

| Target File (under `C:\nnue-lab\`) | Delta (Bytes / Lines) | Post Bytes | Post Lines | CRLF | Post-Apply SHA-256 |
|---|---|---:|---:|---:|---|
| `pipeline/config.forge.toml` | `+13 B / +1 line` | 54,341 | 621 | 0 | `3c2ad6d55fa187fa414488a9e5ffd9075def741a8d0fe6ae94be435875fb463f` |
| `pipeline/nnloop/datagen_uci.py` | `+1,257 B / +24 lines` | 59,997 | 1,124 | 0 | `6507fc8c25927bde26e81624537f89b2b12e49b79d6d999d3220b1ecad019453` |
| `pipeline/nnloop/filterqc.py` | `+290 B / +4 lines` | 9,732 | 213 | 0 | `3e07b233177146a37cac15a5726055335c29c275aa6dbad943d751998e9f546a` |
| `forge/r15dsg/include/forge/search.hpp` | `+3,146 B / +43 lines` | 36,292 | 710 | 0 | `06bfe95e7cab74b62539551dd3f6dbf80d1ec8a5fdbaa1d03a3f576552a30333` |
| `forge/r15dsg/src/search.cpp` | `+6,510 B / +116 lines` | 173,927 | 3,542 | 0 | `905919683fae183f6822003b2ee4f623797b8c321f53116455f668485bb4042f` |
| `forge/r15dsg/src/uci.cpp` | `+1,916 B / +22 lines` | 59,021 | 1,271 | 0 | `89552a8a3e8a10f9958d64b02df868281387bf74882b68ad128fa98ba116c453` |

### 2.4 `UNIFIED_SEARCH_TREE/src_tree` Byte-Exact Parity Check

| Reference File (`neon/forge_fixes/unified_search_tree/src_tree/...`) | Bytes | Lines | CRLF | SHA-256 | Matches Post-P4 Target? |
|---|---:|---:|---:|---|---|
| `include/forge/search.hpp` | 36,292 | 710 | 0 | `06bfe95e7cab74b62539551dd3f6dbf80d1ec8a5fdbaa1d03a3f576552a30333` | **EXACT MATCH** |
| `src/search.cpp` | 173,927 | 3,542 | 0 | `905919683fae183f6822003b2ee4f623797b8c321f53116455f668485bb4042f` | **EXACT MATCH** |
| `src/uci.cpp` | 59,021 | 1,271 | 0 | `89552a8a3e8a10f9958d64b02df868281387bf74882b68ad128fa98ba116c453` | **EXACT MATCH** |

---

## 3. Conflict & Ordering Analysis

### 3.1 Target Overlap Matrix

- **`pipeline/nnloop/datagen_uci.py`**: Touched only by **P2** (4 hunks: `@@ -207,7 +207,17 @@`, `@@ -220,8 +230,12 @@`, `@@ -230,7 +244,7 @@`, `@@ -365,6 +379,9 @@`, `@@ -377,7 +394,7 @@`, `@@ -395,8 +412,12 @@`, `@@ -411,8 +432,9 @@`, `@@ -462,6 +484,7 @@`, `@@ -505,9 +528,10 @@`). Zero overlap with P1/P3/P4.
- **`pipeline/nnloop/filterqc.py`**: Touched only by **P3** (3 hunks: `@@ -58,11 +58,12 @@`, `@@ -108,5 +109,7 @@`, `@@ -202,4 +205,5 @@`). Zero overlap with P1/P2/P4.
- **`forge/r15dsg/{include/forge/search.hpp, src/search.cpp, src/uci.cpp}`**: Touched only by **P4** (`18` hunks across the 3 files). Zero overlap with P1/P2/P3.
- **`pipeline/config.forge.toml`**: Shared by **P3** and **P1** (only shared file).

### 3.2 Exact Line-Level Analysis on `pipeline/config.forge.toml` (`P3` vs `P1`)

- **P3 hunk (`[filter]`):** `@@ -328,10 +328,11 @@` spans baseline lines **`328–337`**:
  - Line `330`: `max_abs_score  = 2000` -> `1200`
  - Line `334`: `conflict_score = 600` -> `300`
  - Inserts after line `334`: `draw_conflict_score = 400` (**net `+1` line**)
  - Line `336`: `min_pieces     = 4` -> `2`
- **P1 hunk (`[train]`):** `@@ -354,7 +354,7 @@` spans baseline lines **`354–360`**:
  - Line `357`: `train_cmd = '...'` (removes ` --keep-noisy`, **net `0` lines**)
- **Separation:** `17` untouched lines separate the end of P3's hunk (`337`) from the start of P1's hunk (`354`), and **`21` lines** (`~20` lines apart) separate P3's last modified line (`336`) from P1's modified line (`357`). There is **zero context overlap** and **zero semantic conflict**.
- **Why `P1 -> P3` is the canonical order:**
  1. Applying **P1 first** modifies line `357` with **net `0` line-count delta** (`-354,7 +354,7`), leaving lines `328–337` at their exact baseline line numbers for **P3**. Consequently, **both** `git -c core.autocrlf=false apply` **and** naive line-pinned Python appliers (such as `apply_unified_diff_in_memory` in `verify_skipnoisy_loop_placement.py` and `test_filterqc_monday_fixes.py`, which assert `orig_lines[old_start]` at exact hunk line numbers without offset search) succeed cleanly.
  2. Applying **P3 first** inserts `draw_conflict_score = 400`, shifting P1's hunk header from **`354 -> 355`** (and `train_cmd` from **`357 -> 358`**). `git -c core.autocrlf=false apply` automatically compensates for this `+1` offset (still producing the exact same SHA-256 `3c2ad6d5...`), whereas a naive line-pinned Python applier would fail at line `354`!

---

## 4. Critical Windows & Non-Git Findings

1. **Mandatory `git -c core.autocrlf=false` (Windows `core.autocrlf=true` hazard):**
   - Verified via `git config --show-origin --get-all core.autocrlf`: `C:/Program Files/Git/etc/gitconfig` sets **`core.autocrlf = true`**.
   - Every patch (`P1`–`P4`) and every target file (`6/6`) has **pure LF (`0` CRLF)** line endings.
   - Empirically tested on a copy of `pipeline/config.forge.toml`: running `git apply config_forge_skipnoisy_DRAFT.patch` **without** `-c core.autocrlf=false` exits `0` with empty stderr while silently converting **all `620` lines** to CRLF (`crlf_count = 620`). That breaks SHA-256 verification, fouls `SOURCE_INPUTS` parity, and risks CRLF issues across Python/WSL tooling.
   - **Rule:** Every `git apply` and `git apply -R` invocation MUST pass `-c core.autocrlf=false`.

2. **Non-Git Directory Warning (No `.git` anywhere in tree):**
   - Verified: `.git` is **absent** in `C:\nnue-lab`, `C:\nnue-lab\pipeline`, `C:\nnue-lab\forge`, and `C:\nnue-lab\forge\r15dsg`.
   - Commands such as `git checkout -- ...`, `git restore`, `git reset`, `git diff`, or `git status` will fail with `fatal: not a git repository`.
   - **Rule:** Always take an explicit file backup in Step 0 before applying, and roll back strictly via `git -c core.autocrlf=false apply -R` (in reverse order `P4 -> P3 -> P2 -> P1`) or by restoring from the Step-0 backup.

3. **`UNIFIED_SEARCH_TREE.patch` (`P4`) Path Prefix:**
   - `P1`, `P2`, and `P3` use `a/pipeline/...` headers (rooted at `C:\nnue-lab`).
   - `P4` uses `a/include/forge/search.hpp`, `a/src/search.cpp`, `a/src/uci.cpp` (rooted at `C:\nnue-lab\forge\r15dsg`).
   - **Rule:** Apply `P4` using either `git -C C:\nnue-lab\forge\r15dsg -c core.autocrlf=false apply ...` **or** `git -C C:\nnue-lab -c core.autocrlf=false apply --directory=forge/r15dsg ...`. Both are verified byte-identical.

---

## 5. Operator-Ready Monday Placement Runbook

> **Pre-flight Gates (do NOT skip):**
> - Confirm loop is cleanly stopped between rounds (`C:\nnue-lab\pipeline\STOP` / `STOP_LOOP.cmd`) and no active GPU training or CPU match is writing to `pipeline/` or `forge/r15dsg/`.
> - Confirm Opus line-by-line review + Fable second-read + declared match gates (`Seed-2 R1` rule for `P1`, `F_FIX_25R_v2` / parity / `UNIFIED_SEARCH_BUNDLE_250k_SPRT` gates as applicable per `lab-place-a-change`).

### Step 0 — Mandatory Backup & Pre-Apply Baseline Check

Run in PowerShell:

```powershell
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$bk = "C:\nnue-lab\tmp\monday_place_backup_$ts"
$targets = @(
  "pipeline/config.forge.toml",
  "pipeline/nnloop/datagen_uci.py",
  "pipeline/nnloop/filterqc.py",
  "forge/r15dsg/include/forge/search.hpp",
  "forge/r15dsg/src/search.cpp",
  "forge/r15dsg/src/uci.cpp"
)
foreach ($rel in $targets) {
  $src = Join-Path "C:\nnue-lab" $rel
  $dst = Join-Path $bk $rel
  New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
  Copy-Item -LiteralPath $src -Destination $dst -Force
}
Write-Host "Backup created at $bk"

# Verify baseline SHA-256s before touching any live file
C:\nnue-lab\venv101\Scripts\python.exe -I -B -c @'
import hashlib, pathlib
expected = {
  "pipeline/config.forge.toml": "d3c4f4eec16eeda71318476cb4d031c252529f77e491e294ddc49fc79c2fd488",
  "pipeline/nnloop/datagen_uci.py": "58a69bd651e50d6a78ed1827ad5f2bbd6c7619d28327641cfdf249b2efb669ad",
  "pipeline/nnloop/filterqc.py": "d48fa8a358bbc6b18ff963c47a17f288ca7ed6f6fe95d53214e89ae2a4494140",
  "forge/r15dsg/include/forge/search.hpp": "07af2ca6290fc019be33ebbc2b88cd30ecd56f7ba94eefefa271c83ca01a7e7f",
  "forge/r15dsg/src/search.cpp": "174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4",
  "forge/r15dsg/src/uci.cpp": "2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013",
}
root = pathlib.Path(r"C:\nnue-lab")
for rel, exp in expected.items():
  data = (root / rel).read_bytes()
  got = hashlib.sha256(data).hexdigest()
  assert got == exp, f"Baseline mismatch on {rel}: {got} != {exp}"
  assert b"\r\n" not in data, f"CRLF found in baseline {rel}"
print("BASELINE_OK: 6/6 SHA-256 and pure-LF verified.")
'@
```

### Steps 1–4 — Sequential Placement (`P1 -> P2 -> P3 -> P4`)

Dry-run `--check` first, then apply each patch with `-c core.autocrlf=false`:

```powershell
# Step 1: P1 (skip-noisy train_cmd in config.forge.toml)
git -C C:\nnue-lab -c core.autocrlf=false apply --check C:\nnue-lab\neon\forge_fixes\loop_place\config_forge_skipnoisy_DRAFT.patch
git -C C:\nnue-lab -c core.autocrlf=false apply         C:\nnue-lab\neon\forge_fixes\loop_place\config_forge_skipnoisy_DRAFT.patch

# Step 2: P2 (7/8 opening-ply parity in datagen_uci.py)
git -C C:\nnue-lab -c core.autocrlf=false apply --check C:\nnue-lab\neon\forge_fixes\patches\datagen_uci_parity_7_8_minimal.patch
git -C C:\nnue-lab -c core.autocrlf=false apply         C:\nnue-lab\neon\forge_fixes\patches\datagen_uci_parity_7_8_minimal.patch

# Step 3: P3 (filterqc F-03 / F-03b / F-06 / F-08 in filterqc.py + config.forge.toml)
git -C C:\nnue-lab -c core.autocrlf=false apply --check C:\nnue-lab\neon\forge_fixes\teamwork_wave15\filterqc_monday_fixes_DRAFT.patch
git -C C:\nnue-lab -c core.autocrlf=false apply         C:\nnue-lab\neon\forge_fixes\teamwork_wave15\filterqc_monday_fixes_DRAFT.patch

# Step 4: P4 (unified search + TM guard options in forge/r15dsg, all default false)
git -C C:\nnue-lab\forge\r15dsg -c core.autocrlf=false apply --check C:\nnue-lab\neon\forge_fixes\unified_search_tree\UNIFIED_SEARCH_TREE.patch
git -C C:\nnue-lab\forge\r15dsg -c core.autocrlf=false apply         C:\nnue-lab\neon\forge_fixes\unified_search_tree\UNIFIED_SEARCH_TREE.patch
# Equivalent from C:\nnue-lab root:
# git -C C:\nnue-lab -c core.autocrlf=false apply --directory=forge/r15dsg C:\nnue-lab\neon\forge_fixes\unified_search_tree\UNIFIED_SEARCH_TREE.patch
```

### Step 5 — Mandatory Post-Apply Verification

Run immediately after Step 4 (before any manual follow-up config edits):

```powershell
C:\nnue-lab\venv101\Scripts\python.exe -I -B -c @'
import ast, hashlib, pathlib, sys, tomllib

root = pathlib.Path(r"C:\nnue-lab")
expected_post = {
  "pipeline/config.forge.toml": "3c2ad6d55fa187fa414488a9e5ffd9075def741a8d0fe6ae94be435875fb463f",
  "pipeline/nnloop/datagen_uci.py": "6507fc8c25927bde26e81624537f89b2b12e49b79d6d999d3220b1ecad019453",
  "pipeline/nnloop/filterqc.py": "3e07b233177146a37cac15a5726055335c29c275aa6dbad943d751998e9f546a",
  "forge/r15dsg/include/forge/search.hpp": "06bfe95e7cab74b62539551dd3f6dbf80d1ec8a5fdbaa1d03a3f576552a30333",
  "forge/r15dsg/src/search.cpp": "905919683fae183f6822003b2ee4f623797b8c321f53116455f668485bb4042f",
  "forge/r15dsg/src/uci.cpp": "89552a8a3e8a10f9958d64b02df868281387bf74882b68ad128fa98ba116c453",
}
for rel, exp in expected_post.items():
  data = (root / rel).read_bytes()
  assert b"\r\n" not in data, f"CRLF detected in {rel}!"
  got = hashlib.sha256(data).hexdigest()
  assert got == exp, f"Post-apply SHA mismatch on {rel}: {got} != {exp}"

# Byte-exact parity against unified_search_tree/src_tree/
src_tree = root / "neon/forge_fixes/unified_search_tree/src_tree"
for sub in ("include/forge/search.hpp", "src/search.cpp", "src/uci.cpp"):
  assert (root / "forge/r15dsg" / sub).read_bytes() == (src_tree / sub).read_bytes(), f"src_tree mismatch: {sub}"

# TOML & semantic checks
cfg = tomllib.loads((root / "pipeline/config.forge.toml").read_text(encoding="utf-8"))
assert "--keep-noisy" not in cfg["train"]["train_cmd"]
assert cfg["train"]["max_window_positions"] == 388_000_000
assert cfg["filter"]["max_abs_score"] == 1200
assert cfg["filter"]["conflict_score"] == 300
assert cfg["filter"]["draw_conflict_score"] == 400
assert cfg["filter"]["min_pieces"] == 2

# AST syntax checks on Python targets
for pyrel in ("pipeline/nnloop/datagen_uci.py", "pipeline/nnloop/filterqc.py"):
  ast.parse((root / pyrel).read_text(encoding="utf-8"), filename=pyrel)

# Load config once via nnloop.common.load_config (CLAUDE.md requirement)
sys.path.insert(0, str(root / "pipeline"))
from nnloop.common import load_config
loaded = load_config(str(root / "pipeline/config.forge.toml"))
assert loaded["filter"]["draw_conflict_score"] == 400
print("POST_APPLY_VERIFIED: 6/6 SHA-256, pure LF, src_tree parity, tomllib, load_config, ast.parse PASS.")
'@
```

---

## 6. Separate Follow-Up Config Toggles & Engine Build (Outside the 4 Patches)

Applying `P1`–`P4` alone keeps `datagen_uci.py` at 8-ply (until `random_move_count_alt` is set), keeps `state.json`/`REPORT.md` logging `keep_noisy` (until `keep_noisy = false` is set), and keeps `forge.exe` at `r15dsg` search (until rebuilt and options enabled). Apply these **explicitly after Step 5** as declared:

1. **Keep-noisy metadata alignment (`pipeline/config.forge.toml`, line `434` post-P3 / `433` baseline):**
   - Change `keep_noisy = true` -> `keep_noisy = false`.
   - Why: `pipeline/forge_train_v3.py` ignores `FORGE_KEEP_NOISY`, so `P1` (`train_cmd`) already controls training; setting `keep_noisy = false` stops `pipeline/run.py:627-632` from labeling skip-noisy rounds `"keep_noisy"` in `runs/forge/state.json` and `REPORT.md`.

2. **Activate 7/8 opening-ply parity (`pipeline/config.forge.toml`, `[datagen]` around line `274`):**
   - Add `random_move_count_alt = 7` immediately below `random_move_count = 8` (keeping `random_move_min_ply = 0`, `random_move_max_ply = 7`, `write_min_ply = 8`).
   - Why: `P2` activates parity alternation only when `random_move_count_alt >= 0`. Odd `game_idx` plays 7 random plies (`write_min_ply = 7`, Black first labelled); even `game_idx` plays 8 random plies (`write_min_ply = 8`, White first labelled). Verify `selfgame_ok(cfg) == ""` after editing.

3. **Engine rebuild, tag bump, and `[engine] v3_uci_options` (`pipeline/config.forge.toml`, lines `170` & `214`):**
   - **CRITICAL ORDERING RULE (`forge/tools/build_forge_v3r15dsg_sp_clang_pgo.sh:7-9` & `pipeline/nnloop/engine.py:62-77, 105`):**
     1. Build the new PGO executable **by hand first** into `C:\nnue-lab\runs\forge\engines\v3-<new_tag>\forge.exe` (e.g., `v3-r15dsg-unified-sp-clang`) while `config.forge.toml` still has `v3_build_tag = "r15dsg-sp-clang"` (whose exe exists, preventing `pgo_selfgame.py` recursion) and **before** adding the new options to `v3_uci_options`.
     2. Run the mandatory Forge correctness gates (`bench 11 = 312866`, `bench 13 = 862329`, `perft 5 = 4865609`) and `OptionRefused` preflight on the new exe.
     3. Only **after** the new exe is built and verified, update `v3_build_tag = "<new_tag>"` and add only the match-approved UCI options (`= true`) to `v3_uci_options` in `config.forge.toml`. Never add new UCI options while `v3_build_tag` points to the old exe (`engine.py` refuses unknown options with `OptionRefused`).
     4. Run `nnloop.common.load_config("C:/nnue-lab/pipeline/config.forge.toml")` once after the edit.

---

## 7. Exact Rollback Commands

If any post-apply check fails (or a placed change must be reverted between rounds):

### Option A — Reverse Patch Rollback (when only `P1`–`P4` were applied)

```powershell
# Dry-run reverse check first, then revert in strict reverse order P4 -> P3 -> P2 -> P1
git -C C:\nnue-lab\forge\r15dsg -c core.autocrlf=false apply -R --check C:\nnue-lab\neon\forge_fixes\unified_search_tree\UNIFIED_SEARCH_TREE.patch
git -C C:\nnue-lab\forge\r15dsg -c core.autocrlf=false apply -R         C:\nnue-lab\neon\forge_fixes\unified_search_tree\UNIFIED_SEARCH_TREE.patch

git -C C:\nnue-lab -c core.autocrlf=false apply -R --check C:\nnue-lab\neon\forge_fixes\teamwork_wave15\filterqc_monday_fixes_DRAFT.patch
git -C C:\nnue-lab -c core.autocrlf=false apply -R         C:\nnue-lab\neon\forge_fixes\teamwork_wave15\filterqc_monday_fixes_DRAFT.patch

git -C C:\nnue-lab -c core.autocrlf=false apply -R --check C:\nnue-lab\neon\forge_fixes\patches\datagen_uci_parity_7_8_minimal.patch
git -C C:\nnue-lab -c core.autocrlf=false apply -R         C:\nnue-lab\neon\forge_fixes\patches\datagen_uci_parity_7_8_minimal.patch

git -C C:\nnue-lab -c core.autocrlf=false apply -R --check C:\nnue-lab\neon\forge_fixes\loop_place\config_forge_skipnoisy_DRAFT.patch
git -C C:\nnue-lab -c core.autocrlf=false apply -R         C:\nnue-lab\neon\forge_fixes\loop_place\config_forge_skipnoisy_DRAFT.patch
```

Then re-run the **Step 0 baseline SHA-256 verification** to confirm all 6 files match their baseline SHA-256s byte-for-byte with `0` CRLF.

### Option B — Full Backup Restore (if Step 6 manual toggles were also applied)

```powershell
# Replace $bk with the exact Step-0 backup path
foreach ($rel in @(
  "pipeline/config.forge.toml",
  "pipeline/nnloop/datagen_uci.py",
  "pipeline/nnloop/filterqc.py",
  "forge/r15dsg/include/forge/search.hpp",
  "forge/r15dsg/src/search.cpp",
  "forge/r15dsg/src/uci.cpp"
)) {
  Copy-Item -LiteralPath (Join-Path $bk $rel) -Destination (Join-Path "C:\nnue-lab" $rel) -Force
}
```

Then re-run the **Step 0 baseline SHA-256 verification**.

---

## 8. Automated Test Coverage

Companion verification suite: `C:\nnue-lab\neon\forge_fixes\teamwork_wave17\test_monday_combined_placement.py`

Verified behaviors on isolated temporary copies in `teamwork_wave17/_tmp_apply_check/` (always removed in `try/finally`):
1. Exact baseline SHA-256s and `0` CRLF on all 4 patches, 6 target files, and 3 `src_tree` reference files.
2. Sequential `git -c core.autocrlf=false apply` in both `P1 -> P2 -> P3 -> P4` and `P3 -> P1 -> P2 -> P4` yields identical post-apply SHA-256s (plus explicit check of the `354 -> 355` line shift when `P3` precedes `P1`).
3. Pure LF (`b"\r\n" not in content`) preserved on all 6 patched files (and verifies that omitting `-c core.autocrlf=false` triggers CRLF conversion when `core.autocrlf=true` is active).
4. `tomllib.loads` checks on patched `config.forge.toml`.
5. `ast.parse` + functional sanity tests on patched `filterqc.py` (`F-03`, `F-03b`, `F-06`, `F-08` on synthetic `.plain`) and patched `datagen_uci.py` (`_random_count_for_game` + `selfgame_ok` parity logic).
6. Byte-exact `src_tree` parity on `search.hpp`, `search.cpp`, `uci.cpp`.
7. Reverse `git -c core.autocrlf=false apply -R` (`P4 -> P3 -> P2 -> P1`) restores all 6 baseline SHA-256s byte-for-byte.
8. Audit document wording/completeness checks on `MONDAY_COMBINED_PLACEMENT_AUDIT_2811.md`.
