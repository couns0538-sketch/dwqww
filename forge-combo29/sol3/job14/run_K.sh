#!/usr/bin/env bash
set -euo pipefail
work=/workspace/work/sol3-job14
job=forge-combo29/sol3/job14
refs=/workspace/work/sol3-job14-reference
old=forge-combo29/sol3/job13
engine="$work/build_floor/forge"
mkdir -p "$job/references"
cp "$work/"{fixed_depth.py,readback.py,verify_counters_raw.py,run_one.sh,known_compare.py,run_K.sh} "$job/"
cp "$refs/"{O_F0.tsv,O_F0.tsv.meta,G_F0.tsv,G_F0.tsv.meta,O_floor1.tsv,O_floor1.tsv.meta,G_floor1.tsv,G_floor1.tsv.meta,Base4.tsv,Base4.raw.txt,Base4.meta,Floor1.tsv,Floor1.raw.txt,Floor1.meta,reference_proof.txt} "$job/references/"
cp "$refs/O.epd" "$job/references/O.authored.epd.txt"
git show HEAD:"$old/references/fixture_G.epd.txt" > "$job/references/G.epd.txt"
git show HEAD:"$old/references/P.fen.txt" > "$job/references/P.fen.txt"
cat > "$job/references/source.txt" <<'EOF'
O and G EPD files at kimi5-work 5db05e095d5e81622eb0de13eb8a738a0ae1d22a.
Reference rows from Astra5 Job 4 at eca6fbaaf22e3c957a83ff96d7fd8ff1d90066db: C/rows/{O,G}_F0.tsv, D/{O,G}_floor1.tsv, A/{Base4,Floor1}.tsv plus raw ladder logs.
O reference runner uses the first four EPD fields and the default 0 1 clocks for all positions. Authored bytes are preserved separately. G already uses 0 1 throughout.
EOF
{
  printf '%s  %s\n' ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8 "$job/references/O.authored.epd.txt"
  printf '%s  %s\n' af3aefd80fcea207b215e95560f5921aa7a3bb9186d4cdfadf2e567207b5c54d "$job/references/G.epd.txt"
} | sha256sum --strict -c > "$job/references/fixture_hash_gate.txt"
awk '{print $1,$2,$3,$4,"0","1"}' "$job/references/O.authored.epd.txt" > "$job/references/O.epd.txt"
test "$(wc -l < "$job/references/O.epd.txt")" -eq 200
test "$(wc -l < "$job/references/G.epd.txt")" -eq 353
sha256sum "$job/references/"*.tsv "$job/references/"*epd.txt > "$job/references/used_input_hashes.txt"
save() {
  local label=$1 status=$2
  date -u "+%FT%TZ $label exit $status" >> "$job/stamps.txt"
  git add --sparse -- "$job"
  git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
  git commit -qm "sol3 job 14 checkpoint $label"
  bash /workspace/work/sol3-job3/push-checkpoint.sh
}

for step in K1 K2; do
  for suite in O G; do
    destination="$job/$step/$suite"
    args=(--depth 12 --counter)
    if [ "$step" = K1 ]; then
      reference="$job/references/${suite}_F0.tsv"
      check=(--counts)
    else
      reference="$job/references/${suite}_floor1.tsv"
      args+=(--null-floor 1)
      check=()
    fi
    status=0
    bash "$job/run_one.sh" "$engine" "$destination" "$job/references/$suite.epd.txt" "${args[@]}" || status=$?
    if ((status == 0)); then
      python3 -B "$job/known_compare.py" "$reference" "$destination/rows.tsv" "${check[@]}" > "$destination/known_gate.json" 2> "$destination/known_gate.stderr.txt" || status=$?
      python3 -B "$job/verify_counters_raw.py" "$destination" "$(wc -l < "$job/references/$suite.epd.txt")" > "$destination/raw_counts.json" 2> "$destination/raw_counts.stderr.txt" || status=$?
    fi
    save "$step $suite known suite rows" "$status"
    if test -f "$destination/known_gate.json"; then cat "$destination/known_gate.json"; fi
  done
done

for arm in Base4 Floor1; do
  destination="$job/K3/$arm"
  args=(--ladder 20 --counter)
  if [ "$arm" = Base4 ]; then args+=(--null-base 4); else args+=(--null-floor 1); fi
  status=0
  bash "$job/run_one.sh" "$engine" "$destination" "$job/references/P.fen.txt" "${args[@]}" || status=$?
  if ((status == 0)); then
    python3 -B "$job/readback.py" A1 "$destination/rows.tsv" "$job/references/$arm.tsv" > "$destination/known_gate.json" 2> "$destination/known_gate.stderr.txt" || status=$?
    python3 -B "$job/readback.py" ladder "$destination/rows.tsv" > "$destination/threshold.json" || status=$?
    python3 -B "$job/verify_counters_raw.py" "$destination" 20 > "$destination/raw_counts.json" 2> "$destination/raw_counts.stderr.txt" || status=$?
  fi
  save "K3 $arm complete P depth ladder" "$status"
  if test -f "$destination/known_gate.json"; then cat "$destination/known_gate.json" "$destination/threshold.json"; fi
done
