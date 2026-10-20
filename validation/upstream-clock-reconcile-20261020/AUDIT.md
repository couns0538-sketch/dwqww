# Upstream clock reconciliation audit

Checkpoint saved before analysis; initial read-only source audit completed on 2026-10-20. A later authorized RED reproduction used the unchanged frozen engine and exact accepted shim/probe, as recorded below. No production file, engine binary, Git state, existing build, or running job was changed. The initial proposed commands below were not executed verbatim; the later dedicated driver preserves the exact executed commands.

## Revisions and preservation boundary

- Frozen 6.4.12 match source: `8865666cc0ab4961cd507bae40ff6ce44e9319df`. Its current branch metadata was `fc98484` when inspected. Leave its source, settings, binaries, hashes and match record frozen.
- Latest fetched accepted integration: `356e863dbd86d2ce24b8ee9486d7406f1d525480`, including clock integration `294cf1ba7d2e3e77a70a08578958a5faea3b54dd` and its native CI baseline-recovery follow-up. Do not reset to `2fc649e`, `9108d01`, or an older accepted checkpoint.
- Common ancestor: `2fc649effb6d2f09f4fdf63b44d59283fe26b616`. The accepted side contains eight additional commits, 23 changed/added files. Its only production-engine delta from that ancestor is the three-file clock-origin change. Preserve its workflow, reports, diagnostic patches, and native probe/driver as evidence; their saved patch files are not instructions to apply another engine fix.
- Accepted `356e863` driver now obtains its baseline from authentic pinned pre-fix `06c581895708a6eb9ff26b380d818f72f7bd9ebf`; retain that change. Do not restore reverse-patch reconstruction, which the accepted CI report says failed before compilation.

## Exact overlap and differences

| Path or mode | Accepted `356e863` | Frozen `8865666` | Reconciliation |
|---|---|---|---|
| Finite UCI clock/movetime | Capture `go_received` before joining the old search, parse limits, set `start_time` only if `!infinite && !ponder && (time_ms >= 0 || movetime_ms >= 0)`; Worker uses it. | Capture `command_start` immediately after reading the command line, before parsing/join, assign `request_start` to every ordinary `go`; Worker uses it. | Both already charge timed admission. Preserve the earlier receipt point and finite timed predicate; do not add another timed correction. |
| UCI depth/nodes/mate with no clock | Worker-local origin. | UCI admission included in reported time and NPS denominator. | Restore accepted worker-local reporting. |
| UCI depth/nodes/mate **with** a clock | Receipt origin, because the predicate tests clock presence, not the depth/node/mate cap. | Receipt origin. | Keep receipt origin; do not incorrectly classify every depth/nodes command as untimed. |
| UCI infinite, including infinite plus clock | Worker-local reporting; no time limit. | Receipt-based reporting; no time limit. | Worker-local reporting, no time limit. |
| UCI ponder | Worker-local reporting. | Receipt-based reporting. | Restore worker-local reporting. Budget clock remains ponderhit-based. |
| Direct Searcher, unset origin, finite timed | Main Worker starts after facade setup/helper admission. | Facade starts clock before vector/table/lease/helper setup and passes a shared origin. | Preserve stronger finite timed facade accounting. |
| Direct Searcher, unset origin, untimed/ponder | Worker-local origins. | Facade origin for all workers. | Preserve accepted default worker-local reporting. |
| Explicit public timestamp | Public field `start_time`. | Public field `request_start`. | Support both names, with `start_time` authoritative. |

Receipt starts after a complete line has been read; neither implementation accounts for time waiting for the newline, earlier queued commands, or runner-to-engine transport. Book hits bypass Worker search. `go perft` is a separate path and unaffected.

Ponder **budget** behavior is already the same: accepted `src/search.cpp:561` and frozen `:634` return zero from `elapsed_ms()` until `ponder_hit_ns` exists, then use that timestamp. `should_stop()` and soft budgeting use this function. In contrast, emitted `info time`/NPS and `SearchInfo.elapsed_ms` use raw `now - start_` (frozen `:1262-1263`, `:1288-1289`, `:1304-1305`, `:1422-1423`), so reporting keeps including pre-hit thinking, and the origin discrepancy changes the admission component. Do not replace reporting with `elapsed_ms()`: that would introduce a separate reporting behavior change.

Frozen 6.4.1-derived safety is stronger than accepted clock-only source: expired-budget preflight occurs after root legality/setup and before iterative search; helpers reset published counts and perform the same preflight before surrendering their own deadline. Preserve this entire block (`8865666:src/search.cpp:1297-1313`), current ponder precedence, all TT race/lifecycle repairs, TT rule50 policy, underpromotions, root-effort fixes, OwnBook control, and later search/NNUE changes. This audit identifies no new strength result.

## Smallest follow-up 6.4.13 source contract

Merge/preserve the complete accepted `356e863` ancestry and resolve just the conflicting timing semantics in a new correctness candidate; do not rewrite or relabel frozen 886 match inputs.

1. Keep public `SearchLimits.start_time` and retain existing `request_start` as a documented compatibility fallback. Resolve `start_time != zero ? start_time : request_start`; an explicit accepted field must win if both are supplied. Put the added field at the end of the existing struct to avoid shifting its current positional aggregate prefix. There is no binary ABI promise here: consumers must rebuild.
2. In UCI, keep `command_start` captured immediately after getline. Supply it in `start_time` only for `!limits.infinite && !limits.ponder && (limits.time_ms >= 0 || limits.movetime_ms >= 0)`. Stop assigning `request_start` automatically to every go. This reuses the accepted timed-only correction.
3. In `Searcher::search`, copy limits as now. Normalize an explicit `start_time`/legacy `request_start` into `worker_limits.start_time`. If both are unset, generate a shared facade origin **only** for the same finite timed predicate. Otherwise leave both zero for worker-local analysis timing. Capture the finite timed fallback before TT aging, exclusive lease/gate drain, and helper creation, as frozen source does.
4. Worker resolves authoritative field, legacy fallback, then local `now`. This fallback also protects existing direct `Worker::search` callers. Keep the current deadline preflight and helper behavior unchanged.

Two scalar fields are justified by the two already exposed source APIs: current `tests/tests.cpp` uses `request_start` at lines 513/558/570/582, and saved instrumentation patches use that name; accepted integration exposes `start_time`. A simple rename breaks one set. A union/reference/macro alias adds lifetime/copy/global-token hazards or custom construction for little benefit. Do not add a third field, a separate reporting clock, or an additional deadline mechanism. Explicit timestamps remain honored even for analysis/ponder, matching the existing public behavior; only **automatic** origin selection is scoped.

## Proposed exact negative/positive probe

The accepted native probe is `356e863:validation/hourly/2026-10-20-go-origin-native/native_clock_probe.py`. At a 440ms pthread_create delay it requires baseline timed first-info `<220ms`, candidate timed first-info `>=380ms`, and candidate depth-1 first-info `<220ms` (lines 125-132). Its own `BAD_GO_ORIGIN_ALL` fixture was deliberately designed to reject the all-go origin behavior (`REPORT.md`; fixture lines 20-23). It checks UCI-visible origin separation; its PASS predicate does **not** enforce a bestmove wall-time deadline. Raw journals, exit validity, bestmove syntax and hashes are retained.

Run only when the controller authorizes local validation resources. This command extracts the unchanged accepted probe in memory and compiles only its diagnostic preload shim outside the checkout. Run once with a hash-verified frozen-886 Release binary for RED, then with the separately built frozen-6.4.13 Release binary for GREEN. Replace only the binary argument for the latter; the fresh temporary directory prevents overwriting evidence. Do not use sanitizer engines for these timing thresholds.

```bash
cd /workspace/dwqww
PYTHONDONTWRITEBYTECODE=1 python3 - /workspace/.cloud-setup/forge-tt-single-worker-gated-release/forge <<'PROBE'
import hashlib, json, os, pathlib, subprocess, sys, tempfile
repo = pathlib.Path.cwd()
accepted = '356e863dbd86d2ce24b8ee9486d7406f1d525480'
folder = 'validation/hourly/2026-10-20-go-origin-native/'
def source(name):
    return subprocess.check_output(['git', 'show', accepted + ':' + folder + name], cwd=repo)
binary = pathlib.Path(sys.argv[1]).resolve(strict=True)
out = pathlib.Path(tempfile.mkdtemp(prefix='forge-clock-reconcile-', dir='/tmp'))
shim = out / 'libdelay.so'
subprocess.run(['cc', '-std=gnu11', '-O2', '-fPIC', '-shared', '-Wall', '-Wextra',
                '-Werror', '-x', 'c', '-', '-o', str(shim), '-ldl'],
               input=source('delayed_pthread_create.c'), check=True)
ns = {'__name__': 'accepted_clock_probe'}
exec(compile(source('native_clock_probe.py'), 'accepted_native_clock_probe.py', 'exec'), ns)
results = [ns['run_trial'](binary, shim, 'candidate_timed', 'go movetime 1200', out, 440),
           ns['run_trial'](binary, shim, 'candidate_depth', 'go depth 1', out, 440)]
checks = {'timed_origin': results[0]['first_info_time_ms'] >= 380,
          'analysis_origin': results[1]['first_info_time_ms'] < 220}
summary = {'accepted_probe_source': accepted, 'binary': str(binary),
           'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
           'probe_sha256': hashlib.sha256(source('native_clock_probe.py')).hexdigest(),
           'shim_sha256': hashlib.sha256(shim.read_bytes()).hexdigest(),
           'results': results, 'checks': checks,
           'status': 'PASS' if all(checks.values()) else 'INCONCLUSIVE_OR_FAIL',
           'scope': 'candidate-side origin assertions only; not full upstream comparison or strength'}
(out / 'result.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({'evidence': str(out), **summary}, indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
PROBE
```

Source-predicted RED on current 886: `timed_origin=true`, `analysis_origin=false`, depth first-info about 440ms, nonzero exit; host pauses can make either separation inconclusive. GREEN after reconciliation: timed first-info at least 380ms, untimed depth-1 below 220ms, both normal exits and valid moves. These are predictions, not executed results.

For the complete unchanged three-trial upstream comparison, use its extracted `native_clock_probe.py` with `--baseline /absolute/build-of-06c581895708a6eb9ff26b380d818f72f7bd9ebf/forge --candidate /absolute/frozen-followup-build/forge --shim /absolute/libdelay.so --out /fresh/result/path --delay-ms 440`. Preserve accepted driver/workflow behavior. Its full CMake/CTest commands are in `run_native_validation.sh:51-59`; the workflow can be manually dispatched for the reconciled revision when that revision is available.

## Follow-up correctness gates

- Extend existing `test_search_request_time` with all three timestamp cases: accepted old `start_time` expires; zero accepted field plus old `request_start` still expires; fresh `start_time` overrides old `request_start` and old `start_time` overrides fresh legacy timestamp. Preserve all current expiration/helper/ponder/infinite/node cases.
- Add explicit worker-origin observations through the existing friend test probe: unset untimed/ponder origins must be at/after Worker entry; unset finite timed facade origin must precede delayed helper/TT admission and be identical across workers. Avoid fragile millisecond comparisons when a direct captured timestamp assertion suffices.
- Extend admission regression mode matrix: untimed depth/nodes/mate, infinite plus movetime, ponder before hit; finite clock combined with depth/nodes/mate must still include admission. Ponder budget after hit must preserve both immediate-hit and old-hit preflight behavior.
- Run full Release CTest, ASan/UBSan CTest, relevant TSan TT/lifecycle checks, and existing frozen Windows validator/package checks for the new candidate. Native shim evidence is Linux timing correctness only; no Windows/Ryzen timing or Elo inference follows.

Initial audit verification: embedded regression Python parsed successfully with `ast.parse`; the initial read-only phase ran no probe, build, engine, test suite, or match.

## Authorized actual RED reproduction

Executed `PYTHONDONTWRITEBYTECODE=1 python3 validation/upstream-clock-reconcile-20261020/run-red.py`; driver exit **0**, meaning its expected negative regression was observed. All child commands, exit codes and raw stdout/stderr are in `red-attempt1/commands.json`; exact UCI send/receive journals are retained. Accepted diagnostic sources were extracted without alteration from `356e863` and copied into the evidence folder. Only the small shim and UCI fixture were compiled, in `/tmp/forge-clock-red-gu5ljkgk`; the Forge engine was reused unchanged.

Frozen Release engine SHA-256 before and after: `d0a556c75e944ebcb9a25b4a836f545969c3bafe10f9a697be9e85f57d4bc082`, matching the existing prior freeze manifest. Its recorded Release CMake/compile/link metadata matched that same manifest; frozen source-export search.hpp/search.cpp/uci.cpp/CMakeLists.txt each matched exact 886 Git blobs. These checks and all probe-source/shim hashes are in `red-attempt1/identity.json`.

| Actual run, 440ms artificial pthread admission | Timed first info | Untimed depth-1 first info | Probe exit / conclusion |
|---|---:|---:|---|
| Accepted native fixture, scoped origin | 672ms | 14ms | 0 / PASS; baseline fixture timed 12ms |
| Accepted native fixture, deliberately unscoped origin | 452ms | 570ms | 1 / expected RED; baseline fixture timed 21ms |
| Unchanged frozen 886 actual Release Forge | 851ms | 547ms | 1 / expected RED: timed true, analysis false |

Actual Forge returned valid `bestmove e2e4` for movetime and `bestmove e2e3` for depth-1, both engine exits 0 with empty stderr. Bestmove walls were 1202.511ms and 553.142ms. These walls are observations, not pass criteria. The controlled shim requests 440ms; substantial extra shared-host scheduling delay is visible, including in fixture wall times. The engine result is a candidate-side reproduction of the accepted origin assertions, not a full actual-engine pre-fix-baseline comparison, a clock-forfeit test, or evidence of speed/strength. Source tracing independently locates the discrepant assignment at frozen UCI `limits.request_start = command_start` for untimed go.

`recommended-engine-only.patch` is an **unapplied** three-file minimal diff against exact frozen 886. It preserves both public field spellings and authoritative accepted precedence, scopes automatic UCI/facade origins, and leaves the deadline/helper/TT code unchanged. It is a recommendation for the separately checkpointed 6.4.13 integration; it does not incorporate accepted metadata/ancestry and must not be mistaken for a full Git merge. Tests and actual GREEN remain pending production-path authorization.
