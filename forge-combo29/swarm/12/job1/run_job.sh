#!/usr/bin/env bash
# run_job.sh EXE SEQDIR OUTDIR TAG — one measuring entry point for seat 12 job 1.
# Writes OUTDIR/<TAG>.meta (exe path it STARTED, its sha256, `id name`, every option line sent,
# plus the nm proof that the exe really carries the sanitizer runtime) and then drives the
# sequence replay. Every later table is built from these files.
set -u
EXE="$1"; SEQDIR="$2"; OUTDIR="$3"; TAG="$4"
mkdir -p "$OUTDIR"
META="$OUTDIR/$TAG.meta"
{
  echo "exe: $EXE"
  echo "sha256: $(sha256sum "$EXE" | cut -d' ' -f1)"
  echo "date_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'uci\nquit\n' | "$EXE" 2>&1 | grep -E "^(id name|option name)" > "$OUTDIR/$TAG.uci.txt"
  echo "id_name: $(grep -m1 '^id name' "$OUTDIR/$TAG.uci.txt" | cut -d' ' -f3-)"
  echo "nm_asan: $(nm -C "$EXE" 2>/dev/null | grep -c __asan_)"
  echo "nm_ubsan: $(nm -C "$EXE" 2>/dev/null | grep -c __ubsan_)"
  echo "nm_tsan: $(nm -C "$EXE" 2>/dev/null | grep -c __tsan_)"
  echo "options_sent: (none - the sequences carry their own setoption lines; the set of option names they may send is listed in $OUTDIR/$TAG.uci.txt)"
  echo "sequence_count: $(ls "$SEQDIR"/seq_*.txt | wc -l)"
  echo "env: ASAN_OPTIONS=detect_leaks=0 UBSAN_OPTIONS=print_stacktrace=1 (set by runner.py for the child)"
} > "$META"
cat "$META"
python3 "$(dirname "$0")/runner.py" "$EXE" "$SEQDIR" "$OUTDIR/$TAG.jsonl" "${5:-20}"
