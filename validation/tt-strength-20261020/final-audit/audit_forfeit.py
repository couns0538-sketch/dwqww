#!/usr/bin/env python3
"""Offline audit of untouched original failed TT run; never executes archived code."""
from pathlib import Path, PurePosixPath
import collections, datetime, gzip, hashlib, importlib.util, io, json, re, statistics, subprocess, tarfile
import chess
ROOT=Path('/workspace/dwqww')
OUT=Path(__file__).resolve().parent
DATA=Path('/workspace/.cloud-setup/tt-strength-final-39403471059/verified/files')
RESULT_REF='origin/results/tt-strength-39403471059-1'
LAUNCH='b48af4c3882d7c20ef3fe5bceea6fe2ae8a7d893'
SOURCES={'baseline':'c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e','candidate':'8865666cc0ab4961cd507bae40ff6ce44e9319df'}
checks=[]
def sha(b): return hashlib.sha256(b).hexdigest()
def digest(p): return sha(Path(p).read_bytes())
def check(name, condition, details=None):
    checks.append({'name':name,'passed':bool(condition),'details':details})
    if not condition: raise AssertionError(name)
def git(*args, cwd=ROOT): return subprocess.check_output(['git',*args],cwd=cwd)
def save(p,x): p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
summary=json.loads((DATA/'strength/summary.json').read_text())
for label,source in SOURCES.items():
    archive=(DATA/f'source/{label}.tar').read_bytes()
    actual=git('archive',source,'CMakeLists.txt','LICENSE','src','include','tests','bench','tools')
    check(label+'_source_tar_matches_git_archive',archive==actual,{'source':source,'sha256':sha(archive)})
    provenance=json.loads((DATA/f'{label}-build-provenance.json').read_text())
    check(label+'_source_commit',provenance['source_commit']==source)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        hashes={r.name:sha(tar.extractfile(r).read()) for r in tar if r.isfile()}
    check(label+'_all_source_hashes',hashes==provenance['exported_source_sha256'],len(hashes))
    commands=json.loads((DATA/f'{label}-compile-commands.json').read_text())
    for i,c in enumerate(commands):
        text=c.get('command',' '.join(c.get('arguments',[])))
        check(f'{label}_compile_flags_{i}',all(x in text for x in ['-O3','-DNDEBUG','-march=x86-64-v3','-mtune=generic','-fno-fast-math','-ffp-contract=off','-fno-lto']) and '-ffast-math' not in text)
    log=(DATA/f'{label}-LastTest.log').read_text()
    # CTest's original LastTest format has one Passed marker per completed suite.
    check(label+'_ctest_9_passed',log.count('Test Passed.')==9 and 'Test Failed.' not in log)
runner_archive=(DATA/'source/fastchess.tar').read_bytes()
check('pinned_fastchess_source_archive',runner_archive==git('archive','60d7a7a26c6b0582a15c112fb29a1829bef2adb3',cwd=Path('/workspace/.cloud-setup/fastchess')))
for rel,expected in json.loads((DATA/'artifacts-SHA256.json').read_text()).items():
    check('actual_artifact_'+rel,digest(DATA/'artifacts'/rel)==expected,expected)
for rel in ['workflow.yml','windows_validate.py']:
    target='.github/workflows/forge-hosted-tt-strength.yml' if rel=='workflow.yml' else 'tools/match/windows_validate.py'
    check('launch_blob_'+target,(DATA/rel).read_bytes()==git('show',LAUNCH+':'+target))
for p in sorted((DATA/'package').rglob('*')):
    if p.is_file():
        rel=str(p.relative_to(DATA/'package'))
        check('launch_package_'+rel,p.read_bytes()==git('show',LAUNCH+':.github/hosted-tt-strength/'+rel))
final=summary['final_input_rehash']
check('final_input_rehash_passed',final['status']=='passed')
for original,row in final['inputs'].items():
    if '/hosted-results/' in original: path=DATA/original.split('/hosted-results/',1)[1]
    elif '/.github/hosted-tt-strength/' in original: path=DATA/'package'/original.split('/.github/hosted-tt-strength/',1)[1]
    elif original.endswith('/.github/workflows/forge-hosted-tt-strength.yml'): path=DATA/'workflow.yml'
    elif original.endswith('/tools/match/windows_validate.py'): path=DATA/'windows_validate.py'
    else: raise AssertionError('Unmapped original path '+original)
    check('frozen_input_'+original,digest(path)==row['expected_sha256']==row['actual_sha256'] and row['matches'])
bench=[]
for i in range(8):
    r=json.loads((DATA/f'strength/bench-{i:02}.json').read_text());bench.append(r)
    check(f'bench{i}_signature_and_stderr',r['engine_nodes']==419798 and (DATA/f'strength/bench-{i:02}.stderr').stat().st_size==0)
for key in ['cpu_seconds','wall_seconds']:
    ratios=[bench[i+1][key]/bench[i][key] for i in [2,4,6]]
    native=summary['bench_aa'][key]
    check(key+'_aa_ratios',ratios==native['ratios'] and statistics.median(ratios)==native['median'] and native['pass'] and .95<=statistics.median(ratios)<=1.05 and all(.85<=v<=1.15 for v in ratios),ratios)
raw=DATA/'strength/sprt/fastchess.log';original=raw.read_bytes();lines=original.splitlines(keepends=True)
text=original.decode();faults=[{'line':i+1,'text':line.decode().rstrip('\n')} for i,line in enumerate(lines) if re.search(rb'^\[(?:WARN(?:ING)?|ERR(?:OR)?|FATAL)\s*\]',line,re.I)]
check('one_exact_failure_warning',len(faults)==1 and 'Engine Baseline loses on time by 45ms' in faults[0]['text'],faults)
end=faults[0]['line']-1
exits=[i for i,line in enumerate(lines[:end]) if b'Process exited normally with status 0' in line]
start=exits[-1]+1
session=b''.join(lines[start:]);(OUT/'game85-original-protocol.log.gz').write_bytes(gzip.compress(session,mtime=0))
# Original outgoing stdin is retained separately per engine; this is an extraction,
# not a reconstructed PGN or executed replay.
inputs={}
for engine in ['Baseline','Candidate']:
    msgs=[]
    for line in lines[start:]:
        marker=('  '+engine+' <--- ').encode()
        if marker in line: msgs.append(line.split(marker,1)[1])
    blob=b''.join(msgs);(OUT/(f'game85-{engine.lower()}-original-input.txt')).write_bytes(blob);inputs[engine]={'commands':len(msgs),'sha256':sha(blob)}
goidx=[i for i,line in enumerate(lines[:end]) if b'  Baseline <--- go ' in line][-1]
posidx=[i for i,line in enumerate(lines[:goidx]) if b'  Baseline <--- position ' in line][-1]
pos=lines[posidx].decode().split('  Baseline <--- ',1)[1].rstrip('\n')
words=pos.split();assert words[:2]==['position','fen'];board=chess.Board(' '.join(words[2:8]));moves=words[9:]
for move in moves: board.push_uci(move)
bestidx=next(i for i in range(goidx+1,len(lines)) if b'  Baseline ---> bestmove ' in lines[i])
best=lines[bestidx].decode().split('bestmove ',1)[1].split()[0];check('final_bestmove_legal',chess.Move.from_uci(best) in board.legal_moves)
def timestamp(i):
    return re.match(rb'^\[[^\]]+\] \[([^\]]+)\]',lines[i])[1].decode()
def stamp_seconds(x):
    h,m,s=x.split(':');return int(h)*3600+int(m)*60+float(s)
go=lines[goidx].decode().split('  Baseline <--- ',1)[1].strip();clock_words=go.split();clock={clock_words[i]:int(clock_words[i+1]) for i in range(1,len(clock_words),2)}
lastinfo=[i for i in range(goidx+1,bestidx) if b'  Baseline ---> info depth ' in lines[i]][-1]
info=lines[lastinfo].decode().split('  Baseline ---> ',1)[1].strip();info_ms=int(re.search(r'\btime (\d+)',info)[1]);wall_ms=(stamp_seconds(timestamp(bestidx))-stamp_seconds(timestamp(goidx)))*1000
forensic={'original_log_sha256':sha(original),'original_log_bytes':len(original),'original_log_lines':len(lines),'game85_original_session_start_line':start+1,'session_original_bytes':len(session),'session_original_sha256':sha(session),'faults':faults,'baseline_input_file':'game85-baseline-original-input.txt','candidate_input_file':'game85-candidate-original-input.txt','extracted_input_records':inputs,'final_search':{'position_command_original':pos,'initial_fen':' '.join(words[2:8]),'previous_legal_plies':len(moves),'current_fen':board.fen(),'current_fen_strict_ep':board.fen(en_passant='fen'),'side_to_move':'white' if board.turn else 'black','go_command_original':go,'go_line':goidx+1,'go_observed_time':timestamp(goidx),'clock_ms':clock,'last_info_line':lastinfo+1,'last_info_original':info,'last_info_observed_time':timestamp(lastinfo),'last_info_reported_ms':info_ms,'bestmove_line':bestidx+1,'bestmove_original':lines[bestidx].decode().rstrip('\n'),'bestmove_observed_time':timestamp(bestidx),'go_to_observed_bestmove_ms':wall_ms,'warning_line':end+1,'warning_observed_time':timestamp(end),'bestmove_is_legal':True,'computed_source_budget':{'overhead':10,'available':53,'soft':17,'hard':31,'parameters':{'TmSoftDivisor':22,'TmIncrementPercent':75,'TmHardPercent':60,'TmHardSoftMultiple':5},'poll_node_mask':1023}},'process_normal_exit_counts':dict(collections.Counter(re.findall(r'<stderr> (Candidate|Baseline) ---> Process exited normally with status 0',text))),'interpretation':'Actual baseline end-to-end time forfeit invalidates the entire attempt. Last completed iteration time does not reveal later unfinished work, output/transport/read delay or scheduling. No causal attribution or Elo gain follows; no archived engine was executed.'}
save(OUT/'forfeit-exchange.json',forensic)
# Source clock invariants: before TT synchronization change, the same receipt epoch
# and main timer-polling body were already present in both frozen engine sources.
old=git('show',SOURCES['baseline']+':src/search.cpp').decode();new=git('show',SOURCES['candidate']+':src/search.cpp').decode()
for begin,finish in [('std::int64_t Worker::elapsed_ms() const {','std::uint64_t Worker::total_nodes() const {'),('bool Worker::should_stop() {','bool Worker::is_draw(')]:
    a=old[old.index(begin):old.index(finish,old.index(begin))];b=new[new.index(begin):new.index(finish,new.index(begin))];check('unchanged_clock_body_'+begin,a==b)
for engine in ['Baseline','Candidate']:
    check(engine+'_all_85_sessions_exit_normal',forensic['process_normal_exit_counts'][engine]==85)
check('failure_summary_no_acceptance',summary['status']=='failed_or_inconclusive_no_acceptance' and 'match_fail_fast' in summary['error'])
check('all_original_log_bytes_unchanged',raw.read_bytes()==original)
result={'status':'offline_integrity_and_forensics_passed_strength_attempt_invalid','run_id':39403471059,'results_commit':git('rev-parse',RESULT_REF).decode().strip(),'launch_sha':LAUNCH,'checks':checks,'check_count':len(checks),'all_checks_passed':all(x['passed'] for x in checks),'final_frozen_inputs':len(final['inputs']),'failure':'Baseline time forfeit by45ms in started game85; wrapper correctly fails fast','accepted_strength_result':False,'engine_or_game_execution_during_audit':False,'observations':forensic}
save(OUT/'forensic-audit.json',result)
print(json.dumps({k:result[k] for k in ['status','check_count','all_checks_passed','final_frozen_inputs','failure','accepted_strength_result']}))
