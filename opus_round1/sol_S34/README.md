# S34 gate-manifest validator v2

`forge_sol_S34_validate_manifest_v2.py` audits a forge gate manifest (`forge_gates.json`) offline and read-only.
It needs Python 3.10+ and the standard library only, prints one JSON report to stdout and writes no file.

```sh
python -I -B forge_sol_S34_validate_manifest_v2.py <forge_gates.json>            # deployed-driver profile (default)
python -I -B forge_sol_S34_validate_manifest_v2.py <forge_gates.json> --strict   # Sol's strict profile
```

Exit status: 0 no findings, 1 findings, 2 the file could not be read as a manifest. Every finding has a code, a
JSON pointer and a message. A UTF-8 BOM is accepted (the live file has one). Run it on a copy of the live file,
not on the file the gate driver uses, if the driver may write while you read.

## Profiles
- **Default (deployed driver).** Fields the deployed `forge_queue.ps1` (sha256 `636b6cca…`) defaults may be absent:
  `tc` → 10+0.1 (line 89), `concurrency` → 5 (line 90), `openings_start` → 1 (line 92), `sprt` → [0,10],
  nonreg false (lines 94-97). A field that is present is never filled: it must be valid as written. Uniqueness of
  `srand` and of the effective `openings_start` applies to every gate, held and dropped ones included.
  `--driver-defaults` is accepted as an alias.
- **Strict (`--strict`).** Every gate states `tc`, `sprt`, `openings_start` and `concurrency` explicitly (Sol's v1
  default).

## Rules added in v2 (Sol's v1 rules are kept)
| code | rule | source |
|---|---|---|
| `JSON_CASE_DUPLICATE_KEY` | object keys that differ only in case | driver reads with `ConvertFrom-Json` (line 37), case-insensitive names |
| `OPTIONS_SHAPE`, `OPTION_FORMAT`, `OPTION_CONTROL_CHAR` | gate `options` is a list of strings matching `^option\.([^=]+)=(.*)$` in full, no control characters | driver line 216 |
| `OPTION_DUPLICATE` | an option name twice (case-insensitive) | UCI names are case-insensitive |
| `OPTION_RESERVED` | `Threads`, `Hash`, `OwnBook` in gate options | driver sets them itself (line 350) |
| `BASE_OPTIONS_IGNORED` | non-empty `options` in `base` / `base_override` (also inside `ag_prev`) | driver passes no base options (line 351) |
| `ANNOTATION_TYPE` | `ag_vs_lock`, `ag_rebuilt_on`, `ag_rebase_of`, `ag_void_rerun_of`, `ag_void_cause` nonempty strings; `ag_rebase_exempt24`, `pooled` booleans | `autonomy/autopromote.ps1` (sha256 `896663b0…`) lines 187, 266, 408, 439, 452 |
| `AG_PREV_SHAPE` + nested checks | `ag_prev` is an object with only `exe`, `sha256`, `prebench`, `base_override`, `srand`, `ag_vs_lock`; its `srand` is not part of the uniqueness rule | autopromote line 453 |

These annotation fields were Sol's v1's 123 false `UNSUPPORTED_FIELD` findings on the live file.

## Files
- `forge_sol_S34_validate_manifest_v2.py` — the validator.
- `make_bad_manifests_v2.py` — writes `bad_manifests_v2/`: a valid manifest (plain and with BOM) and 51 bad
  manifests with one planted defect each, plus `index.json` (file, code, explaining message text, profile).
  Deterministic (`logs/step3_fixtures.log`). Sol's 29 v1 fixtures were never pushed, so they were rebuilt.
- `test_validate_manifest_v2.py` — Sol's 21 tests ported (profile made explicit) + 10 v2 tests. Set `S34_SNAPSHOT`
  (lock-archive snapshot) and `S34_LIVE` (read-only copy of the live file) to run the two real-file tests.
- `mutation_check_v2.py` — 10 planted validator bugs; each must fail the tests.
