#!/usr/bin/env python3
"""Read-only Forge depth and WAC screens; subprocess argv only, never a shell.

Historical imports are observations, not engine reruns or strength evidence.
WAC parsing/legality uses python-chess, as the supplied tactics.py does.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import queue
import re
import shutil
import signal
import subprocess
import sys
import threading
import time

DEPTHS = (11, 13, 16, 20, 22)
FIXED_REFS = dict(zip(DEPTHS, (308972, 745494, 2460422, 11901452, 31111774)))
WAC_SHA256 = '9bfb7b42cf5bbc7f3d60ff767ca3be460e0ae4d9110ef9a71ddf0bd7071d4d46'
BENCH = re.compile(r'info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)')
CORE = {'Threads': 1, 'Hash': 16, 'OwnBook': False}

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(65536), b''): h.update(chunk)
    return h.hexdigest()

def unique_object(pairs):
    result = {}
    for k, v in pairs:
        if k in result: raise ValueError('duplicate JSON key: ' + k)
        result[k] = v
    return result

def parse_json(text): return json.loads(text, object_pairs_hook=unique_object)

def option_commands(options):
    if not isinstance(options, dict): raise ValueError('options must be a JSON object')
    if set(options) & set(CORE): raise ValueError('Threads/Hash/OwnBook are fixed core settings')
    commands = []
    for name, value in {**CORE, **options}.items():
        if not isinstance(name, str) or not name or name != ' '.join(name.split()) or 'value' in name.split() or any(c in name for c in '\r\n\x00'):
            raise ValueError('invalid UCI option name')
        if type(value) is bool: text = 'true' if value else 'false'
        elif type(value) is int: text = str(value)
        elif type(value) is float and math.isfinite(value): text = str(value)
        elif isinstance(value, str): text = value
        else: raise ValueError('option value must be a finite scalar')
        if not text or any(c.isspace() or ord(c) < 32 for c in text): raise ValueError('option value must be one UCI token')
        commands.append('setoption name ' + name + ' value ' + text)
    return commands

def parse_bench(lines, depth):
    matches = [BENCH.fullmatch(line) for line in lines if BENCH.fullmatch(line)]
    if len(matches) != 1: raise ValueError('expected exactly one bench summary')
    match = matches[0]
    if int(match[1]) != depth or int(match[2]) <= 0: raise ValueError('wrong bench depth or nonpositive nodes')
    return int(match[2])

def compare_nodes(off, on):
    if set(off) != set(DEPTHS) or set(on) != set(DEPTHS): raise ValueError('all five depths required')
    if any(type(n) is not int or n <= 0 for n in [*off.values(), *on.values()]): raise ValueError('positive integer nodes required')
    changed = [d for d in DEPTHS if off[d] != on[d]]
    # Integer arithmetic makes the strict >20% boundary exact.
    flags = [d for d in (20, 22) if abs(on[d] - off[d]) * 5 > off[d]]
    d = changed[0] if changed else None
    return {'guard_status': 'FAIL' if flags else 'PASS', 'guard_depths': flags,
            'guard_rule': 'abs(ON/OFF - 1) > 0.20 at d20 or d22',
            'percent_change': {str(d): 100 * (on[d] - off[d]) / off[d] for d in DEPTHS},
            'pc_precheck': {'depth': d, 'off_nodes': off[d], 'on_nodes': on[d]} if d else None,
            'option_live': bool(changed)}

def import_p23b(root):
    root = Path(root).resolve(strict=True)
    bench = root / '12_strength/p23b_refutlmr_h256/artifacts/bench.log'
    table = root / '19_screen_ref_p23b/README_p23b_lock_table.md'
    inputs = {str(p): sha(p) for p in (bench, table)}
    series = {}
    for line in bench.read_text().splitlines():
        match = re.fullmatch(r'\d{4}-\d\d-\d\d \d\d:\d\d:\d\d \S+ (\S+) (info string bench .*)', line)
        if not match: raise ValueError('unrecognized supplied bench row')
        summary = BENCH.fullmatch(match[2])
        if not summary: raise ValueError('malformed supplied bench summary')
        depth = int(summary[1]); group = series.setdefault(match[1], {})
        if depth in group: raise ValueError('duplicate supplied series depth')
        group[depth] = parse_bench([match[2]], depth)
    expected = {'LOCK','REL_OFF','EXP_OFF','EXP_RefutLmr=1','REL_RefutLmr=1'}
    if set(series) != expected: raise ValueError('unexpected supplied P23b series')
    for name, row in series.items():
        compare_nodes(FIXED_REFS, row)
        if name in ('LOCK','REL_OFF','EXP_OFF') and row != FIXED_REFS: raise ValueError('supplied OFF reference mismatch')
    settings = {}
    table_text = table.read_text()
    section = table_text.split('## Deep-node screen (',1)[1].split('\n## ',1)[0]
    for line in section.splitlines():
        if not re.match(r'^\| (?:\*\*)?m[134] r[4-7]', line): continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        label = cells[0].replace('**', '')
        name = re.match(r'm[134] r[4-7]', label)[0]
        nodes = {d: int(cells[i+1]) for i, d in enumerate(DEPTHS)}
        if name in settings: raise ValueError('duplicate supplied table setting')
        settings[name] = {**compare_nodes(FIXED_REFS, nodes), 'nodes': {str(d):nodes[d] for d in DEPTHS},
                          'historical_label': cells[6], 'historical_variant': label,
                          'evidence_kind': 'SUPPLIED_DOCUMENTARY_TABLE_NO_INDIVIDUAL_RAW_LOG'}
    if len(settings) != 12: raise ValueError('expected twelve P23b table settings')
    primary = {int(d): n for d,n in settings['m1 r5']['nodes'].items()}
    if primary != series['REL_RefutLmr=1'] or primary != series['EXP_RefutLmr=1']: raise ValueError('documentary primary differs from raw artifact')
    return {'evidence_kind':'SUPPLIED_ARTIFACT_IMPORT_NO_RERUN', 'import_status':'PASS',
            'artifact_series':{name:{str(d):row[d] for d in DEPTHS} for name,row in series.items()},
            'settings':settings, 'input_sha256':inputs,
            'interpretation':'Current absolute deep guard supersedes historical acceptance labels; no native rerun, WAC rerun, or Elo claim.'}

def load_wac(path):
    try: chess = importlib.import_module('chess')
    except ImportError as exc: raise ValueError('python-chess is required for WAC EPD parsing and legality; no engine launched') from exc
    path = Path(path).resolve(strict=True)
    digest = sha(path)
    if digest != WAC_SHA256: raise ValueError('WAC300 suite SHA256 differs from supplied x_wacnew.epd')
    rows = []; ids = set(); multiple = 0
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip(): continue
        try:
            board, ops = chess.Board.from_epd(line)
            pid = ops['id']; bm = ops.get('bm', []); am = ops.get('am', [])
            if not board.is_valid() or not isinstance(pid, str) or pid in ids or not bm: raise ValueError('invalid board, duplicate ID, or missing bm')
            if any(m not in board.legal_moves for m in [*bm,*am]): raise ValueError('illegal bm/am move')
        except Exception as exc: raise ValueError('EPD parse error at line %d: %s' % (number,exc)) from exc
        ids.add(pid); multiple += len(bm)>1
        rows.append({'id':pid,'board':board,'bm':set(bm),'am':set(am)})
    if len(rows) != 300 or ids != {'WAC.%03d'%n for n in range(1,301)}: raise ValueError('expected exact 300 WAC.001..WAC.300 positions')
    return rows, {'path':str(path),'sha256':digest,'bytes':path.stat().st_size,'positions':len(rows),
                  'unique_ids':len(ids),'valid_boards':len(rows),'legal_bm_am':True,'parse_exceptions':[],
                  'multiple_bm_positions':multiple,'chess_version':chess.__version__,
                  'chess_module':str(Path(chess.__file__).resolve()), 'chess_module_sha256':sha(chess.__file__)}

def score_bestmove(row, text):
    chess = importlib.import_module('chess')
    result = {'id':row['id'],'bestmove_uci':text,'legal':False,'bestmove_allowed':False,'exception':None,
              'bm_uci':sorted(m.uci() for m in row['bm']),'am_uci':sorted(m.uci() for m in row['am'])}
    try:
        move = chess.Move.from_uci(text)
        result['legal'] = move in row['board'].legal_moves
        result['bestmove_allowed'] = result['legal'] and (not row['bm'] or move in row['bm']) and move not in row['am']
        if not result['legal']: result['exception'] = 'illegal bestmove for original EPD position'
    except (ValueError, TypeError) as exc: result['exception'] = type(exc).__name__ + ': ' + str(exc)
    return result

class Capture:
    """One child per exchange; every child is quit/terminated/killed and waited."""
    def __init__(self, out, argv, timeout, max_output_bytes=4*1024*1024):
        self.out, self.argv, self.timeout = out, argv, timeout
        if max_output_bytes <= 0: raise ValueError('capture limit must be positive')
        self.max_output_bytes = max_output_bytes
        self.records = []

    def exchange(self, label, operation, postcheck=None):
        prefix = '%03d_%s' % (len(self.records),label)
        streams = {'stdout': bytearray(), 'stderr': bytearray()}; events = queue.Queue(); sent = []
        overflow = threading.Event()
        p = subprocess.Popen(self.argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             bufsize=0, cwd=self.out, start_new_session=(os.name=='posix'),
                             env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(self.out)))
        def reader(name):
            pending = b''
            try:
                for data in iter(lambda:getattr(p,name).read(65536),b''):
                    room = self.max_output_bytes-len(streams[name])
                    streams[name].extend(data[:room])
                    if len(data)>room:
                        overflow.set(); events.put(('limit',name)); break
                    if name == 'stdout':
                        pending += data
                        while b'\n' in pending:
                            line,pending = pending.split(b'\n',1); events.put(('line',line+b'\n'))
                if name=='stdout' and pending: events.put(('line',pending))
            finally:
                getattr(p,name).close()
                if name == 'stdout': events.put(('eof',None))
        threads = [threading.Thread(target=reader,args=(name,),daemon=True) for name in streams]
        for t in threads: t.start()
        def send(line):
            if any(c in line for c in '\r\n\x00'): raise ValueError('invalid command line')
            data = (line+'\n').encode(); sent.append(data); p.stdin.write(data); p.stdin.flush()
        def until(predicate, timeout=None):
            deadline = time.monotonic() + (self.timeout if timeout is None else timeout); lines = []
            while True:
                remain = deadline-time.monotonic()
                if remain <= 0: raise TimeoutError('deadline waiting for engine reply')
                try: kind, data = events.get(timeout=remain)
                except queue.Empty as exc: raise TimeoutError('deadline waiting for engine reply') from exc
                if kind == 'eof': raise RuntimeError('stdout EOF before expected reply')
                if kind == 'limit': raise RuntimeError('engine output capture limit exceeded')
                line = data.decode('utf-8','strict').rstrip('\r\n'); lines.append(line)
                if line.startswith(('info string unknown option','info string invalid value')): raise RuntimeError(line)
                if predicate(line): return lines
        value = None; error = None; timed_out = False; cleanup = 'quit'; started = time.monotonic()
        try: value = operation(send,until)
        except Exception as exc:
            error = type(exc).__name__ + ': ' + str(exc); timed_out = isinstance(exc,TimeoutError)
        finally:
            grace = min(self.timeout,1.0)
            try:
                if p.poll() is None: send('quit')
                p.stdin.close(); p.wait(timeout=grace)
            except (OSError, subprocess.TimeoutExpired) as exc:
                timed_out = timed_out or isinstance(exc,subprocess.TimeoutExpired)
                cleanup = 'terminate'
                try:
                    if os.name=='posix': os.killpg(p.pid,signal.SIGTERM)
                    else: p.terminate()
                except ProcessLookupError: pass
                try: p.wait(timeout=grace)
                except subprocess.TimeoutExpired:
                    cleanup = 'kill'
                    try:
                        if os.name=='posix': os.killpg(p.pid,signal.SIGKILL)
                        else: p.kill()
                    except ProcessLookupError: pass
                    p.wait(timeout=2)
                finally:
                    if not p.stdin.closed: p.stdin.close()
            # The leader may have exited while descendants retain our pipes.
            # This process group was created exclusively for this exchange.
            descendant_cleanup = False
            if os.name=='posix':
                try:
                    os.killpg(p.pid,signal.SIGKILL); descendant_cleanup = True
                except ProcessLookupError: pass
            for t in threads: t.join(timeout=2)
        complete = not any(t.is_alive() for t in threads)
        if error is None and postcheck is not None:
            try: value = postcheck(bytes(streams['stdout']).decode('utf-8','strict').splitlines())
            except Exception as exc: error = type(exc).__name__+': '+str(exc)
        row = {'label':label,'argv':self.argv,'pid':p.pid,'returncode':p.returncode,'timed_out':timed_out,
               'timeout_seconds':self.timeout,'error':error,'cleanup':cleanup,'child_waited':p.returncode is not None,
               'capture_complete':complete,'descendant_group_killed':descendant_cleanup,
               'output_truncated':overflow.is_set(),'max_output_bytes_per_stream':self.max_output_bytes,
               'elapsed_seconds':time.monotonic()-started}
        for name,data in [('stdin',b''.join(sent)),('stdout',bytes(streams['stdout'])),('stderr',bytes(streams['stderr']))]:
            target = self.out/(prefix+'.'+name); target.write_bytes(data)
            row[name] = {'path':target.name,'bytes':len(data),'sha256':sha(target)}
        diagnostics = any(b'info string unknown option' in data or b'info string invalid value' in data for data in streams.values())
        row['status'] = 'PASS' if error is None and p.returncode==0 and complete and cleanup=='quit' and not timed_out and not overflow.is_set() and not streams['stderr'] and not diagnostics else 'FAIL'
        self.records.append(row)
        # Keep receipts even if the caller or a later exchange fails.
        (self.out/'processes.json').write_text(json.dumps(self.records,indent=2)+'\n')
        return value, row

def configure(send, until, commands, allow_unadvertised):
    send('uci'); handshake = until(lambda line:line=='uciok')
    names = set()
    for line in handshake:
        match = re.match(r'^option name (.+) type (?:spin|check|button|string|combo)(?: |$)',line)
        if match: names.add(match[1])
    for command in commands:
        name = command[len('setoption name '):].split(' value ',1)[0]
        if name not in names and name not in allow_unadvertised: raise ValueError('option not advertised: '+name+'; use an explicit source-grounded allowlist for release tunables')
    for command in commands: send(command)
    send('isready'); until(lambda line:line=='readyok')
    return names

def engine_argv(text):
    argv = parse_json(text)
    if not isinstance(argv,list) or not argv or any(not isinstance(a,str) or not a or '\x00' in a for a in argv): raise ValueError('engine argv must be a nonempty JSON string list')
    resolved = shutil.which(argv[0])
    if resolved is None: raise ValueError('engine executable not found')
    argv[0] = str(Path(resolved).resolve(strict=True))
    return argv

def identity(argv):
    paths = [Path(a) for a in argv if Path(a).is_file()]
    return {str(p.resolve()):sha(p) for p in paths}

def first_bench(cap):
    def operation(send,until):
        send('bench 11')
        return parse_bench(until(lambda line:bool(BENCH.fullmatch(line))),11)
    return cap.exchange('FIRST_BARE_BENCH11',operation,lambda lines:parse_bench(lines,11))

def runtime(args, out):
    argv = engine_argv(args.engine_argv_json); before = identity(argv)
    cap = Capture(out,argv,args.timeout)
    result = {'status':'FAIL','mode':args.mode,'engine_argv':argv,'input_sha256_before':before,
              'interpretation':'Screen only; no Elo claim. Recorded bestmoves are engine outputs for original EPD positions.'}
    allow_unadvertised = parse_json(args.allow_unadvertised_options_json)
    if not isinstance(allow_unadvertised,list) or any(not isinstance(n,str) or not n for n in allow_unadvertised): raise ValueError('unadvertised allowlist must be a JSON string list')
    result['caller_allowed_unadvertised_options'] = allow_unadvertised
    if args.expected_engine_sha256 and sha(argv[0]) != args.expected_engine_sha256: raise ValueError('engine executable SHA256 mismatch')
    # Parse and validate every input before the very first engine process.
    if args.mode == 'sweep':
        off_options = parse_json(args.off_options_json); on_options = parse_json(args.on_options_json)
        off_commands = option_commands(off_options); on_commands = option_commands(on_options)
        result.update(off_options=off_options,on_options=on_options)
    else:
        commands = option_commands(parse_json(args.options_json)); positions, suite = load_wac(args.suite)
        result.update(suite=suite,movetime_ms=args.movetime_ms,results=[])
    try:
        nodes, receipt = first_bench(cap)
        result['first_bare_bench11_nodes'] = nodes
        if receipt['status'] != 'PASS' or (args.reference=='lock' and nodes != FIXED_REFS[11]):
            raise RuntimeError('first bare bench11 process/signature failed; UCI not started')
        if any(not Path(path).is_file() or sha(path)!=digest for path,digest in before.items()): raise RuntimeError('input file changed after first bare bench; UCI not started')
        if args.mode == 'sweep':
            series = {'off':{},'on':{}}
            for side,commands in [('off',off_commands),('on',on_commands)]:
                for depth in DEPTHS:
                    def operation(send,until):
                        configure(send,until,commands,allow_unadvertised)
                        send('bench %d'%depth)
                        return parse_bench(until(lambda line:bool(BENCH.fullmatch(line))),depth)
                    value, receipt = cap.exchange('%s_d%d'%(side,depth),operation,lambda lines:parse_bench(lines,depth))
                    if receipt['status'] != 'PASS': raise RuntimeError('%s d%d process failed: %s'%(side,depth,receipt['error']))
                    series[side][depth] = value
                    result[side+'_nodes'] = {str(d):n for d,n in series[side].items()}
            comparison = compare_nodes(series['off'],series['on'])
            reference_ok = args.reference=='none' or series['off']==FIXED_REFS
            live_ok = off_options==on_options or comparison['option_live']
            result.update(off_nodes={str(d):n for d,n in series['off'].items()},on_nodes={str(d):n for d,n in series['on'].items()},
                          comparison=comparison,reference_status='PASS' if reference_ok else 'FAIL',
                          option_live_required=off_options!=on_options,
                          status='PASS' if reference_ok and live_ok and comparison['guard_status']=='PASS' else 'FAIL')
            if not live_ok: result['failure']='different option sets were inert across all five depths; option live check failed'
        else:
            def operation(send,until):
                names = configure(send,until,commands,allow_unadvertised)
                if 'Clear Hash' not in names: raise ValueError('Clear Hash not advertised')
                for row in positions:
                    send('ucinewgame'); send('setoption name Clear Hash'); send('isready'); until(lambda line:line=='readyok')
                    send('position fen '+row['board'].fen()); send('go movetime %d'%args.movetime_ms)
                    lines = until(lambda line:line.startswith('bestmove '),timeout=args.timeout+args.movetime_ms/1000)
                    tokens = lines[-1].split()
                    if len(tokens) not in (2,4) or (len(tokens)==4 and tokens[2]!='ponder'): raise ValueError('malformed bestmove line')
                    result['results'].append(score_bestmove(row,tokens[1]))
            _, receipt = cap.exchange('wac300_fixedtime',operation)
            illegal = sum(not row['legal'] for row in result['results'])
            result.update(evaluated=len(result['results']),solved=sum(row['bestmove_allowed'] for row in result['results']),
                          illegal_moves=illegal,exceptions=[{'id':r['id'],'exception':r['exception']} for r in result['results'] if r['exception']],
                          status='PASS' if receipt['status']=='PASS' and len(result['results'])==300 and not illegal else 'FAIL')
            if sha(args.suite)!=suite['sha256']: raise RuntimeError('suite changed during run')
    except Exception as exc:
        result.update(status='FAIL',failure=type(exc).__name__+': '+str(exc))
    result['processes'] = cap.records
    after = {}
    for path in before:
        try: after[path] = sha(path)
        except OSError as exc: after[path] = {'error':type(exc).__name__+': '+str(exc)}
    result['input_sha256_after'] = after
    if before != after: result.update(status='FAIL',failure='input file changed during run')
    return result

def new_out(path):
    path = Path(path).absolute()
    if path.resolve() != path or os.path.lexists(path) or not path.parent.is_dir(): raise ValueError('output must be NEW with existing nonsymlink parent')
    if any(p=='baseline' or p.startswith('dist-v') for p in path.parts): raise ValueError('protected output directory')
    path.mkdir(); return path

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode',required=True)
    p = sub.add_parser('p23b-import'); p.add_argument('--source-root',type=Path,required=True)
    p = sub.add_parser('wac-validate'); p.add_argument('--suite',type=Path,required=True)
    for mode in ('sweep','wac300'):
        p = sub.add_parser(mode)
        p.add_argument('--engine-argv-json',required=True)
        p.add_argument('--expected-engine-sha256')
        p.add_argument('--allow-unadvertised-options-json',default='[]',help='Explicit source-grounded release tunable names; captured as caller declarations, not engine validation')
        p.add_argument('--timeout',type=float,default=120.0)
        p.add_argument('--reference',choices=('lock','none'),default='lock')
        if mode=='sweep':
            p.add_argument('--off-options-json',default='{}'); p.add_argument('--on-options-json',default='{}')
        else:
            p.add_argument('--options-json',default='{}'); p.add_argument('--suite',type=Path,required=True)
            p.add_argument('--movetime-ms',type=int,default=1000)
    for p in sub.choices.values(): p.add_argument('--out',type=Path,required=True)
    args = parser.parse_args(argv)
    if hasattr(args,'timeout') and (not math.isfinite(args.timeout) or args.timeout<=0): raise ValueError('timeout must be finite and positive')
    if hasattr(args,'movetime_ms') and args.movetime_ms<=0: raise ValueError('movetime must be positive')
    out = new_out(args.out)
    if args.mode=='p23b-import': result=import_p23b(args.source_root)
    elif args.mode=='wac-validate': _, proof=load_wac(args.suite); result={'status':'PASS','mode':args.mode,'suite':proof,'engine_execution':False}
    else: result=runtime(args,out)
    result['tool_sha256'] = sha(Path(__file__).resolve())
    result['invocation_argv'] = [sys.executable,*sys.argv] if argv is None else [str(Path(__file__).resolve()),*argv]
    (out/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    (out/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(out.iterdir()) if p.is_file() and p.name!='SHA256SUMS.txt'))
    status = result.get('status',result.get('import_status','FAIL'))
    print(json.dumps({'status':status,'mode':args.mode,'out':str(out),'result_sha256':sha(out/'result.json')}))
    return 0 if status=='PASS' else 1

if __name__=='__main__':
    try: raise SystemExit(main())
    except (OSError,ValueError,TypeError,KeyError) as exc:
        print('ERROR: '+str(exc),file=sys.stderr); raise SystemExit(1)
