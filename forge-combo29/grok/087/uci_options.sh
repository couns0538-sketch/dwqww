#!/usr/bin/env bash
# Proof that uci lists IdeaA6 and its spins with defaults. Fresh process, no setoption.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OUT="forge-combo29/grok/$S"
EXE="/agent/repos/work/forge-combo29/build/forge"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
printf 'uci\nquit\n' | "$EXE" > "$OUT/uci_p.txt"
{
  echo "exe $EXE"
  echo "sha256 $SHA"
  echo "id name $(awk '/^id name /{sub(/^id name /,""); print; exit}' "$OUT/uci_p.txt")"
  echo "options: none"
  echo "command: uci"
} > "$OUT/uci_p.txt.meta"
awk '/^option name IdeaA6/ || /^id name /' "$OUT/uci_p.txt" > "$OUT/uci_p_idea.txt"
