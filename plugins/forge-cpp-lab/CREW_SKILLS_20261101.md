# Forge crew skills — Codex terminal / PowerShell

This extends Forge C++ Lab to version 1.1.0. It adds the seven requested skills; the existing C++ engineering skill is retained. Installing skills does not start a build, match, trainer or gate.

| Skill | Work it directs and helper supplied |
|---|---|
| `forge-lock-proof-set` | One configured run of two independent byte-identical LTO+PGO builds, current OFF pins, active ON difference, perft, T1/T4 and ASan+UBSan, with a table and bound proof report. Native recipes must be prepared from the actual engine checkout. |
| `eval-exact-simd-port` | Native raw-bit scalar/SIMD/VNNI parity on pinned fens12k, active-path evidence and one-weight negative control before timing; checker verifies bound traces. |
| `abba-nps-timing` | Quiet single-core T1 A/A calibration then at least ten complete ABBA blocks, exact nodes, median ratio and spread; checker verifies recorded identities and statistics. |
| `npt-data-holdout-check` | Independent complete 013/014 position and authentic game-ID separation, with exact six-field source FEN preservation; auditor consumes authoritative normalized exports. |
| `resumable-shard-job` | Immutable checkpoints/shard hashes and owned-test interruption/resume MD5+SHA256 comparison; included fixture must be followed by the real adapter replay. |
| `grok-pc-safe-run` | Reviewed D-only job, Idle priority, at most two declared workers/CPUs, 32 GiB reserve, protected roots, no other-process/queue control. PowerShell policy preflight is not an OS sandbox. |
| `gate-handover-pack` | New sealed artifact pack, MD5SUMS/SHA256SUMS, README/GATE document and fresh supplied start/srand snapshot scan, bound to tested binaries/net/options. QA still checks the live queue. |

## Install once per crew member

Use **one** installation method to avoid loading both plugin and standalone copies of the same skill.

### Plugin route

For a fresh Codex marketplace registration:

```powershell
codex plugin marketplace add https://github.com/couns0538-sketch/dwqww --ref astra-crew-skills-20261101 --sparse plugins/forge-cpp-lab --sparse .agents/plugins --json
codex plugin add forge-cpp-lab@forge-engine-tools --json
codex plugin list --available --json --marketplace forge-engine-tools
```

CLI command syntax was inspected locally. Installation is a user action, not performed here. If `forge-engine-tools` was already registered against the older branch, inspect `codex plugin marketplace list --json` and use the client marketplace settings to select the new branch. `marketplace upgrade` refreshes the **registered ref**; it does not by itself switch an old branch to this one. Do not delete/reinstall other crew plugins to resolve a conflict. Use the standalone route if the client cannot import this catalog. Start a fresh Codex session after installation and verify all seven names are available.

If PowerShell chooses a blocked npm `.ps1` shim, use `codex.cmd` for the same arguments; do not lower execution policy just to install these files.

### Standalone skill files

After extracting the delivered bundle, open PowerShell in its root (containing `plugins`). This copies only the seven skills to the normal per-user Codex skill folder. It refuses any existing name, preserving files rather than overwriting another crew member's work:

```powershell
$names = @('forge-lock-proof-set','eval-exact-simd-port','abba-nps-timing','npt-data-holdout-check','resumable-shard-job','grok-pc-safe-run','gate-handover-pack')
$source = Join-Path (Get-Location) 'plugins\forge-cpp-lab\skills'
$destination = Join-Path $env:USERPROFILE '.agents\skills'
# First inspect existing names. If any already exists, review/update that skill
# through your normal crew process; do not make a duplicate or overwrite it.
foreach ($name in $names) {
    if (Test-Path -LiteralPath (Join-Path $destination $name)) { throw "Skill already exists; review existing $name before installation." }
    if (-not (Test-Path -LiteralPath (Join-Path $source "$name\SKILL.md"))) { throw "Missing packaged skill: $name" }
}
$null = New-Item -ItemType Directory -Path $destination -Force
foreach ($name in $names) { Copy-Item -LiteralPath (Join-Path $source $name) -Destination $destination -Recurse -ErrorAction Stop }
```

The command deliberately stops on **any** existing name; it does not automatically merge versions or claim to compare their contents. The skills' helpers and references stay beside each SKILL.md. Installation writes to the crew member's Codex skill directory; the D-only workload policy applies to subsequent grok-pc jobs.

## Invoke from the engine checkout

These are Codex prompts, not direct native engine commands. They tell the installed skills to recover the current baseline and prepare reviewed, pinned job records from the actual checkout. They do not assume an obsolete Forge lock:

```powershell
codex 'Use forge-lock-proof-set. Recover the current lock, prepare the native recipes and run the complete proof set on an authorized test host.'
codex 'Use eval-exact-simd-port. Prove raw-bit parity on our pinned fens12k and a one-weight negative control before any timing.'
codex 'Use abba-nps-timing. Calibrate A/A, then run quiet-core ABBA with exact nodes and report median and spread.'
codex 'Use npt-data-holdout-check. Audit the frozen training export against complete 013 and 014, authentic game IDs, and original full-FEN state.'
codex 'Use resumable-shard-job. Verify the fixture, then prove the actual isolated shard adapter survives interruption with identical output MD5.'
codex 'Use grok-pc-safe-run. Review the D-only job manifest and protected roots, enforce Idle and at most two workers, and preserve logs.'
codex 'Use gate-handover-pack. Seal the verified artifacts and fresh copied start/srand scan for QA without changing any live queue.'
```

Run only the relevant command for the current task. The skill directories contain exact helper CLIs and complete record contracts. Set `$SkillDir` to the selected installed skill and `$RunDir` to a new approved evidence directory when using those examples. Helper PASS means the documented scope, not blanket acceptance of an engine or evidence of Elo.

## Two deliberate boundaries

- T4 is incompatible with the grok-pc two-worker limit. Use a separate explicitly authorized four-thread test host for the full proof set; never relax the grok-pc safety profile silently.
- The requested lock proof's **ON bench differs** rule qualifies behavior-changing feature gates. A bit-exact SIMD optimization should preserve search identity. Do not distort the algorithm just to make its ON nodes differ; use the exact-parity/identity protocol for that class of change.

No real private holdout, native Windows engine, live trainer, production restart or gate was exercised while authoring this package. Test logs separate original helper/fixture results, PowerShell syntax/pure-helper checks and unrun platform qualification. These workflows cannot prevent a trusted executable from ignoring its contract; native adapters, declared protected roots and original logs require review.
