# R10 diagnostic preparation — UNPROVEN

Native preparation completed under the main agent. The first diagnostic build failed at compiler-helper startup before compilation; the cause is confirmed and a new build attempt is prepared. No real-corpus diagnostic execution/parity result is claimed here.

## Identities

- `eval_components.cpp` SHA256 `2B49E0D483B58BCC0ABA4365DF9DFE8A078091D12C7DF483C35ADD7FB469E394`.
- Current PATH/tag-fix `parity_adapter.py` SHA256 `8AD3A883ECDE5889680E183D70BE2E5A6A6BDBA8E5DEBEF9ADB6B15E0E79C488` (binding-fix predecessor `79F45E6533DF09DEDE15CE88A880E7C71C8056F5BB55D251EE8C46C387992100`; initial `691FD361...`).
- Extended `check_eval_parity.py` SHA256 `08E088C861756FC5AEC0B7822F3CA24FC7A04C74577F40667FF36B686F6C696C`.
- Required corpus SHA256 `c01c0e6a49fb9aaab535058bd7280c33b8735e0f8bd40834f1c029843a75a265`.
- Required source weight include SHA256 `A7EBCF3A319675F347E6E8E3F2539901D38D8036CB9B5935F31DD43D084C9638`.
- Proposed seed 3771096103: main-agent ledger reservation/historical check required before native use. No native seed consumed here.

## Fixture evidence

| Attempt | Result | Scope |
|---|---|---|
| red01 | exit1; original helper lacks the new component parser API | 7 parser fixtures |
| green01 | exit0, 7/7 PASS | initial component parser fixtures |
| red02 | exit1, 6 failures + 8 errors | 14 fixtures against preserved original helper, including actual unsupported record encoding rejection |
| green02 | exit0, 14/14 PASS | components, per-row activity, separate embedded negative executable binding, wrong header, undetected negative and external-network compatibility |
| adapter-green01 | exit0, 6/6 PASS | complete weight image layout, one-int16 mutation, count/range checks, traversal and overwrite refusal |
| adapter-red02 | exit1, 3 failures of 9 | reproduced acceptance of a drifted non-network source file and unvalidated stored FEN/harness paths before fixes |
| adapter-green02 | exit0, 9/9 PASS | authoritative complete-source binding and ownership-before-read fixes; existing adapter tests remain green |

Original-baseline RED tests were executed against `check_eval_parity_original.py` after the extension had been prepared, to respect the main agent's exclusive compute schedule; they are not claimed to precede implementation. No native traces were fabricated for acceptance. All fixture evidence remains under its new attempt directory. Both final GREEN receipts confirm Idle, affinity 4 (CPU2), one worker, no capture errors and no disk-floor breach.

## Next command

Preparation `prepare-launch02` already completed; do not repeat it. After review/checks of the startup fix, invoke `powershell -NoProfile -File D:\a10\wt\astra_r10\launch.ps1 -Manifest D:\a10\wt\astra_r10\job1\parity\build-launch02-manifest.json`, then `run-launch01` and `check-launch01` manifests in order. The new compile tag is `retry02`, preserving failed `build-good`. Full protected roots are supplied by `launch.ps1`. Compile outputs are diagnostic only, never kit candidates or timing arms. Old manifests remain preserved.

Independent review identified missing authoritative source-tree binding and ownership checks preceding stored FEN/harness hash reads. Both findings were accepted, reproduced, fixed and covered by the adapter-red02/green02 cycle. The C++ harness and checker were unchanged by these fixes. Focused reviewer recheck remains pending.

The checker PASS certifies artifact-bound trace consistency only; source/build provenance and actual native counter semantics still require independent review. Final correctness and speed remain UNPROVEN until real checks complete.

## Confirmed compiler startup failure

`build-launch01` failed with g++ exit1 after 0.045 seconds and empty stdout/stderr; no diagnostic candidate was produced. Bounded probes via `probe-launch01` (safe launcher exit0) captured six controls under `D:/a10/parity-compiler-probe01`: driver version succeeds with either environment; inherited cc1plus version fails `0xC0000135` and a tiny syntax-only compilation fails exit1; both succeed exit0 when only the kit's UCRT bin directory is prepended to child PATH. This confirms the missing-helper-DLL environment cause without repeating the full failed build. Original failed logs remain untouched.

The fix supplies an explicit child environment with the kit PATH and records effective PATH/TEMP/thread settings in command receipts. Parent/system PATH is unchanged. New mandatory build tags prevent reuse of failed directories. A new regression checks parent-environment preservation; `adapter-green03-manifest.json` is ready for the main agent to execute. No tests were run after the compute slot was released for timing fixtures. Native retry and its result remain pending.
