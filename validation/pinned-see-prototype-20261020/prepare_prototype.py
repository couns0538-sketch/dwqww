#!/usr/bin/env python3
"""Freeze source/core, patch only an exported board.cpp, and build serially."""
from pathlib import Path
import datetime, difflib, hashlib, json, os, shutil, subprocess, tarfile, time

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
WORK = Path('/workspace/pinned-see-prototype-20261020')
COMMIT = '21538ec5416c909fc98a08688242a0b3b9710b25'
BUILD = Path('/workspace/.cloud-setup/forge-extension-path-release')
OLD_SOURCE = Path('/workspace/.cloud-setup/forge-extension-path-source')
SOURCE = WORK / 'source'
RECORD = {'source_commit': COMMIT, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'phases': []}

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(): (ROOT / 'build-record.json').write_text(json.dumps(RECORD, indent=2) + '\n')
def run(label, args, timeout=60):
    start = time.monotonic()
    p = subprocess.run(args, cwd=WORK, capture_output=True, timeout=timeout)
    for ext, data in [('stdout', p.stdout), ('stderr', p.stderr)]: (ROOT / (label + '.' + ext)).write_bytes(data)
    RECORD['phases'].append({'label':label, 'command': [str(a) for a in args], 'cwd':str(WORK), 'return_code':p.returncode, 'elapsed_seconds':time.monotonic()-start, 'timeout_seconds':timeout})
    save()
    if p.returncode: raise RuntimeError(label + ' failed')
    return p.stdout

WORK.mkdir(exist_ok=True)
paths = ['CMakeLists.txt', 'LICENSE', 'include', 'src', 'tests', 'tools', 'bench']
files = subprocess.check_output(['git', '-C', str(REPO), 'ls-tree', '-r', '--name-only', COMMIT, '--', *paths], text=True).splitlines()
hashes = {}
for relative in files:
    expected = subprocess.check_output(['git', '-C', str(REPO), 'show', COMMIT + ':' + relative])
    actual = (OLD_SOURCE / relative).read_bytes()
    if expected != actual: raise RuntimeError('Existing Release source mismatch: ' + relative)
    hashes[relative] = hashlib.sha256(expected).hexdigest()
(ROOT / 'frozen-source-sha256.json').write_text(json.dumps(hashes, indent=2) + '\n')
archive = ROOT / 'frozen-source-21538ec.tar'
archive.write_bytes(subprocess.check_output(['git','-C',str(REPO),'archive',COMMIT,*paths]))
SOURCE.mkdir(exist_ok=True)
with tarfile.open(archive) as tar: tar.extractall(SOURCE, filter='data')
assert all(sha(SOURCE / p) == h for p,h in hashes.items())
RECORD['complete_build_source_export'] = {'paths':paths,'files':len(files),'archive_sha256':sha(archive),'all_existing_build_sources_match_commit':True}
flags_file = BUILD / 'CMakeFiles/forge_core.dir/flags.make'
shutil.copy2(flags_file, ROOT / 'original-flags.make')
flags = next(line.split(' = ',1)[1].split() for line in flags_file.read_text().splitlines() if line.startswith('CXX_FLAGS = '))
core = BUILD / 'libforge_core.a'
RECORD['original_core_path'] = str(core)
RECORD['original_core_sha256_before'] = sha(core)
shutil.copy2(core, ROOT / 'baseline-libforge_core.a')
shutil.copy2(core, ROOT / 'candidate-libforge_core.a')
members = run('original-members', ['ar', 't', core]).decode().splitlines()
RECORD['original_member_sha256'] = {m:hashlib.sha256(subprocess.check_output(['ar','p',str(core),m])).hexdigest() for m in members}
board = SOURCE / 'src/board.cpp'
before = board.read_text()
needle = '        const Bitboard stm_attackers = attackers & occupied(stm);\n'
replacement = '''        Bitboard stm_attackers = attackers & occupied(stm);
        // Exchange occupants are virtual: original piece bitboards retain the
        // captured victim on `to`, and consumed recapturers at empty origins.
        // A candidate moves to the occupied target, so only its origin leaves
        // occupancy. Keeping the target occupied also permits along-pin moves.
        const Bitboard removed = ~occupancy | square_bb(to);
        Bitboard candidates = stm_attackers & ~pieces(stm, King);
        while (candidates != 0) {
            const int square = pop_lsb(candidates);
            if (square_attacked_with_occupancy(king_square(stm), opposite(stm),
                                              occupancy ^ square_bb(square), removed)) {
                stm_attackers &= ~square_bb(square);
            }
        }
'''
assert before.count(needle) == 1
after = before.replace(needle, replacement)
board.write_text(after)
(ROOT / 'pinned-see.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile='a/src/board.cpp', tofile='b/src/board.cpp')))
shutil.copy2(board, ROOT / 'candidate-board.cpp')
RECORD['candidate_board_sha256'] = sha(board)
save()
obj = WORK / 'board.cpp.o'
run('compile-board', ['/usr/bin/c++', *flags, '-I'+str(SOURCE/'include'), '-c', str(board), '-o', str(obj)], 90)
run('replace-board', ['ar','r',str(ROOT/'candidate-libforge_core.a'), str(obj)])
run('ranlib', ['ranlib', str(ROOT/'candidate-libforge_core.a')])
candidate_hashes = {m:hashlib.sha256(subprocess.check_output(['ar','p',str(ROOT/'candidate-libforge_core.a'),m])).hexdigest() for m in members}
RECORD['candidate_member_sha256'] = candidate_hashes
RECORD['only_changed_member'] = [m for m in members if candidate_hashes[m] != RECORD['original_member_sha256'][m]]
assert RECORD['only_changed_member'] == ['board.cpp.o']
RECORD['original_core_sha256_after'] = sha(core)
assert RECORD['original_core_sha256_after'] == RECORD['original_core_sha256_before']
RECORD['candidate_core_sha256'] = sha(ROOT/'candidate-libforge_core.a')
save()
print(json.dumps({'status':'prototype_core_built', 'changed_members':RECORD['only_changed_member'], 'candidate_core_sha256':RECORD['candidate_core_sha256']}))
