#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job24
root=/workspace/work/sol3-job24
net=/workspace/work/sol3-job4-net/net768.fnn3
fixture=forge-combo29/sol3/job23/step1/positions.tsv
fixture_pin=e7100aae3c0a8ac1a9966fb8d746ec9511bbd63513ef4ecea99bd38b6255dfae
case "$1" in
    known) build=A-kF2; phase=step2; fixture=forge-combo29/sol3/job19/positions.txt;
           fixture_pin=3c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521 ;;
    wrong2) build=A-wrong2; phase=step2 ;;
    new-blind) build=A-kF2-blind; phase=step2 ;;
    old-blind) build=A-kF-blind; phase=step2 ;;
    r1|r2) build=A-kF2; phase=step3 ;;
    *) exit 2 ;;
esac
part=$1
label=${2:-$part}
if [[ "$part" == old-blind || "$part" == r1 || "$part" == r2 ]]; then
    test "$(git log -1 --format=%s -- "$job/prediction.md")" = 'sol3 job 24 prediction'
    rg -Fq 'Prediction published before old-blind and R2' "$job/stamps.txt"
fi
if [[ "$part" == r2 ]]; then
    test -s "$job/step3/k2_gate.json"
fi
engine="$root/build/$build/forge"
pin=$(awk 'NR==1 {print $1}' "$root/build_logs/$build/result.txt")
out="$root/raw/$label"
pub="$job/$phase/$label"
mkdir -p "$root/raw" "$job/$phase"
mkdir "$pub"
claim=$(awk 'NR==1 {print $1}' "$job/stamps.txt")
cutoff=$(($(date -u -d "$claim" +%s) + 3000))
remaining=$((cutoff - $(date -u +%s)))
args=(python3 -B "$job/run_matrix24.py" --part "$part" --engine "$engine" --engine-sha256 "$pin"
      --fixture "$fixture" --fixture-sha256 "$fixture_pin" --net "$net" --output "$out")
export ASAN_OPTIONS=detect_leaks=1:halt_on_error=1
export UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1
export PYTHONPATH=/workspace/work/sol3-replay/python
{
    printf 'ASAN_OPTIONS=%q\nUBSAN_OPTIONS=%q\nPYTHONPATH=%q\n' "$ASAN_OPTIONS" "$UBSAN_OPTIONS" "$PYTHONPATH"
    printf '%q ' "${args[@]}"
    printf '\n'
} > "$pub/invocation.txt"
run_code=124
if ((remaining > 0)); then
    run_code=0
    began_ns=$(date -u +%s%N)
    timeout --foreground --kill-after=8s "$remaining" "${args[@]}" \
        > "$out.driver.stdout.txt" 2> "$out.driver.stderr.txt" || run_code=$?
    finished_ns=$(date -u +%s%N)
    printf 'start_epoch_ns %s\nfinish_epoch_ns %s\nelapsed_ns %s\n' "$began_ns" "$finished_ns" "$((finished_ns - began_ns))" > "$pub/time.txt"
fi
printf 'driver exit %s\n' "$run_code" > "$pub/driver.status.txt"
if [[ -d "$out" ]]; then
    inputs=()
    copies=()
    for stream in "$out"/process-*/*.txt; do
        [[ -f "$stream" ]] || continue
        process=$(basename "$(dirname "$stream")")
        kind=$(basename "$stream" .txt)
        name="$process-$kind"
        inputs+=(--input "$name=$stream")
        if [[ "$kind" != stderr && "$phase" == step2 ]]; then copies+=(--copy-small "$name"); fi
    done
    if (("${#inputs[@]}")); then
        python3 -B "$job/retain.py" retain --out "$pub/streams" "${inputs[@]}" "${copies[@]}"
    fi
    for name in summary.json rows.tsv games.tsv blind.tsv; do
        if [[ -f "$out/$name" ]]; then cp "$out/$name" "$pub/$name"; fi
    done
fi
if [[ -f "$out.driver.stderr.txt" ]]; then cp "$out.driver.stderr.txt" "$pub/driver.stderr.txt"; fi
printf '%s %s %s driver exit %s, raw streams retained locally with receipt\n' "$(date -u +%FT%TZ)" "$phase" "$label" "$run_code" >> "$job/stamps.txt"
python3 -B "$job/retain.py" check --root "$job" > "$root/$label.size-check.json"
git add -- "$job"
git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
git commit -m "sol3 job 24 $phase record $label raw evidence"
bash /workspace/work/sol3-job3/push-checkpoint.sh
exit "$run_code"
