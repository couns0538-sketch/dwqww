#!/bin/sh
# Re-run every NEGATIVE claim this audit makes, with the command that enumerates the
# thing being denied. A negative claim without an enumerating command is unfalsifiable,
# so this file exists to make each one checkable by someone who does not trust us.
#
# Usage: sh scripts/verify_claims.sh
set -u
REPO=${REPO:-/agent/repos/dwqww}
FAIL=0

say() { printf '\n=== %s\n' "$1"; }
chk() { # chk <description> <actual> <expected>
  if [ "$2" = "$3" ]; then printf '  PASS  %s (%s)\n' "$1" "$2"
  else printf '  FAIL  %s: got %s want %s\n' "$1" "$2" "$3"; FAIL=1; fi
}

say "refs and commits the negative claims quantify over"
REFS=$(git -C "$REPO" for-each-ref --format='%(refname)' | wc -l | tr -d ' ')
ORIGIN=$(git -C "$REPO" for-each-ref --format='%(refname)' | grep -c '^refs/remotes/origin/')
TAGS=$(git -C "$REPO" for-each-ref --format='%(refname)' | grep -c '^refs/tags/')
COMMITS=$(git -C "$REPO" rev-list --all | wc -l | tr -d ' ')
echo "  refs=$REFS (origin/*=$ORIGIN, tags=$TAGS)  commits=$COMMITS"
echo "  both refs/remotes/origin/* AND refs/tags are inside this census."

say "CLAIM: no COMMIT starts with 068f  (expected: it is a binary sha256, not a commit)"
chk "git rev-list --all | grep -c '^068f'" "$(git -C "$REPO" rev-list --all | grep -c '^068f')" 0

say "CLAIM: the audit base is a real commit containing forge-combo29/"
chk "git cat-file -t 6b98f217" "$(git -C "$REPO" cat-file -t 6b98f217 2>&1)" "commit"
if git -C "$REPO" cat-file -e 6b98f217:forge-combo29 2>/dev/null; then
  echo "  PASS  base tree contains forge-combo29/"
else echo "  FAIL  base tree has no forge-combo29/"; FAIL=1; fi

say "CLAIM: the r15 patch text hashes to d6bd72c531f785f4..."
git -C "$REPO" cat-file -p 12772bb790459856ed42d512a28721b8f96c4249 > /tmp/_f5.md
awk 'NR>55 && /^```$/{exit} NR>55' /tmp/_f5.md > /tmp/_f5.patch
P=$(sha256sum /tmp/_f5.patch | cut -d' ' -f1)
case "$P" in
  d6bd72c531f785f4*) echo "  PASS  patch sha256 = $P" ;;
  *) echo "  FAIL  patch sha256 = $P"; FAIL=1 ;;
esac

say "CLAIM: integrate/combo29-all is an OLDER tree, not the base's line"
MB=$(git -C "$REPO" merge-base 6b98f217 origin/integrate/combo29-all 2>/dev/null | cut -c1-9)
echo "  merge-base = $MB  (documented e04556ddc)"
if [ -n "$MB" ]; then echo "  PASS  a merge-base exists, so the histories are related, not disjoint"
else echo "  FAIL  no merge-base"; FAIL=1; fi
AHEAD=$(git -C "$REPO" rev-list --count origin/integrate/combo29-all..6b98f217 2>/dev/null)
echo "  base is $AHEAD commits ahead (documented 277)"

say "CLAIM: the owner's net is not in the repository"
if git -C "$REPO" ls-tree -r --name-only 6b98f217 | grep -qiE '\.fnn3$'; then
  echo "  FAIL  a .fnn3 net IS committed at the base"; FAIL=1
else echo "  PASS  no .fnn3 file at the base commit"; fi

printf '\n================ '
[ "$FAIL" = 0 ] && echo "ALL CLAIMS VERIFIED" || echo "SOME CLAIMS FAILED"
printf '================\n'
exit "$FAIL"
