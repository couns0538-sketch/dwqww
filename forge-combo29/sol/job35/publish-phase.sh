#!/usr/bin/env bash
set -euo pipefail
phase=${1:?provide controls, U1 or U2}
case "$phase" in
    controls) labels=(K25a K25b C25); proofs=(K25.txt K25.json C25.txt C25.json whole_games35.py compare_games35.py run-measured.sh) ;;
    U1) labels=(U1-r15d U1-kF); proofs=(U1.txt U1.json U1.cmp.txt U1.openings-cmp.txt) ;;
    U2) labels=(U2-r15d U2-kF); proofs=(U2.txt U2.json U2.cmp.txt U2.openings-cmp.txt) ;;
    *) exit 2 ;;
esac
scratch=/workspace/work/sol-job35
repo=/workspace/work/sol-job1/repo
target=forge-combo29/sol/job35
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
git diff --cached --name-only | awk '!/^forge-combo29\/sol\/job35\// {print; bad=1} END {exit bad}'
test -z "$(find "$target" -type f -size +20000000c -print -quit)"
git -c core.hooksPath=/dev/null -c user.name=sol -c user.email=sol@users.noreply.github.com commit -m "Sol Job 35 publish $phase records"
git rev-parse HEAD > "$scratch/$phase.commit"
GIT_TERMINAL_PROMPT=0 git -c core.hooksPath=/dev/null push origin HEAD:refs/heads/for-fable-and-opus/sol-work
test "$(git ls-remote --exit-code origin refs/heads/for-fable-and-opus/sol-work | cut -f1)" = "$(cat "$scratch/$phase.commit")"
date -u +%FT%TZ > "$scratch/$phase.push.stamp"
test -z "$(git status --short)"
