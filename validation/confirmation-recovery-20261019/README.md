# Original confirmation evidence recovery

This is a bounded data recovery job for completed run `39332822379`, original
attempt 1, head `f1b44cc71554e8ea1ec61b3ca6adc90da65646b6`, job `118334929163`.
It does not rerun a match, build, engine, or downloaded script. Nothing in this
package has been pushed or launched by its preparation agent.

The original match step succeeded at `2026-10-19T22:44:49Z` and original raw
artifact upload succeeded at `22:44:53Z`. The later results-branch step failed.
Its precise cause remains unknown pending review of the original log; the
public artifact's displayed 19.3 MB size does not establish a Git file-size
failure.

Only original artifact `12226439147`, named
`forge-hosted-confirmation-39332822379-1`, is requested. The frozen original
ZIP SHA256 is
`1dc3d43767bc95251acdf2ec363e4e79b8a00e15d16b1fbd3202ec644b9a5600`.
Official artifact/run/job REST JSON must agree on the frozen identities, head,
digest, original step outcomes and timestamps before either original download.
The standard `${{ github.token }}` is used only by official API/action routes;
bearer headers are stripped on redirects and signed URLs are not recorded.

The official REST ZIP download retains original archive bytes, while the pinned
official download action retrieves that same sole artifact into a separate
directory. The extracted files must match every original ZIP payload byte.
The original job log is saved byte for byte before a separate derived excerpt
report is written. Log and ZIP retrieval are attempted independently. A log
failure still allows the action to retrieve the identified artifact, but blocks
Git publication. REST JSON, retrieval provenance, original downloads, extracted
files, recovery runner metadata and trusted recovery sources are all retained.

The frozen `.github/hosted-nnue-strength/archive_results.py` is unchanged at
SHA256 `952a090fee4f5ce67df93f5f389be5e46138f5b5787161c96156d80ad1fbaf6c`.
Its CLI accepts `--input`, `--out`, `--name`, and `--split-size`; successful
return includes `verify_archive()`. Schema 1 contains `format=raw-split-zip`,
whole-ZIP size/hash, ordered physical `parts`, `split_size`, `manifest_member`,
and each input file's relative path, size and SHA256. Verification reassembles
parts on disk, validates each part and the complete ZIP, compares internal and
external manifests, and hashes every uncompressed payload. The wrapper also
rejects symlinks/nonregular input nodes, compares the entire raw inventory, and
bounds the external manifest as well as all parts to 64 MiB.

The always-conditioned original-byte/metadata/archive upload occurs before Git
publication. Its direct paths cover trusted metadata/source copies and original
ZIP/log downloads. Extracted files are carried in the verified archive; the
uploader never globs the downloaded extraction tree, including when a rejected
symlink or nonregular node prevents archival. The original ZIP preserves those
source bytes on failure. The
job has a 15-minute limit; individual step budgets total 14 minutes, including
checkout, upload and publication. Only a verified manifest and its exact ZIP
parts are staged on an orphan results branch
`results/confirmation-recovery-39332822379-RECOVERYRUNID-ATTEMPT`. An existing
remote ref is refused; the ordinary non-force push cannot advance a different
existing orphan history. Results branch names cannot trigger recovery.

## Offline validation and root launch gate

Run from `/workspace/dwqww`:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B validation/confirmation-recovery-20261019/validate.py
```

This records exact subprocess argv, exit status, source hashes and full output
in `offline-checks.json` and `offline-checks.log`. Tests use mocked identities
and temporary synthetic data; every shell block is checked with `bash -n`
without executing its commands. The preparation agent performed no Git
mutation, network retrieval, engine run, push or hosted launch.

The launch gate is deliberately still
`PREPARED_PENDING_ROOT_REVIEW_AND_SINGLE_PUSH`. The root agent must review the
workflow and checks, then change only `protocol.json`'s status to
`REVIEWED_READY_FOR_SINGLE_PUSH`, rerun the command above, and checkpoint these
owned paths. This is internal root review; no user approval question is needed.
The code refuses metadata retrieval until that reviewed status is present.

Suggested exact root commands after review (not executed here):

```bash
python3 -B - <<'PY'
import json
from pathlib import Path
p = Path('validation/confirmation-recovery-20261019/protocol.json')
v = json.loads(p.read_text())
assert v['status'] == 'PREPARED_PENDING_ROOT_REVIEW_AND_SINGLE_PUSH'
v['status'] = 'REVIEWED_READY_FOR_SINGLE_PUSH'
p.write_text(json.dumps(v, indent=2) + '\n')
PY
PYTHONDONTWRITEBYTECODE=1 python3 -B validation/confirmation-recovery-20261019/validate.py
git add -- .github/workflows/forge-recover-confirmation.yml validation/confirmation-recovery-20261019
git commit -m "Prepare bounded original confirmation evidence recovery"
git ls-remote --exit-code origin refs/heads/forge/recover-confirmation-20261020-original-01
```

The final read-only command must report an absent ref (exit 2). Then launch
exactly once, with no rerun/reset/force option:

```bash
git push origin HEAD:refs/heads/forge/recover-confirmation-20261020-original-01
```

Confirm the launched workflow's recovery head, original source identity checks,
original ZIP digest, original log failure details, raw upload, verified manifest
and final results ref from actual CI evidence. No live recovery result or chess
strength conclusion is claimed by these offline checks.

Final root review: protocol is REVIEWED_READY_FOR_SINGLE_PUSH. The upload now
retains all of recovery-raw/ plus archived-results/, including extracted files
when original ZIP retrieval or archive construction fails. Earlier pending
status and subset-upload review notes above are historical. No games are rerun.
