#!/usr/bin/env bash
set -euo pipefail
phase=${1:?provide controls, T1 or T2}
case "$phase" in
    controls) labels=(K24a K24b C24); proofs=(K24.txt K24.json C24.txt C24.json) ;;
    T1) labels=(T1-r15d T1-kF); proofs=(T1.txt T1.json T1.cmp.txt) ;;
    T2) labels=(T2-r15d T2-kF); proofs=(T2.txt T2.json T2.cmp.txt) ;;
    T2-observed) labels=(T2-observed-r15d T2-observed-kF); proofs=(T2-observed.txt T2-observed.cmp.txt) ;;
    *) exit 2 ;;
esac
scratch=/workspace/work/sol-job34
repo=/workspace/work/sol-job1/repo
target=forge-combo29/sol/job34
cd "$repo"
test "$(git branch --show-current)" = for-fable-and-opus/sol-work
test -z "$(git status --short)"
mkdir -p "$target/raw"
for label in "${labels[@]}"; do
    python3 - "$scratch/raw/$label.records.txt" <<'PY'
from hashlib import file_digest
import json
from pathlib import Path
import sys
records = Path(sys.argv[1])
meta = json.loads(records.with_suffix(records.suffix + '.meta').read_bytes())
with records.open('rb') as stream:
    assert file_digest(stream, 'sha256').hexdigest() == meta['records_sha256']
PY
    cp "$scratch/raw/$label".{records.txt,records.txt.meta,run.txt} "$target/raw/"
done
for proof in "${proofs[@]}"; do cp "$scratch/$proof" "$target/"; done
printf '%s %s raw records and metadata checked\n' "$(date -u +%FT%TZ)" "$phase" >> "$target/stamps.txt"
git add --sparse -- "$target"
git diff --cached --check
git diff --cached --name-only | awk '!/^forge-combo29\/sol\/job34\// {print; bad=1} END {exit bad}'
test -z "$(find "$target" -type f -size +20000000c -print -quit)"
git -c core.hooksPath=/dev/null -c user.name=sol -c user.email=sol@users.noreply.github.com commit -m "Sol Job 34 publish $phase records"
git rev-parse HEAD > "$scratch/$phase.commit"
GIT_TERMINAL_PROMPT=0 git -c core.hooksPath=/dev/null push origin HEAD:refs/heads/for-fable-and-opus/sol-work
test "$(git ls-remote --exit-code origin refs/heads/for-fable-and-opus/sol-work | cut -f1)" = "$(cat "$scratch/$phase.commit")"
date -u +%FT%TZ > "$scratch/$phase.push.stamp"
test -z "$(git status --short)"
