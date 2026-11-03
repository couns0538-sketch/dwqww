#!/usr/bin/env bash
# test_installer.sh SCRATCH_DIR [LIVE_TRAINER] - Opus R14-B item 1: exit codes and file effects of
# install_fast_loader.py on copies of the live trainer's config.py + train.py (read-only from LIVE_TRAINER, default
# F:/opus_scratch/r6/nnue-pytorch-amd). The live folder itself is only read (--check) and its two files are hashed
# before and after; no install command is ever sent to it: the live-folder guard is tested on a copy of the installer
# whose LIVE_TRAINER names a stand-in folder (so a broken guard would patch only the stand-in). One PASS / FAIL line
# per case; exit 0 = all PASS. Bug hunt of 2026-11-02 22:2x (a misspelt --check used to install); CR fix 2026-11-03
# (copies whose trainer files are hard / symbolic links, a dangling link in a loader target's place).
set -u
d=${1:?scratch dir}
live=${2:-F:/opus_scratch/r6/nnue-pytorch-amd}
here=$(cd "$(dirname "$0")" && pwd)
I=$here/install_fast_loader.py
PY=${PY:-/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe}
for f in "$I" "$PY" "$live/config.py" "$live/train.py"; do [ -f "$f" ] || { echo "not found: $f" >&2; exit 2; }; done
[ -e "$d" ] && { echo "refusing existing $d" >&2; exit 2; }
mkdir -p "$d" && cd "$d" || exit 1
fails=0
expect() {  # expect CODE NAME TEXT CMD...: exit code and a text the output must contain, no traceback
  local want=$1 name=$2 text=$3; shift 3
  "$@" >"$name.out" 2>&1; local got=$?
  if [ "$got" = "$want" ] && grep -qF -- "$text" "$name.out" && ! grep -q Traceback "$name.out"; then
    echo "PASS $name (exit $got): $(head -c 140 "$name.out" | tr '\n' ' ')"
  else echo "FAIL $name: exit $got, wanted $want with '$text': $(head -c 300 "$name.out" | tr '\n' ' ')"; fails=$((fails + 1)); fi
}
check() { local name=$1; shift; if "$@"; then echo "PASS $name"; else echo "FAIL $name"; fails=$((fails + 1)); fi; }
fresh() { mkdir -p "$1" && cp "$live/config.py" "$live/train.py" "$1/"; }
live_sum() { sha256sum "$live/config.py" "$live/train.py" | cut -d' ' -f1 | tr '\n' ' '; }
live0=$(live_sum)
fresh t1; sum1=$(cat t1/*.py | sha256sum)
expect 0 check_fresh "anchors OK" "$PY" -I -B "$I" t1 --check
check check_changed_nothing test "$(cat t1/*.py | sha256sum)" = "$sum1"
expect 2 misspelt_check "unknown or incomplete argument '--chek'" "$PY" -I -B "$I" t1 --chek
check misspelt_check_changed_nothing test "$(cat t1/*.py | sha256sum)" = "$sum1"
expect 2 loader_dll_without_path "unknown or incomplete argument '--loader-dll'" "$PY" -I -B "$I" t1 --loader-dll
expect 2 no_folder "cannot read it as a trainer file" "$PY" -I -B "$I" no_such_dir
mkdir -p t2 && cp "$live/config.py" t2/ && printf 'x = "\xff"\n' > t2/train.py
expect 2 not_utf8 "cannot read it as a trainer file (UnicodeDecodeError" "$PY" -I -B "$I" t2
check not_utf8_config_unchanged cmp -s "$live/config.py" t2/config.py
fresh t3 && printf '\n# fast_loader\n' >> t3/config.py && sum3=$(cat t3/*.py | sha256sum)
expect 2 already_patched "already patched" "$PY" -I -B "$I" t3
check already_patched_changed_nothing test "$(cat t3/*.py | sha256sum)" = "$sum3"
fresh t4 && sed -i 's/world_size=1,/world_size=2,/' t4/train.py && sum4=$(cat t4/*.py | sha256sum)
expect 2 anchor_changed "anchor not found exactly once" "$PY" -I -B "$I" t4
check anchor_changed_changed_nothing test "$(cat t4/*.py | sha256sum)" = "$sum4"
fresh t5 && touch t5/forge_fastloader.dll && dll=$(cygpath -w "$live/train.py") && sum5=$(cat t5/*.py | sha256sum)
expect 2 loader_target_exists "exists, not overwritten" "$PY" -I -B "$I" t5 --loader-dll "$dll"
check loader_target_exists_changed_nothing test "$(cat t5/*.py | sha256sum)" = "$sum5"
# the guard: the committed installer names the live folder, and a copy of it whose LIVE_TRAINER names a stand-in
# (fresh copies of the two files) refuses a real install there
check live_guard_names_live_folder grep -qF 'LIVE_TRAINER = Path(r"F:\opus_scratch\r6\nnue-pytorch-amd")' "$I"
cat > make_guard_copy.py <<'EOF'
import re
import sys
src, dst, stand_in = sys.argv[1:]
with open(src, encoding="utf-8") as fh:
    text = fh.read()
new, k = re.subn(r'^LIVE_TRAINER = Path\(r"[^"]*"\)', 'LIVE_TRAINER = Path(r"' + stand_in + '")', text, flags=re.M)
with open(dst, "x", encoding="utf-8", newline="") as fh:
    fh.write(new)
sys.exit(0 if k == 1 else 1)
EOF
fresh stand_in && sum_si=$(cat stand_in/*.py | sha256sum)
check live_guard_copy_made "$PY" -I -B make_guard_copy.py "$I" guard_installer.py "$(cygpath -m "$PWD/stand_in")"
expect 2 live_install_refused "is the live npt trainer" "$PY" -I -B guard_installer.py stand_in
check live_install_refused_changed_nothing test "$(cat stand_in/*.py | sha256sum)" = "$sum_si"
# final bug hunt (04:31): the \\?\ spelling of the same folder passed the path comparison and patched the stand-in;
# the guard now compares file identity first. Other spellings (case, forward slashes, trailing slash) too.
expect 2 live_install_refused_extended_path "is the live npt trainer" "$PY" -I -B guard_installer.py '\\?\'"$(cygpath -w "$PWD/stand_in")"
expect 2 live_install_refused_other_spelling "is the live npt trainer" "$PY" -I -B guard_installer.py "$(cygpath -m "$PWD/STAND_IN")/"
check live_install_spellings_changed_nothing test "$(cat stand_in/*.py | sha256sum)" = "$sum_si"
# CR fix 2026-11-03 (item 1): a "copy" whose config.py / train.py are links to the live trainer's files - patching it
# wrote through the links into the live files. Shown on the stand-in only (a hard link to a real live file would itself
# change that file's link count, and F: is write-forbidden): hl/ = hard links, sl/ = symbolic links to the stand-in's
# two files. The guard copy (stand-in = live) must refuse both by file identity, also with --check; the committed
# installer (live = the real folder) by link count / link type alone, whatever the target.
mklinks() {  # mklinks hard|sym DIR: both trainer files of DIR as links to the stand-in's
  mkdir -p "$2" && "$PY" -I -B -c "import os, sys
kind, d, si = sys.argv[1:]
for f in ('config.py', 'train.py'):
    (os.link if kind == 'hard' else os.symlink)(os.path.join(si, f), os.path.join(d, f))" "$1" "$2" "$(cygpath -w "$PWD/stand_in")"
}
check linked_made_hard mklinks hard hl
check linked_made_sym mklinks sym sl
expect 2 linked_hard_refused "the same file as the live npt trainer's config.py" "$PY" -I -B guard_installer.py hl
expect 2 linked_sym_refused "the same file as the live npt trainer's train.py" "$PY" -I -B guard_installer.py sl
expect 2 linked_check_refused "the same file as the live npt trainer's config.py" "$PY" -I -B guard_installer.py hl --check
expect 2 linked_hard_refused_by_link_count "2 hard links" "$PY" -I -B "$I" hl
expect 2 linked_sym_refused_by_link_type "a symbolic link" "$PY" -I -B "$I" sl
check linked_live_unchanged test "$(cat stand_in/config.py stand_in/train.py | sha256sum)" = "$sum_si"
# a dangling symbolic link in a loader target's place used to pass the "exists" test and be written through
fresh t6 && "$PY" -I -B -c "import os, sys; os.symlink(os.path.join(sys.argv[1], 'forge_fastloader.py'), sys.argv[2])" \
  "$(cygpath -w "$PWD/stand_in")" t6/forge_fastloader.py && sum6=$(cat t6/config.py t6/train.py | sha256sum)
expect 2 loader_target_dangling_link "forge_fastloader.py: is a symbolic link, not overwritten" "$PY" -I -B "$I" t6 --loader-dll "$dll"
check loader_target_dangling_link_wrote_nothing test ! -e stand_in/forge_fastloader.py -a ! -e t6/forge_fastloader.dll \
  -a "$(cat t6/config.py t6/train.py | sha256sum)" = "$sum6"
expect 0 live_check_allowed "anchors OK" "$PY" -I -B "$I" "$live" --check
expect 0 install "patched" "$PY" -I -B "$I" t1
check install_patched_both test "$(grep -c fast_loader t1/config.py)" -ge 1 -a "$(grep -c fast_loader t1/train.py)" -ge 1
for f in config.py train.py; do  # CRLF / LF as found, no mixed line ends
  check "install_line_ends_$f" "$PY" -I -B -c "import sys; a = open(sys.argv[1], 'rb').read(); b = open(sys.argv[2], 'rb').read()
crlf = b'\r\n' in a
sys.exit(0 if (b'\r\n' in b) == crlf and (not crlf or b.count(b'\n') == b.count(b'\r\n')) else 1)" "$live/$f" "t1/$f"
done
expect 2 second_install "already patched" "$PY" -I -B "$I" t1
check live_unchanged test "$(live_sum)" = "$live0"
echo "failures: $fails"
exit $((fails > 0))
