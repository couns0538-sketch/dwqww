#!/usr/bin/env bash
# uci answer of exe P. Proof that IdeaK9 and IdeaK9_Cap are listed with defaults.
set -euo pipefail
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
EXE=/agent/repos/work/forge-combo29/build-release/forge
SHA=$(sha256sum "$EXE" | awk '{print $1}')
printf 'uci\nquit\n' | "$EXE" > "$DIR/uci_p.txt"
{
  echo "exe=$EXE"
  echo "sha256=$SHA"
  echo "id_name=$(sed -n 's/^id name //p' "$DIR/uci_p.txt" | head -1)"
  echo "options_sent=none"
  echo "command=uci"
} > "$DIR/uci_p.meta"
grep -n -E 'option name (IdeaK9|IdeaK9_Cap) ' "$DIR/uci_p.txt" > "$DIR/uci_p_new_options.txt"
echo "----- new options -----"
cat "$DIR/uci_p_new_options.txt"
