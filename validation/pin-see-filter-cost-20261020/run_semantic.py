#!/usr/bin/env python3
"""Isolated serial board-only build and immutable-corpus API parity gate."""
from pathlib import Path
import csv, datetime, difflib, hashlib, io, json, os, shutil, subprocess, tarfile, time

OUT = Path(__file__).resolve().parent
REPO = OUT.parent.parent
WORK = Path('/workspace/pin-see-filter-cost-20261020')
REV = '8d303e4ca0428e9750bbf3e2663c64d9fafbd1ad'
BUILD = Path('/workspace/.cloud-setup/forge-pin-see-release')
ORIGINAL_SOURCE = Path('/workspace/.cloud-setup/forge-pin-see-source')
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
RECORD = {'source_commit': REV, 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'phases': [], 'engine_execution_budget_seconds': 120, 'engine_elapsed_seconds': 0,
          'performance_claim': None, 'status': 'RUNNING'}

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(): (OUT/'semantic-record.json').write_text(json.dumps(RECORD, indent=2)+'\n')
def run(label, args, timeout=60, engine=False):
    if engine and RECORD['engine_elapsed_seconds'] + timeout > 120:
        raise RuntimeError('Insufficient remaining preregistered engine budget')
    start = time.monotonic()
    try:
        p = subprocess.run([str(x) for x in args], cwd=WORK, env=ENV, capture_output=True, timeout=timeout)
        rc, stdout, stderr = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as exc:
        rc, stdout, stderr = 124, exc.stdout or b'', exc.stderr or b''
    elapsed = time.monotonic()-start
    for ext, data in [('stdout',stdout),('stderr',stderr)]: (OUT/(label+'.'+ext)).write_bytes(data)
    RECORD['phases'].append({'label':label,'command':[str(x) for x in args], 'cwd':str(WORK),
                            'timeout_seconds':timeout, 'exit_code':rc,
                            'elapsed_seconds_operational_only':elapsed,'engine_execution':engine,
                            'stdout_sha256':sha(OUT/(label+'.stdout')),'stderr_sha256':sha(OUT/(label+'.stderr'))})
    if engine: RECORD['engine_elapsed_seconds'] += elapsed
    save()
    print(label, rc, flush=True)
    if rc: raise RuntimeError(label+' exit '+str(rc))
    return stdout

try:
    WORK.mkdir(exist_ok=False)
    paths = ['CMakeLists.txt','LICENSE','src','include','tests','tools','bench']
    archive = subprocess.check_output(['git','archive',REV,*paths],cwd=REPO)
    (OUT/'source-reference-8d303e4.tar').write_bytes(archive)
    src = WORK/'source-reference'; src.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar: tar.extractall(src, filter='data')
    expected = {str(p.relative_to(src)):sha(p) for p in sorted(src.rglob('*')) if p.is_file()}
    assert all(sha(ORIGINAL_SOURCE/p)==h for p,h in expected.items())
    RECORD['reference_source_sha256'] = expected
    RECORD['reference_source_archive_sha256'] = sha(OUT/'source-reference-8d303e4.tar')
    original_core = BUILD/'libforge_core.a'
    RECORD['original_core_path'] = str(original_core)
    RECORD['original_core_sha256_before'] = sha(original_core)
    assert RECORD['original_core_sha256_before'] == '27c8db2caf860c868dbece61a4de0b8121a5d696b846a96e4f7aa2439498ea97'
    original_flags = BUILD/'CMakeFiles/forge_core.dir/flags.make'
    shutil.copy2(original_flags,OUT/'original-flags.make')
    flags = next(line.split(' = ',1)[1].split() for line in original_flags.read_text().splitlines() if line.startswith('CXX_FLAGS = '))
    RECORD['compiler'] = '/usr/bin/c++'; RECORD['flags'] = flags
    reference_core = OUT/'reference-libforge_core.a'; mask_core = OUT/'mask-libforge_core.a'
    shutil.copy2(original_core,reference_core); shutil.copy2(original_core,mask_core)
    members = run('original-members',['ar','t',original_core]).decode().splitlines()
    member_hashes = {m:hashlib.sha256(subprocess.check_output(['ar','p',original_core,m])).hexdigest() for m in members}
    RECORD['reference_core_members'] = member_hashes
    (OUT/'reference-board.cpp.o').write_bytes(subprocess.check_output(['ar','p',original_core,'board.cpp.o']))
    mask_src = WORK/'source-mask'; shutil.copytree(src,mask_src)
    before = (src/'src/board.cpp').read_text()
    needle = '''        // Exchange occupants are virtual: original piece bitboards retain the
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
    replacement = '''        // Every candidate only removes its own origin; the target stays occupied.
        // Existing checks reject every non-king; singleton ray blockers identify
        // exactly the origins whose departure would expose a live enemy slider.
        const Bitboard king_attackers = stm_attackers & pieces(stm, King);
        if ((stm_attackers & ~king_attackers) != 0) {
            const Color enemy = opposite(stm);
            const int king = king_square(stm);
            const Bitboard live = occupancy & ~square_bb(to);
            const Bitboard queens = pieces(enemy, Queen) & live;
            bool checked =
                (attacks::pawn(stm, king) & pieces(enemy, Pawn) & live) != 0 ||
                (attacks::knight(king) & pieces(enemy, Knight) & live) != 0 ||
                (attacks::king(king) & pieces(enemy, King) & live) != 0;
            Bitboard pinners =
                (attacks::bishop(king, 0) & ((pieces(enemy, Bishop) & live) | queens)) |
                (attacks::rook(king, 0) & ((pieces(enemy, Rook) & live) | queens));
            Bitboard forbidden = 0;
            while (!checked && pinners != 0) {
                const int pinner = pop_lsb(pinners);
                const Bitboard blockers = attacks::between(king, pinner) & occupancy;
                if (blockers == 0) checked = true;
                else if (!more_than_one(blockers)) forbidden |= blockers;
            }
            stm_attackers = checked ? king_attackers : stm_attackers & ~forbidden;
        }
'''
    assert before.count(needle)==1
    after = before.replace(needle,replacement)
    (mask_src/'src/board.cpp').write_text(after)
    (OUT/'reference-board.cpp').write_text(before); (OUT/'mask-board.cpp').write_text(after)
    (OUT/'mask.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/src/board.cpp',tofile='b/src/board.cpp')))
    RECORD['mask_board_sha256'] = sha(OUT/'mask-board.cpp')
    with tarfile.open(OUT/'source-mask.tar','w') as tar:
        for relative in expected: tar.add(mask_src/relative,arcname=relative)
    RECORD['mask_source_archive_sha256'] = sha(OUT/'source-mask.tar')
    save()
    run('compile-mask-board',['/usr/bin/c++',*flags,'-I'+str(mask_src/'include'),'-c',mask_src/'src/board.cpp','-o',OUT/'mask-board.cpp.o'],90)
    # ar uses the input basename as its archive member name.
    shutil.copy2(OUT/'mask-board.cpp.o',WORK/'board.cpp.o')
    run('replace-mask-board',['ar','r',mask_core,WORK/'board.cpp.o'])
    run('ranlib-mask',['ranlib',mask_core])
    actual_members={m:hashlib.sha256(subprocess.check_output(['ar','p',mask_core,m])).hexdigest() for m in members}
    RECORD['mask_core_members'] = actual_members
    RECORD['changed_core_members'] = [m for m in members if actual_members[m]!=member_hashes[m]]
    assert RECORD['changed_core_members']==['board.cpp.o']
    inputs = OUT/'inputs'; inputs.mkdir()
    originals = [REPO/'validation/pinned-see-prototype-20261020/cases.tsv',
                 REPO/'validation/pinned-see-prototype-20261020/supplement-cases.tsv',
                 REPO/'validation/pin-see-coverage-20261020/cases.tsv']
    immutable = {str(p):sha(p) for p in originals}
    combined=[]
    for label,path in zip(['main','supplement','coverage'],originals):
        shutil.copy2(path,inputs/(label+'.tsv')); combined.extend(path.read_text().splitlines())
    assert len(combined)==316 and len({line.split('\t',1)[0] for line in combined})==316
    (inputs/'all316.tsv').write_text('\n'.join(combined)+'\n')
    driver = REPO/'validation/pinned-see-prototype-20261020/see_diagnostic.cpp'
    immutable[str(driver)] = sha(driver); shutil.copy2(driver,OUT/'see_diagnostic.cpp')
    for path in [REPO/'validation/pinned-see-prototype-20261020/oracle-corpus.json',
                 REPO/'validation/pinned-see-prototype-20261020/supplement-oracle.json',
                 REPO/'validation/pin-see-coverage-20261020/oracle-corpus.json',
                 REPO/'validation/pin-see-coverage-20261020/known-limitation.json']:
        immutable[str(path)] = sha(path)
        shutil.copy2(path,inputs/(path.parent.name+'-'+path.name))
    RECORD['immutable_input_sha256_before'] = immutable
    run('compile-api-driver',['/usr/bin/c++',*flags,'-I'+str(src/'include'),'-c',OUT/'see_diagnostic.cpp','-o',OUT/'see_diagnostic.o'],60)
    for label,core in [('reference',reference_core),('mask',mask_core)]:
        exe=OUT/('see-'+label)
        run('link-api-'+label,['/usr/bin/c++',*flags,OUT/'see_diagnostic.o',core,'-pthread','-o',exe],60)
        run('api-'+label,[exe,inputs/'all316.tsv'],15,engine=True)
    ref=(OUT/'api-reference.stdout').read_bytes(); mask=(OUT/'api-mask.stdout').read_bytes()
    RECORD['byte_identical_api_stdout'] = ref==mask
    assert ref==mask
    rows=list(csv.DictReader(ref.decode().splitlines(),delimiter='\t'))
    assert len(rows)==316
    assert sum(r['initial_legal']=='0' for r in rows)==2
    for r in rows:
        if r['id'].startswith('inherited_recapture_promotion_'):
            assert r['static_exchange']=='-400' and r['ge-500']=='1'
    RECORD['api_rows'] = len(rows)
    RECORD['threshold_answers_compared'] = len(rows)*20
    RECORD['known_promotion_limitations_preserved'] = True
    RECORD['original_core_sha256_after'] = sha(original_core)
    RECORD['original_source_files_unchanged'] = all(sha(ORIGINAL_SOURCE/p)==h for p,h in expected.items())
    RECORD['immutable_input_sha256_after'] = {p:sha(p) for p in immutable}
    assert RECORD['original_core_sha256_after']==RECORD['original_core_sha256_before']
    assert RECORD['original_source_files_unchanged']
    assert RECORD['immutable_input_sha256_after']==immutable
    RECORD['artifact_sha256'] = {p.name:sha(p) for p in [reference_core,mask_core,OUT/'see-reference',OUT/'see-mask',OUT/'mask-board.cpp.o',OUT/'see_diagnostic.o']}
    RECORD['status']='PASS_BYTE_IDENTICAL_API_PARITY'
    RECORD['completed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat(); save()
    print(json.dumps({k:RECORD[k] for k in ['status','api_rows','threshold_answers_compared','known_promotion_limitations_preserved','engine_elapsed_seconds']}))
except BaseException as exc:
    RECORD['status']='FAILED_PRESERVE_ATTEMPT'
    RECORD['error']=repr(exc); save(); raise
