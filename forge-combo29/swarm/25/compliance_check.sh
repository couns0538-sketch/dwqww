#!/usr/bin/env bash
# compliance_check.sh : the brief's rules, checked mechanically. Run before every push.
# Fails loudly (exit 1) on any violation, so a .pyc or a stray file cannot go unnoticed.
set -u
cd "$(dirname "$0")/../.." 2>/dev/null || true
S=$(cat ~/swarm_seat.txt)
MYDIR="forge-combo29/swarm/$S"
cd "$(git rev-parse --show-toplevel)"
BASE=ae78bd1c2212807e86231ba1c039c0c7f97249cf     # my seat commit; diff from here
fails=0
note() { printf '%-46s %s\n' "$1" "$2"; }

# 1. no binary files tracked in my folder
bins=$(git ls-files "$MYDIR" | grep -E '\.(pyc|pyo|so|a|o|zip|gz|tar|png|jpg|jpeg|gif|exe|bin|dll|dylib)$' || true)
if [ -n "$bins" ]; then note "TRACKED BINARIES" "FAIL"; echo "$bins" | sed 's/^/    /'; fails=1
else note "tracked binaries in my folder" "PASS (0)"; fi

# 2. no file tracked OUTSIDE my folder by me
outside=$(git log --name-only --pretty=format: "$BASE"..HEAD 2>/dev/null | grep -v "^$MYDIR/" | grep -v '^$' | sort -u || true)
if [ -n "$outside" ]; then note "files touched outside my folder" "FAIL"; echo "$outside" | sed 's/^/    /'; fails=1
else note "files touched outside my folder" "PASS (0)"; fi

# 3. every tracked file in my folder is text (UTF-8 acceptable; binary content is not)
nontext=0
while IFS= read -r f; do
  [ -f "$f" ] || continue
  case "$(file -b "$f")" in
    *text*|*JSON*|*empty*|*CSV*) : ;;
    *) echo "    NON-TEXT: $f -> $(file -b "$f" | cut -c1-60)"; nontext=$((nontext+1)) ;;
  esac
done < <(git ls-files "$MYDIR")
if [ "$nontext" -gt 0 ]; then note "non-text files in my folder" "FAIL ($nontext)"; fails=1
else note "non-text files in my folder" "PASS (0)"; fi

# 4. no engine source tracked by me (patches only, and they must be .patch.txt)
srcs=$(git log --name-only --pretty=format: "$BASE"..HEAD 2>/dev/null | grep -E '^(forge-combo29/)?(src|include)/' | sort -u || true)
if [ -n "$srcs" ]; then note "engine source committed" "FAIL"; echo "$srcs" | sed 's/^/    /'; fails=1
else note "engine source committed" "PASS (0)"; fi

# 5. working tree clean (so nothing uncommitted is forgotten)
if [ -n "$(git status --porcelain -- "$MYDIR")" ]; then
  note "uncommitted changes in my folder" "WARN (push before ending)"
  git status --short -- "$MYDIR" | head -5 | sed 's/^/    /'
else note "uncommitted changes in my folder" "PASS (none)"; fi

echo
if [ "$fails" -ne 0 ]; then echo "COMPLIANCE: FAILED - fix before pushing"; exit 1; fi
echo "COMPLIANCE: PASS"
