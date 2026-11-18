#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job23
root=/workspace/work/sol3-job23
net=/workspace/work/sol3-job4-net/net768.fnn3
case "$1" in
    known) build=A-kF; fixture=forge-combo29/sol3/job19/positions.txt; phase=step2 ;;
    control) build=A-wrong; fixture="$job/step1/positions.tsv"; phase=step2 ;;
    r1|r2) build=A-kF; fixture="$job/step1/positions.tsv"; phase=step3 ;;
    *) exit 2 ;;
esac
part=$1
if [[ "$phase" == step3 ]]; then
    test -s "$job/step2/gate.json"
    test "$(git log -1 --format=%s -- "$job/prediction.md")" = 'sol3 job 23 prediction'
    rg -Fq 'Prediction published before Step 3' "$job/stamps.txt"
fi
label=${2:-$part}
engine="$root/build/$build/forge"
pin=$(awk 'NR==1 {print $1}' "$root/build_logs/$build/result.txt")
if [[ "$part" == known ]]; then
    fixture_pin=3c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521
else
    fixture_pin=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["files"]["positions.tsv"]["sha256"])' "$job/step1/receipt.json")
fi
out="$root/raw/$label"
pub="$job/$phase/$label"
mkdir -p "$root/raw" "$job/$phase"
mkdir "$pub"
claim=$(awk 'NR==1 {print $1}' "$job/stamps.txt")
cutoff=$(($(date -u -d "$claim" +%s) + 3000))
remaining=$((cutoff - $(date -u +%s)))
args=(python3 -B "$job/run_matrix.py" --part "$part" --engine "$engine" --engine-sha256 "$pin"
      --fixture "$fixture" --fixture-sha256 "$fixture_pin" --net "$net" --output "$out")
export ASAN_OPTIONS=detect_leaks=1:halt_on_error=1
export UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1
export PYTHONPATH=/workspace/work/sol3-replay/python
{
  printf 'ASAN_OPTIONS=%q\nUBSAN_OPTIONS=%q\nPYTHONPATH=%q\n' "$ASAN_OPTIONS" "$UBSAN_OPTIONS" "$PYTHONPATH"
  printf '%q ' "${args[@]}"
  printf '\n'
} > "$pub/invocation.txt"
code=124
if ((remaining > 0)); then
    code=0
    timeout --foreground --kill-after=8s "$remaining" "${args[@]}" > "$out.driver.stdout.txt" 2> "$out.driver.stderr.txt" || code=$?
fi
printf 'driver exit %s\n' "$code" > "$pub/driver.status.txt"
if [[ -d "$out" ]]; then
    inputs=()
    copies=()
    for stream in "$out"/process-*/*.txt; do
        [[ -f "$stream" ]] || continue
        process=$(basename "$(dirname "$stream")")
        kind=$(basename "$stream" .txt)
        name="$process-$kind"
        inputs+=(--input "$name=$stream")
        if [[ "$kind" != stderr && "$part" != r1 ]]; then copies+=(--copy-small "$name"); fi
    done
    if (("${#inputs[@]}")); then
        python3 -B "$job/retain.py" retain --out "$pub/streams" "${inputs[@]}" "${copies[@]}"
    fi
    for name in summary.json rows.tsv games.tsv; do
        if [[ -f "$out/$name" ]]; then cp "$out/$name" "$pub/$name"; fi
    done
fi
if [[ -f "$out.driver.stderr.txt" ]]; then cp "$out.driver.stderr.txt" "$pub/driver.stderr.txt"; fi
printf '%s %s %s driver exit %s, raw streams retained locally with receipt\n' "$(date -u +%FT%TZ)" "$phase" "$label" "$code" >> "$job/stamps.txt"
python3 -B "$job/retain.py" check --root "$job" > "$root/$label.size-check.json"
git add -- "$job"
git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
git commit -m "sol3 job 23 $phase record $label raw evidence"
bash /workspace/work/sol3-job3/push-checkpoint.sh
exit "$code"
