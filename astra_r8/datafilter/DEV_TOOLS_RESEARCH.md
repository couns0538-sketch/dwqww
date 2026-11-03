# Additional developer-tool investigation — UNPROVEN

Checked 2026-11-03; the latest extension schedules final review at 08:23–09:23 UTC.
The work is Python conversion/filtering and proof handling. New C++ builds,
sanitizer campaigns against modified engine code, training, GPU profiling and
loader work remain outside scope. A plugin can supply access or workflow; its
presence does not establish correctness.

## Selected tools and actual availability

| Tool | Concrete value here | Observed state and decision |
|---|---|---|
| CodeRabbit | Another review of a frozen code diff, especially parsing, publication and evidence assumptions | Signed native Windows CLI 0.9.2; authentication succeeds. Usage reports 10 included reviews remaining and usage billing inactive. Reserve a scoped review for the final hour; no paid-credit override. No review has run yet. |
| Ruff | Offline detection of undefined names, suspicious control flow and common Python mistakes | Existing pinned environment contains 0.16.0. Ran explicit F/B/PLE/PLW/S rules, one Rayon worker, no cache or fixes. 345 observations require triage; most are test assertions, non-security MD5/random usage and checked subprocesses. |
| Hypothesis | Generate combinations of legal move histories, mirrored labels, malformed metadata and PGN whitespace; shrink failures to useful fixtures | Version 6.170.14 isolated with sortedcontainers 2.4.0. All 1,200 generated examples PASS on pre-fix source (400 per property), deterministic settings, no database. No installed npt package changed. |
| Coverage.py | Find failure branches the existing tests do not execute; distinguish branch coverage from line coverage | Version 7.17.0 isolated beside Hypothesis. All 344 tests + 11 subtests pass in 390.47 seconds with branch tracing; 71% measured main-process coverage, including audit utilities. Earlier standalone audits and untraced child execution are outside this measurement. |
| Pyright (MIT) | Inspect optional values, call signatures and metadata interfaces | Isolated 1.1.414, verified public npm archive, existing Node with serial type checking. Actual scope: 23 files, 30 diagnostics, 5.434 seconds. Focused review found typing/interface limitations rather than a reachable runtime defect; dispositions are retained in evidence/extension3h/pyright_actual/TRIAGE.md. |
| Context7 | Resolve exact documentation/API questions before writing tests or integration code | Connected. The reused research reviewer checked Hypothesis settings through its documentation tools. It is documentation support, not a validator. |
| GitHub | Read current crew issues, PR feedback and CI status against exact commits | Connected; local git remains the publication path. Do not post review messages without authorization. |

Ruff's assertions warning revealed a real false PASS on deliberately corrupted
audit inputs under Python optimization. Six failing regressions preceded the
explicit-exception repair; 16 optimized/normal positive and negative checks now
pass, and independent review approved full verification. Its late-bound closure warnings in resource
tests refer to functions invoked before the next loop iteration; they are not
automatically defects. Subprocess calls already inspect return codes explicitly.
MD5 is retained only to compare existing producer sidecars, alongside SHA256.
Randomness is seeded sampling, not cryptography. No mass automatic fixes or
formatting changes are planned.

The tool directory is `C:/astra8_data/extension3h_20261103/python_tools`.
Downloads and extracted files retain complete package licences; total expanded
size is 3,015,717 bytes. Hashes and source URLs are in `tools_install.json` at that
artifact root. The pinned Python has no pip: no bootstrap or package-manager
change was made. Exact PyPI wheels were SHA256-verified and extracted with path
validation and exclusive writes. Coverage's inspected `.pth` file is inert:
only an explicit import path is used, never `site.addsitedir` or installation
into the existing environment. The first rejected extraction was retained.

Operational detail: database=None does not disable Hypothesis's other caches.
The first run created an owned `.hypothesis` cache in the worktree; after checking
its resolved path, creation times and absence of reparse points, it was preserved
as `hypothesis_cache_initial` under the C: artifact root. Subsequent harnesses set
HYPOTHESIS_STORAGE_DIRECTORY before importing Hypothesis. No dataset was moved.

Hypothesis is MPL-2.0 and remains a separate test tool; its implementation is
not copied into Forge, the adapter or repository. Coverage.py and
sortedcontainers are Apache-2.0; Ruff is MIT. Tests and audit harnesses authored
for this task are original code. This is separate from the user's prohibition
on copying GPL/AGPL engine/training implementations.

## Evaluated but not installed

| Tool | Potential use | Decision for this run |
|---|---|---|
| mutmut | Check whether tests detect deliberately changed operators and control flow | Official requirements demand fork support, hence WSL on Windows. Do not change this machine's execution environment for it; the existing targeted fault-injection tests already exercise the confirmed audit risk. |
| Semgrep CE | Original rules for unsafe deserialization, shell execution and output publication patterns; has a CLI/MCP interface | Native Windows is supported. Engine and rule licences are separate; no implementation/rules are copied. More setup than the available Ruff check, so deferred unless a specific remaining risk needs it. |
| CodeQL | Cross-function security queries over Python/C++ | Requires a CodeQL database and applicable GitHub licensing. No new CI workflow, repository setting or database is created here. Reconsider for a separate repository-wide security job. |
| SonarQube | Additional static analysis and project issue tracking | CLI 1.11.0 installed, but user reports authentication failed; no analysis claimed. It does not block these other checks. |

Plugin Management searches for coding/testing/static-analysis tools returned
the already connected GitHub, Context7 and Superpowers integrations, plus
unrelated application tools. No useful additional unconnected plugin was
identified in those bounded results; this is not an exhaustive marketplace
claim. CLI tools can provide the missing checks without another plugin.

## Primary references

- [CodeRabbit CLI scopes, authentication and billing consent](https://docs.coderabbit.ai/cli)
- [CodeRabbit review configuration](https://docs.coderabbit.ai/reference/configuration)
- [Ruff configuration and explicit rule selection](https://docs.astral.sh/ruff/configuration/)
- [Ruff rule catalogue](https://docs.astral.sh/ruff/rules/)
- [Hypothesis settings and determinism](https://hypothesis.readthedocs.io/en/latest/reference/api.html)
- [Hypothesis example-count limitations](https://hypothesis.readthedocs.io/en/latest/explanation/test-case-count.html)
- [Hypothesis stateful testing and when ordinary generated tests suffice](https://hypothesis.readthedocs.io/en/latest/stateful.html)
- [Hypothesis licence](https://github.com/HypothesisWorks/hypothesis/blob/master/LICENSE.txt)
- [Coverage.py branch measurement](https://coverage.readthedocs.io/en/latest/branch.html)
- [Pyright installation](https://github.com/microsoft/pyright/blob/main/docs/installation.md)
- [mutmut platform requirements](https://mutmut.readthedocs.io/en/latest/)
- [Semgrep CLI, local scanning and MCP](https://docs.semgrep.dev/cli-reference)
- [CodeQL CLI capabilities and licence eligibility](https://docs.github.com/en/code-security/concepts/code-scanning/codeql/codeql-cli)
- [Context7 documentation service](https://context7.com/docs/overview)

All tool findings require reproduction and assessment. Passing checks here
cannot establish Elo, NNUE quality, full-corpus historical reachability or
training throughput. Crew strength gates remain required: **UNPROVEN**.
