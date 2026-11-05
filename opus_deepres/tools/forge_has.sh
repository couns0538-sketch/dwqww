#!/usr/bin/env bash
# forge_has.sh - "does Forge have it": grep the lock FD3A5190 source (git d4f4312 = src_al1s198_clean, read-only).
# usage: bash forge_has.sh 'REGEX' [MAXHITS]   -> file:line: text (generated tables and weights are skipped)
LOCK=/c/Users/Administrator/grok-pc/forge_push/qa_ltopgo_al1_stage/src_al1s198_clean
rx="$1"; max="${2:-12}"
if [ -z "$rx" ]; then echo "usage: bash forge_has.sh 'REGEX' [MAXHITS]"; exit 2; fi
cd "$LOCK" || { echo "lock source missing: $LOCK"; exit 2; }
hits=$(grep -rnE -i "$rx" include src \
  --exclude=nnue_weights.inc --exclude=book_data.inc --exclude=eval_params_table.inc --exclude=polyglot_keys.inc)
n=$(printf '%s' "$hits" | grep -c . )
printf '%s\n' "$hits" | head -n "$max" | cut -c1-160
echo "# $n hit(s) for /$rx/ in the lock source (showing at most $max)"
