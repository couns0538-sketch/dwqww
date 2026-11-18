#!/usr/bin/env bash
set -euo pipefail
root=/workspace/work/sol3-job6
job=forge-combo29/sol3/job6
old=forge-combo29/sol3/job4
positions=forge-combo29/sol3/job3/positions.txt
net=/workspace/work/sol3-job4-net/net768.fnn3
cutoff=$(date -u -d 2026-11-18T11:02:40Z +%s)
mkdir "$root/stage3"
cp "$root/run_k12_matrix.sh" "$job/"
for cell in B2 B3 N2 N3 ND; do
  out="$root/stage3/$cell"
  mkdir "$out"
  status=0
  # The unmodified Job 4 harness accepts the label 11, which only names its outputs.
  args=("$root/build_12/forge" "$positions" "$out" 11 "$cell")
  if [[ "$cell" = N* ]]; then args+=(--net "$net"); fi
  remaining=$((cutoff - $(date -u +%s)))
  {
    printf 'k12 command using Job 4 harness output label 11\npython3 -B %q' "$old/identity.py"
    printf ' %q' "${args[@]}"
    printf '\n'
    sha256sum "$root/build_12/forge" "$positions"
    date -u +%FT%TZ
    if (( remaining > 0 )); then
      timeout --kill-after=5s "$remaining" python3 -B "$old/identity.py" "${args[@]}" || status=$?
    else
      status=124
    fi
  } > "$out/run_12_${cell}.txt" 2> "$out/run_12_${cell}.stderr.txt"
  for file in "$out/"*; do
    name=$(basename "$file")
    cp "$file" "$job/${name/_11_/_12_}"
  done
  if [ "$status" -eq 0 ]; then
    python3 - "$old" "$job" "$cell" <<'PY' > "$job/k12_${cell}_compare.txt" 2> "$job/k12_${cell}_compare.stderr.txt" || status=$?
from pathlib import Path
import hashlib,re,sys
old,new=map(Path,sys.argv[1:3]);cell=sys.argv[3]
r1=(old/f'rows_11_{cell}.txt').read_bytes()
r2=(new/f'rows_12_{cell}.txt').read_bytes()
rows1,rows2=r1.splitlines(),r2.splitlines()
print('rows k11', len(rows1), hashlib.sha256(r1).hexdigest())
print('rows k12', len(rows2), hashlib.sha256(r2).hexdigest())
print('row matches', sum(x==y for x,y in zip(rows1,rows2)), 'of', len(rows1))
if r1!=r2:
    for a,b in zip(rows1,rows2):
        if a!=b:
            print('first difference', repr(a), repr(b));break
assert len(rows1) == 389 and r1==r2
if cell in ('B3','N3'):
    pattern=re.compile(rb'^info string softnodes nodes (\d+)$',re.M)
    totals1=pattern.findall((old/f'identity_11_{cell}.stdout.txt').read_bytes())
    totals2=pattern.findall((new/f'identity_12_{cell}.stdout.txt').read_bytes())
    print('soft final totals match', sum(a==b for a,b in zip(totals1,totals2)), 'of', len(totals1))
    assert len(totals1)==389 and totals1==totals2
PY
  fi
  date -u "+%Y-%m-%dT%H:%M:%SZ Step 3 k12/$cell engine and k11 readback exit $status" >> "$job/stamps.txt"
  git add --sparse -- "$job/"
  git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
  git -c user.name=sol3 -c user.email=sol3@users.noreply.github.com commit -qm "sol3 job 6 step 3 checkpoint k12 $cell"
  if test -f "$job/k12_${cell}_compare.txt"; then cat "$job/k12_${cell}_compare.txt"; fi
  test "$status" -eq 0
done
