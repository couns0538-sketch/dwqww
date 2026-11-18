#!/usr/bin/env bash
set -euo pipefail
root=/workspace/work/sol3-job6
job=forge-combo29/sol3/job6
net=/workspace/work/sol3-job4-net/net768.fnn3
cutoff=$(date -u -d 2026-11-18T11:02:40Z +%s)
mkdir "$root/stage4b" "$root/tree_hlm_search"
cp -a "$root/tree_12/." "$root/tree_hlm_search/"
cp "$root/run_hlm_search.sh" /workspace/work/sol3-job6-hlm/hlm_search_probe.diff "$job/"
python3 - "$job" <<'PY'
import difflib
from pathlib import Path
import sys
job=Path(sys.argv[1]); original=(job/'driver_final.py').read_text()
replacements={
    '                hlm_counts = None\n': '                hlm_counts = None\n                hlm_raw = None\n',
    '                            hlm_counts = dict(zip': '                            hlm_raw = detail\n                            hlm_counts = dict(zip',
    'record.update(hlm=hlm_counts, hlm_first_mismatch=hlm_first)': 'record.update(hlm=hlm_counts, hlm_raw=hlm_raw, hlm_first_mismatch=hlm_first)',
}
text=original
for needle,replacement in replacements.items():
    assert text.count(needle)==1,needle
    text=text.replace(needle,replacement)
(job/'driver_hlm.py').write_text(text)
(job/'driver_hlm_evidence.diff').write_text(''.join(difflib.unified_diff(original.splitlines(keepends=True), text.splitlines(keepends=True), fromfile='a/driver_final.py', tofile='b/driver_hlm.py')))
PY
status=0
{
  date -u +%FT%TZ
  LC_ALL=C patch -d "$root/tree_hlm_search" -p1 -F0 --batch --forward -i "$(realpath "$job/hlm_probe.diff")" || status=$?
  if [ "$status" -eq 0 ]; then
    LC_ALL=C patch -d "$root/tree_hlm_search" -p1 -F0 --batch --forward -i "$(realpath "$job/hlm_search_probe.diff")" || status=$?
  fi
} > "$job/hlm_search.patch.stdout.txt" 2>&1
if rg -qi 'offset|fuzz|FAILED|reject|Skipping|Reversed' "$job/hlm_search.patch.stdout.txt"; then status=21; fi
remaining=$((cutoff-$(date -u +%s)))
if [ "$status" -eq 0 ] && ((remaining>0)); then
  timeout --kill-after=5s "$remaining" bash /workspace/work/sol3-job3/build_one.sh "$root/tree_hlm_search" "$root/build_hlm_search" "$job/hlm_search.build.stdout.txt" || status=$?
elif [ "$status" -eq 0 ]; then status=124; fi
date -u "+%Y-%m-%dT%H:%M:%SZ Step 4b instrumented k12 build exited $status" >> "$job/stamps.txt"
git add --sparse -- "$job/"
git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
git -c user.name=sol3 -c user.email=sol3@users.noreply.github.com commit -qm 'sol3 job 6 step 4b checkpoint instrumented k12 build'
test "$status" -eq 0
trace="$root/stage4b/hlm.trace.jsonl"
exe="$root/build_hlm_search/forge"
args=(--engine "$exe" --net "$net" --games 60 --softnodes 2000 --random-plies 8 --max-plies 300 --seed 20261117 --json --trace "$trace" --hlm)
{
  printf 'python3 -B %q' "$job/driver_hlm.py"
  printf ' %q' "${args[@]}"
  printf '\n'
  sha256sum "$exe" "$net" "$job/driver_hlm.py"
  printf 'uci\nquit\n' | "$exe" | sed -n '/^id name /p'
  date -u +%FT%TZ
} > "$job/hlm_search.meta"
remaining=$((cutoff-$(date -u +%s)))
if ((remaining>0)); then
  timeout --kill-after=5s "$remaining" python3 -B "$job/driver_hlm.py" "${args[@]}" > "$job/hlm_search.json" 2> "$job/hlm_search.stderr.txt" || status=$?
else status=124; fi
if [ "$status" -eq 0 ]; then
  python3 -B "$job/trace_tools.py" compare "$root/stage2/arm_12.trace.jsonl" "$trace" > "$job/hlm_search.first_difference.json"
  python3 - "$job" "$trace" "$root/stage4b/hlm_raw.tsv" <<'PY' > "$job/hlm_search.gate.txt" 2> "$job/hlm_search.gate.stderr.txt" || status=$?
import collections,json,re,sys
from pathlib import Path
job,trace,raw=map(Path,sys.argv[1:])
a=json.loads((job/'arm_12.json').read_text());b=json.loads((job/'hlm_search.json').read_text())
keys=('searches','total_nodes','trace_fnv1a64','terminal','final_sum','at_cap','final_fnv1a64')
pattern=re.compile(r'info string hlm calls=(\d+) incheck=(\d+) nomove=(\d+) mismatch=(\d+)')
totals=collections.Counter()
count=0
with trace.open() as inp, raw.open('w') as out:
    for line in inp:
        row=json.loads(line)
        signal=row['hlm_raw']
        match=pattern.fullmatch(signal)
        assert match, row
        for name,number in zip(('calls','incheck','nomove','mismatch'),map(int,match.groups())):
            totals[name]+=number
        out.write(f"{row['game']}\t{row['ply']}\t{signal}\n")
        count+=1
assert count==b['searches']
assert all(b['hlm'][k]==v for k,v in totals.items())
print('Raw HLM lines:',count)
print('Independent exact HLM sums:',dict(totals))
print('Measurement identity:',{key:b[key] for key in keys})
print('First mismatch:',b['hlm']['first_mismatch'])
assert all(a[key]==b[key] for key in keys), 'HLM search probe changed the workload'
assert totals['mismatch']==0
print('Step 4b gates PASS')
PY
  if test -s "$root/stage4b/hlm_raw.tsv"; then
    mkdir "$job/hlm_raw"
    split -l 1400 -d -a 2 --additional-suffix=.txt "$root/stage4b/hlm_raw.tsv" "$job/hlm_raw/counters-"
    sha256sum "$root/stage4b/hlm_raw.tsv" >> "$job/hlm_search.meta"
  fi
fi
printf 'exit_code %s\n' "$status" >> "$job/hlm_search.meta"
date -u "+%Y-%m-%dT%H:%M:%SZ Step 4b warm full-generator search comparison and readback exited $status" >> "$job/stamps.txt"
git add --sparse -- "$job/"
git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
git -c user.name=sol3 -c user.email=sol3@users.noreply.github.com commit -qm 'sol3 job 6 step 4b preserve the full warm HLM audit and counters'
cat "$job/hlm_search.json" "$job/hlm_search.stderr.txt"
test "$status" -eq 0
