# Evidence sealer fixtures — UNPROVEN

Scope: synthetic artifact-copy and receipt-validation fixtures only. No native
engine, gate, match, training or real data audit was executed by these tests.

The new standalone `skills/gate-handover-pack/scripts/seal_evidence.py` supports
explicit `incomplete-engine` and `data-tool` purposes. Original strict
`make_gate_pack.py` remains byte-identical to the installed copy, SHA256
`65ca15daa52566320e25f0152831b5480cfe89c6b893fb15b11e6d11a61baced`.
Neither new purpose emits `READY_FOR_QA_REVIEW`. All statuses remain UNPROVEN.

Tests were authored before implementation; execution was deliberately deferred
until the parent released its exclusive compute slot after native work.

- `green01`: 14/15 PASS. The missing-data-report test accidentally retained the
  incomplete-engine blocker, and correctly received an earlier unresolved-blocker
  refusal. Corrected only that fixture to provide an empty blocker list so it
  reaches the missing-report check. Original logs/receipt retained.
- `green02`: **15/15 PASS**, native exit 0, no capture errors, no disk breach,
  Idle priority, affinity mask 4 (logical CPU 2), one worker. Full protected-root
  list passed unchanged to the branch-local safety launcher. Slot then released.

Cases cover original byte/hash preservation, both checksum manifests, no gate-ready
status, reused output refusal, corrupted input, traversal, Windows case collisions,
missing blockers, writes outside D:/a10, real owned symlink refusal, missing actual
reports, missing game IDs, fixture scope, missing fault points, wrong resumed MD5,
and attempts to substitute a baseline file as its resumed output.

Structured self-review checked bounded JSON parsing/copying, all three fault
points, independently stored resumed outputs, report/evidence hash binding, and
workspace/free-space reservations. Independent parent review remains required.
The test that supplies a synthetic actual-adapter envelope tests the checker
contract only; its fixture logs explicitly do not establish native execution.

Sealer SHA256: `ad9da2101fd0d9929ec931745e1e471773ee0325366acdd43389d54bc41cab09`.

Re-run only in a free authorized CPU slot, preserving previous evidence:

```powershell
powershell -NoProfile -File D:\a10\wt\astra_r10\job1\pack-tests\run_tests.ps1 -Tag green03
```

No git commit was made by this subagent. Main agent owns review, ledger update,
explicit file staging and push.
