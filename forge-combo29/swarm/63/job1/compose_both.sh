#!/usr/bin/env bash
# Reproduce the composition in BOTH orders and record every exit code and the hash.
set -u
echo "== order 1: seat 12 (repo root, -p1) then seat 27 (inside forge-combo29, -p1) =="
bash "$HOME/p/compose.sh" mate 2>&1 | tee /tmp/c1.txt
echo
echo "== order 2: seat 27 (inside forge-combo29, -p1) then seat 12 (repo root, -p1) =="
bash "$HOME/p/compose.sh" report 2>&1 | tee /tmp/c2.txt
echo
echo "== byte comparison =="
sha256sum "$HOME/comp/mate/applied/forge-combo29/src/search.cpp" "$HOME/comp/report/applied/forge-combo29/src/search.cpp"
if cmp -s "$HOME/comp/mate/applied/forge-combo29/src/search.cpp" "$HOME/comp/report/applied/forge-combo29/src/search.cpp"; then
  echo "cmp: IDENTICAL"
else
  echo "cmp: DIFFER"
fi
echo
echo "== expected hash =="
echo "24912a43d315243f2f9dcb0ea032e7160633b99483c0a5e26541e870b2a26671  (claimed)"
