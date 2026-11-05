#!/usr/bin/env bash
# doc_checks_o30.sh - Opus 30-h job: re-run only the document checks of tools/final_checks_o30.sh (10 cleanroom_lint incl.
# the commit messages, 11 doc_lint, 12 INDEX.md hashes, 13 cited paths, 15 cited hashes) after the last document edits,
# with the check functions taken from final_checks_o30.sh itself (no second copy to drift). Idle on O30_MASK (required).
# Prints one PASS / FAIL line per check and a total; exit 0 only if all pass.
set -u
[ -n "${O30_MASK:-}" ] || { echo "doc_checks_o30: set O30_MASK (no default)" >&2; exit 78; }
W=/d/o30/wt; T=$W/opus_30h/tools; A=$W/opus_30h/a; B=$W/opus_30h/b
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
. "$T/idle.sh"; o30_pin_self "$O30_MASK" || { echo "doc_checks_o30: cannot pin (fail closed)"; exit 78; }
F="$T/final_checks_o30.sh"
for fn in lint doclint indexsha paths hashes; do
    first=$(grep -E "^$fn\(\) \{" "$F" | head -1)
    if [[ "$first" =~ \}[[:space:]]*$ ]]; then
        eval "$first"                                   # a one-line function (doclint, indexsha)
    else
        eval "$(sed -n "/^$fn() {/,/^}/p" "$F")"        # a multi-line function, up to its closing brace
    fi
    declare -F "$fn" > /dev/null || { echo "doc_checks_o30: no function $fn in $F" >&2; exit 2; }
done
tmp=/d/o30/tmp/doc_checks_$(date +%Y%m%d_%H%M%S); mkdir -p "$tmp"
pass=0; fail=0
for c in "10_cleanroom lint" "11_doc_lint doclint" "12_index_hashes indexsha" "13_paths paths" "15_doc_hashes hashes"; do
    set -- $c
    if "$2" > "$tmp/$1.log" 2>&1; then echo "PASS $1"; pass=$((pass + 1)); else echo "FAIL $1 (log $tmp/$1.log)"; fail=$((fail + 1)); fi
done
echo "doc_checks_o30: $pass PASS, $fail FAIL (logs $tmp)"
[ "$fail" = 0 ]
