#!/usr/bin/env bash
# build_o30tuned.sh <TUNED_OPTIONS.txt> <SPSA run dir> <tag> - Opus 30-h job: the Item B exe with ONE switch for a tuned
# set, from the session's report to a checked exe:
#  1 fresh clone of the expose22 scratch repo (D:\o30\repos\spsa, head deabbd2) -> D:\o30\repos\<tag> (refused if it exists)
#  2 b/o30_tuned_patch.py (UCI check O30Tuned, default false; table = TUNED_OPTIONS.txt + the run's params.csv starts)
#  3 commit; the patch saved as b/o30tuned_<tag>.patch; cleanroom_lint on it
#  4 kit v2.3 -Expose pc1 + pc2 (tools/kit_build_o30.sh: binding pc1 = pc2, OFF pins + perft pins); the kit waits
#    until CPUs 0-1 are free enough, so run it after the tuner has stopped
#  5 b/test_o30tuned.sh on the pc1 exe (OFF pins -Full, switch = explicit list, true then false = lock, invalid value)
# Exit 0 only if every step passed; the last line names the exe and its sha256.
set -uo pipefail
tuned="$1"; run="$2"; tag="$3"
B=$(cd "$(dirname "$0")" && pwd); T="$B/../tools"
. "$T/idle.sh"; o30_pin_self 0x3 || { echo "cannot pin to Idle / CPUs 0-1 (fail closed)" >&2; exit 78; }
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
src=/d/o30/repos/spsa; repo=/d/o30/repos/$tag
[ -f "$tuned" ] && [ -f "$run/params.csv" ] || { echo "need $tuned and $run/params.csv" >&2; exit 2; }
[ -e "$repo" ] && { echo "refusing: $repo exists" >&2; exit 2; }
[ -e "$B/o30tuned_$tag.patch" ] && { echo "refusing: $B/o30tuned_$tag.patch exists" >&2; exit 2; }
git clone -q "$src" "$repo" || exit 2
[ "$(git -C "$repo" rev-parse --short=7 HEAD)" = "deabbd2" ] || { echo "the expose22 repo head is not deabbd2" >&2; exit 2; }
"$PY" -I -B "$B/o30_tuned_patch.py" --tuned "$(cygpath -w "$tuned")" --params "$(cygpath -w "$run/params.csv")" \
  --repo "$(cygpath -w "$repo")" --label "the SPSA session $(basename "$run") of the Opus 30-h job" || exit 3
git -C "$repo" -c user.name=couns0538-sketch -c user.email=couns0538@gmail.com commit -q -am "O30Tuned: one switch for the tuned set" || exit 3
git -C "$repo" diff HEAD~1 HEAD > "$B/o30tuned_$tag.patch" || exit 3
"$PY" -I -B "$T/cleanroom_lint.py" --patch "$(cygpath -w "$B/o30tuned_$tag.patch")" || exit 4
bash "$T/kit_build_o30.sh" "$repo" "$tag" || exit 5
exe=/d/o30/w/${tag}_pc1/src_copy/forge_ltopgo_${tag}_pc1.exe
bash "$B/test_o30tuned.sh" "$exe" "$tuned" 0x3 || exit 6
echo "O30TUNED EXE $(cygpath -w "$exe") sha256 $(sha256sum "$exe" | cut -c1-64) patch b/o30tuned_$tag.patch md5 $(md5sum "$B/o30tuned_$tag.patch" | cut -c1-32)"
