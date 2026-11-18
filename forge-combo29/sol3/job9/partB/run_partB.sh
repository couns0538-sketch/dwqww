#!/usr/bin/env bash
set -euo pipefail
work=/workspace/work/sol3-job9
job=forge-combo29/sol3/job9
part="$job/partB"
net=/workspace/work/sol3-job4-net/net768.fnn3
fixture="$part/position_stream.jsonl"
cutoff=$(date -u -d 2026-11-18T12:52:16Z +%s)
export PYTHONPATH=/workspace/work/sol3-job4-driver
sha256sum "$work/build_control/forge" "$PYTHONPATH/identity.py" > "$part/control_and_helper.sha256.txt"

compare() {
  local label=$1
  shift
  python3 -B "$part/uci_stream.py" compare "$@" > "$part/$label.json" 2> "$part/$label.stderr.txt"
}

for tag in r15d_cached k11v_cached r15d_reset k11v_reset control_reset control_cached; do
  arm=${tag%_*}
  mode=${tag##*_}
  extra=()
  case "$arm" in
    r15d) engine=/workspace/work/sol3-job4/build_0/forge ;;
    k11v) engine=/workspace/work/sol3-job8/build_v/forge ;;
    control)
      engine="$work/build_control/forge"
      read -r control_sha _ < "$part/control_and_helper.sha256.txt"
      extra=(--exe-sha256 "$control_sha")
      ;;
  esac
  args=(run --build "$arm" --mode "$mode" --engine "$engine" --net "$net"
        --fixture "$fixture" --output "$part/$tag" "${extra[@]}")
  status=0
  left=$((cutoff - $(date -u +%s)))
  {
    printf 'PYTHONPATH=%q python3 -B %q' "$PYTHONPATH" "$part/uci_stream.py"
    printf ' %q' "${args[@]}"
    printf '\n'
    date -u +%FT%TZ
    if ((left > 0)); then
      timeout --kill-after=5s "$left" python3 -B "$part/uci_stream.py" "${args[@]}" > "$part/$tag.driver.stdout.json" 2> "$part/$tag.driver.stderr.txt" || status=$?
    else
      status=124
    fi
    printf 'exit_code %s\n' "$status"
  } > "$part/$tag.run.meta"
  if ((status == 0)); then
    case "$tag" in
      k11v_cached)
        compare first_cached_common common "$part/r15d_cached" "$part/k11v_cached" || status=$?
        compare cached_search search "$part/r15d_cached" "$part/k11v_cached" || status=$?
        ;;
      r15d_reset)
        compare first_reset_common common "$part/r15d_reset" "$part/r15d_cached" || status=$?
        ;;
      k11v_reset)
        compare all_four_common common "$part/r15d_cached" "$part/r15d_reset" "$part/k11v_cached" "$part/k11v_reset" || status=$?
        compare reset_search search "$part/r15d_reset" "$part/k11v_reset" || status=$?
        for baseline in r15d_reset k11v_cached k11v_reset; do
          cmp "$part/r15d_cached/common.txt" "$part/$baseline/common.txt" || status=$?
        done
        cmp "$part/r15d_cached/search.txt" "$part/k11v_cached/search.txt" || status=$?
        cmp "$part/r15d_reset/search.txt" "$part/k11v_reset/search.txt" || status=$?
        ;;
      control_reset)
        compare control_reset_common common "$part/k11v_reset" "$part/control_reset" || status=$?
        compare control_reset_search search "$part/k11v_reset" "$part/control_reset" || status=$?
        ;;
      control_cached)
        compare first_control_difference common "$part/control_reset" "$part/control_cached" --expect-difference || status=$?
        ;;
    esac
  fi
  date -u "+%FT%TZ Part B $tag recorded complete raw and normalized streams with eligible comparisons, exit $status" >> "$job/stamps.txt"
  git add --sparse -- "$part" "$job/stamps.txt"
  git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
  git commit -qm "sol3 job 9 part B checkpoint $tag"
  bash /workspace/work/sol3-job3/push-checkpoint.sh
  if ((status != 0)); then
    cat "$part/$tag.driver.stderr.txt"
    printf 'Part B stopped in %s with exit %s\n' "$tag" "$status"
    exit "$status"
  fi
  python3 - "$part/$tag/summary.json" <<'PY'
import json
from pathlib import Path
import sys
result = json.loads(Path(sys.argv[1]).read_text())
print(result['build'], result['mode'], result['positions_completed'], result['normalized_stream_lines'],
      result['normalized_stream_sha256'], result['normalized'])
PY
done
