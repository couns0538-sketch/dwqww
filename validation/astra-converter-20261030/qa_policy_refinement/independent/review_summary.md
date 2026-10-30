# Independent policy review

No source edits or commits. All test artifacts remain under this directory.

## Corrected defects

1. Launcher initially rejected valid `engtype_3D` names because its identity regex required an alphabetic first type character. The latest source accepts 3D; portable regex/source checks pass. PowerShell runtime is unavailable, so Windows behavior remains unverified.
2. Runtime policy initially treated the empty managed `/tmp/.git` directory as a repository. The shared helper now recognizes actual Git metadata, and the independent positive external-executable case passes.
3. Runtime policy initially normalized `..` before resolving symlinks. A synthetic `outside/link/../adapter` passed policy for an outside executable but invoked the adapter inside a repository before failing a late identity check. Original proof remains in `symlink_dotdot_execution.json`. Fresh-process verification of the corrected helper rejects the real repository target before executable invocation or output-directory creation. Bare repositories are also rejected.

## Verification

- `data2_final.log`: 110 tests, OK, 13 native GPL-adapter tests skipped because the opt-in external adapter was not configured.
- `audit_tests.log`: 25 audit tests, OK; default retained/queryable indexes, explicit pruning, prior-evidence preservation, and failed final identity checks covered.
- `launcher_source_final.log`: 5 portable source/documentation checks, OK.
- `final_adversarial_report.json`: independent external allow, bare Git rejection, symlink/.. rejection, no prohibited invocation, no output writes. Includes exact converter/helper/launcher hashes.
- No grok-pc or GPU access. No native PowerShell execution.

## Documentation requiring owner update at review time

`docs/ASTRA_CONVERTER_20261030.md` around lines 326–329 claims only one completed working index exists and that indexes are no longer retained 37 times; line 347 says a verified resume replaces retained interrupted indexes. Defaults now retain all indexes. Storage-planning claims must be conditional on explicit `verify --prune-indexes`, with current resume behavior described accurately. Related statements occur around lines 113 and 267. Owner notified.

## Final follow-up

Fresh-read converter documentation now correctly states default index retention, explicit opt-in cleanup, and historical measurement scope. No outstanding documentation defect from the findings above. Launcher source re-review confirms per-physical-engine grouping and threshold/snapshot logic, Python flag clusters and case-sensitive interpreter options; no additional concrete defect identified. `launcher_regex_grouping_review.json` replays extracted regex/grouping semantics only, not Windows execution.
