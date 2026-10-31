# Offline evidence checker

Run through Python 3.10 or newer; no third-party packages are required:

```bash
python /path/to/plugin/skills/cpp-chess-engineering/scripts/check_evidence.py /path/to/record.json
```

The checker only reads the nominated record/files and prints JSON. It does not execute commands, contact a service, change the repository or write output. If saving stdout, choose a new evidence path; shell redirection is outside the checker's no-overwrite guarantee.

Schema 1 fields:

| Field | Required content |
|---|---|
| `schema` | Integer 1 |
| `kind` | `correctness`, `exact-speed` or `strength` |
| `baseline`, `candidate` | Objects with `commit` (full 40-hex Git SHA-1) and nonempty `artifacts` lists |
| Artifact/evidence reference | Object with `path` (relative forward-slash path, based on record parent) and `sha256` (64 hex digits) |
| `checks` | Nonempty list of unique named objects; `name`, `status` (`PASS`, `FAIL`, `UNVERIFIED`) |
| `checks[].evidence` | Required reference for PASS/FAIL; optional for UNVERIFIED |
| `bench` | Required for exact-speed; `expected`, `baseline`, `candidate` maps with identical nonempty depth keys and nonnegative integer node counts |

Relative paths may include `../`; nominate only authorized artifacts. Absolute, drive-qualified, UNC and backslash paths are rejected so spelling is portable. Hashes stream through bounded buffers and file identity is checked around reads; ctime participates only on POSIX. This catches ordinary changed files, not all possible malicious concurrent rewrites. Commits are syntax-checked, not resolved through Git. Record real source/net/build artifacts and original logs; a plausible SHA or a log labelled PASS does not establish provenance by itself.

Bench depths are decimal strings such as `"11"`. Supply pins from the *current* baseline contract; values are never copied from the binary being qualified. The checker compares both supplied baseline and candidate vectors to those pins. It does not extract nodes or timing from arbitrary engine output. Include the original bench transcript as check evidence and independently confirm the transcription.

Exit 0/PASS means the declared check statuses, hashes and supplied pins are internally consistent. Exit 1/FAIL means a hash/artifact or declared qualification check failed/was unverified, or an explicit node pin differs. Exit 2/INVALID means the record cannot express a valid check: missing required data, malformed digest, mismatched vector keys, duplicate JSON keys, nonfinite numbers, boolean node counts, etc. A malformed path is INVALID; a missing referenced file is FAIL.

`strength_claim` is always `UNVERIFIED`, including `kind="strength"`. This tool never parses Fastchess LLR, authenticates PGNs or estimates Elo. A PASS does not prove a repaired bug, actual platform execution, a speedup, or a match result. Use the existing engine validator and original runner evidence for those judgments.

The tests create actual fixture files, alter bytes, remove references, change pins and exercise exit codes. Fixtures are not engine experiment results. Run all plugin tests with:

```bash
python -W error::ResourceWarning -m unittest discover -s /path/to/plugin/tests -v
```
