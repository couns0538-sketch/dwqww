#!/usr/bin/env bash
# Prove the warned -p1 trap is loud: applying each patch at the WRONG strip level must fail.
set -u
cd "$HOME/comp/mate/applied/forge-combo29"
echo "== seat 12 patch applied at the seat-27 level (inside forge-combo29) =="
patch -p1 --dry-run -i "$HOME/p/two_doors_mate.patch.txt"; echo "EXIT=$?"
cd "$HOME/comp/mate/applied"
echo
echo "== seat 27 patch applied at the seat-12 level (repo root) =="
patch -p1 --dry-run -i "$HOME/p/drawn_root_reporting.patch.txt"; echo "EXIT=$?"
