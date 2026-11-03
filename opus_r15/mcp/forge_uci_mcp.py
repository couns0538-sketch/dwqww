#!/usr/bin/env python3
"""forge_uci_mcp.py - Opus R15: a small MCP server (stdio, JSON-RPC 2.0, standard library only) for Forge work.

Tools: pin_check, uci_options, bench, perft, gate_summary, index_check, pc_status. It is a thin adapter over the R15
tools next to it (../tools): every engine it starts runs at Idle on CPUs 0-1 (the server lowers itself at start, so
children inherit both), it reads gate folders read-only, and it writes only small JSON files under its own tmp folder
(FORGE_MCP_TMP, default D:\\o15\\mcp\\tmp). Messages are newline-delimited JSON on stdin / stdout; logs go to stderr.

Run: C:\\Users\\Administrator\\grok-pc\\nnue\\.venv\\Scripts\\python.exe -I -B forge_uci_mcp.py
Register (user scope):  claude mcp add --scope user forge-uci -- <that python> -I -B <this file>
Self-test: python -I -B test_forge_uci_mcp.py
"""
import json
import os
import re
import subprocess
import sys
import time
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.normpath(os.path.join(HERE, '..', 'tools'))
sys.path.insert(0, TOOLS)
import gate_summary  # noqa: E402  (standard library only)

SERVER = {'name': 'forge-uci', 'version': '1.0.0'}
VERSIONS = ['2025-06-18', '2025-03-26', '2024-11-05']
TMP = os.environ.get('FORGE_MCP_TMP', r'D:\o15\mcp\tmp')
MASK = os.environ.get('FORGE_MCP_MASK', '0x3')
PY = sys.executable
KIWIPETE = 'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1'


def log(msg):
    print(f'forge-uci: {msg}', file=sys.stderr, flush=True)


def lower_self():
    """Idle class + CPU mask on this process, inherited by every engine it starts (Windows; fail closed)."""
    if os.name != 'nt':
        return
    import ctypes
    k32 = ctypes.windll.kernel32
    k32.GetCurrentProcess.restype = ctypes.c_void_p
    h = ctypes.c_void_p(k32.GetCurrentProcess())
    if not k32.SetPriorityClass(h, 0x40) or not k32.SetProcessAffinityMask(h, ctypes.c_size_t(int(MASK, 16))):
        log('cannot set Idle / CPU mask - exiting rather than running engines unprotected')
        sys.exit(3)


def need_exe(args):
    exe = str(args.get('exe', ''))
    if not exe or not os.path.isfile(exe):
        raise ValueError(f'exe not found: {exe!r}')
    return exe


def parse_options(text):
    opts = []
    for part in [p for p in str(text or '').split(';') if p.strip()]:
        if '=' not in part:
            raise ValueError(f'bad option {part!r} (want Name=Value)')
        n, v = part.split('=', 1)
        opts.append((n.strip(), v.strip()))
    return opts


def uci_session(exe, commands, until, timeout):
    """Run one engine, send `commands`, return its stdout once a line matches `until` (or the process ends)."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        out, err = p.communicate('\n'.join(commands + ['quit']) + '\n', timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        raise ValueError(f'engine did not finish within {timeout} s')
    return out, err


def t_uci_options(args):
    exe = need_exe(args)
    out, _ = uci_session(exe, ['uci'], 'uciok', 60)
    opts = []
    for line in out.splitlines():
        m = re.match(r'option name (.+?) type (\w+)(?: default (\S+))?(?: min (-?\d+) max (-?\d+))?', line)
        if m:
            opts.append({'name': m.group(1), 'type': m.group(2), 'default': m.group(3),
                         'min': int(m.group(4)) if m.group(4) else None, 'max': int(m.group(5)) if m.group(5) else None})
    ids = [l for l in out.splitlines() if l.startswith('id ')]
    return {'exe': exe, 'id': ids, 'options': opts, 'count': len(opts)}


def t_bench(args):
    exe = need_exe(args)
    depth = int(args.get('depth', 13))
    if not 1 <= depth <= 22:
        raise ValueError('depth must be 1..22')
    cmds = ['uci'] + [f'setoption name {n} value {v}' for n, v in parse_options(args.get('options'))] + ['isready', f'bench {depth}']
    t0 = time.time()
    out, _ = uci_session(exe, cmds, 'bench', 1800)
    m = re.search(r'info string bench depth (\d+) nodes (\d+)', out)
    if not m:
        raise ValueError('no bench line in the engine output')
    bad = [l for l in out.splitlines() if l.startswith(('info string invalid', 'info string unknown', 'info string error'))]
    return {'exe': exe, 'depth': depth, 'nodes': int(m.group(2)), 'options': args.get('options', ''),
            'engine_warnings': bad, 'seconds': round(time.time() - t0, 1)}


def t_perft(args):
    exe = need_exe(args)
    depth = int(args.get('depth', 5))
    if not 1 <= depth <= 6:
        raise ValueError('depth must be 1..6')
    fen = str(args.get('fen', 'startpos'))
    pos = 'position startpos' if fen == 'startpos' else ('position fen ' + (KIWIPETE if fen == 'kiwipete' else fen))
    out, _ = uci_session(exe, [pos, f'go perft {depth}'], 'nodes', 600)
    m = re.findall(r'^nodes (\d+)$', out, re.M)
    if not m:
        raise ValueError('no perft result (bad FEN?)')
    return {'exe': exe, 'fen': fen, 'depth': depth, 'nodes': int(m[-1])}


def t_pin_check(args):
    exe = need_exe(args)
    os.makedirs(TMP, exist_ok=True)
    js = os.path.join(TMP, f'pin_{uuid.uuid4().hex[:12]}.json')
    cmd = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', os.path.join(TOOLS, 'pin_check.ps1'),
           '-Exe', exe, '-Json', js, '-Mask', MASK]
    if args.get('full'):
        cmd.append('-Full')
    if args.get('options'):
        parse_options(args['options'])
        cmd += ['-Options', str(args['options'])]
    if args.get('expect'):
        cmd += ['-Expect', str(args['expect'])]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    rec = json.load(open(js, encoding='utf-8-sig')) if os.path.exists(js) else None
    if rec:
        rec.pop('transcript', None)
    return {'exit_code': p.returncode, 'output': p.stdout.strip(), 'record': rec}


def t_gate_summary(args):
    d = str(args.get('gate_dir', ''))
    if not os.path.isdir(d):
        raise ValueError(f'not a folder: {d!r}')
    o = gate_summary.summarise(d, bool(args.get('watch')), int(args.get('last_min', 60)))
    o.pop('printed', None)
    return {'text': gate_summary.fmt(o), 'summary': o}


def t_index_check(args):
    cmd = [PY, '-I', '-B', os.path.join(TOOLS, 'index_check.py')]
    if args.get('root'):
        cmd += ['--root', str(args['root'])]
    if args.get('no_engine'):
        cmd.append('--no-engine')
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    return {'exit_code': p.returncode, 'output': (p.stdout + p.stderr).strip()}


def t_pc_status(args):
    p = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', os.path.join(TOOLS, 'pc_gate.ps1'),
                        '-Drive', 'D', '-MaxCpu', '97', '-Cpus', '0,1', '-MaxMyCpu', '60'], capture_output=True, text=True, timeout=120)
    return {'exit_code': p.returncode, 'ok_to_start_heavy_work': p.returncode == 0, 'output': (p.stdout + p.stderr).strip()}


def schema(props, required=()):
    return {'type': 'object', 'properties': props, 'required': list(required), 'additionalProperties': False}


EXE = {'type': 'string', 'description': 'full path of a Forge exe'}
OPTS = {'type': 'string', 'description': "UCI options 'Name=Value;Name2=Value2' (optional)"}
TOOLSPEC = {
    'pin_check': (t_pin_check, 'Check a Forge exe against the lock pins (bench d11/13/16, +d20/22 with full; perft 5 '
                  'startpos + kiwipete). With options: the ON line must be advertised, accepted and live, perft = pins.',
                  schema({'exe': EXE, 'options': OPTS, 'full': {'type': 'boolean'},
                          'expect': {'type': 'string', 'description': "exact bench nodes 'd11=N,d13=N'"}}, ['exe'])),
    'uci_options': (t_uci_options, "List the options a Forge exe advertises in its 'uci' answer (name, type, default, "
                    'min, max) and its id lines.', schema({'exe': EXE}, ['exe'])),
    'bench': (t_bench, "Run 'bench <depth>' (1..22) on a Forge exe, optionally after setoption lines; returns the node "
              'count (Idle, CPUs 0-1).', schema({'exe': EXE, 'depth': {'type': 'integer', 'minimum': 1, 'maximum': 22},
                                                  'options': OPTS}, ['exe'])),
    'perft': (t_perft, "Run 'go perft <depth>' (1..6) on startpos, kiwipete or a FEN; returns the node count.",
              schema({'exe': EXE, 'depth': {'type': 'integer', 'minimum': 1, 'maximum': 6},
                      'fen': {'type': 'string', 'description': "'startpos', 'kiwipete' or a FEN"}}, ['exe'])),
    'gate_summary': (t_gate_summary, 'Summarise a fastchess gate folder (W/D/L, pentanomial, Elo, nElo, exact LLR, '
                     'time forfeits, illegal moves, disconnects, games/h, reproduction of the printed block); watch = '
                     'speed of a running gate.', schema({'gate_dir': {'type': 'string'}, 'watch': {'type': 'boolean'},
                                                         'last_min': {'type': 'integer', 'minimum': 10}}, ['gate_dir'])),
    'index_check': (t_index_check, 'Check every line of the R15 candidate INDEX (exe hashes, record checks, CI, '
                    'advertised option and ON range).', schema({'root': {'type': 'string'}, 'no_engine': {'type': 'boolean'}})),
    'pc_status': (t_pc_status, 'Free disk C:/D:/F:, total and per-CPU load, free RAM, and whether a heavy step may start '
                  '(the R14-B pc_gate rules: D: >= 51 GB, C: >= 50 GB, CPUs 0-1 <= 60 %).', schema({})),
}


def handle(msg):
    mid = msg.get('id')
    method = msg.get('method')
    if method == 'initialize':
        want = (msg.get('params') or {}).get('protocolVersion')
        return {'jsonrpc': '2.0', 'id': mid, 'result': {
            'protocolVersion': want if want in VERSIONS else VERSIONS[0],
            'capabilities': {'tools': {'listChanged': False}}, 'serverInfo': SERVER,
            'instructions': 'Forge chess engine checks on grok-pc: engines run at Idle on CPUs 0-1; read-only on gates.'}}
    if method == 'notifications/initialized' or (mid is None and str(method).startswith('notifications/')):
        return None
    if method == 'ping':
        return {'jsonrpc': '2.0', 'id': mid, 'result': {}}
    if method == 'tools/list':
        return {'jsonrpc': '2.0', 'id': mid, 'result': {'tools': [
            {'name': n, 'description': d, 'inputSchema': s} for n, (_, d, s) in TOOLSPEC.items()]}}
    if method == 'tools/call':
        params = msg.get('params') or {}
        name = params.get('name')
        if name not in TOOLSPEC:
            return {'jsonrpc': '2.0', 'id': mid, 'result': {
                'content': [{'type': 'text', 'text': f'unknown tool {name!r}'}], 'isError': True}}
        try:
            res = TOOLSPEC[name][0](params.get('arguments') or {})
            return {'jsonrpc': '2.0', 'id': mid, 'result': {
                'content': [{'type': 'text', 'text': json.dumps(res, indent=1)}], 'structuredContent': res, 'isError': False}}
        except (ValueError, OSError, subprocess.SubprocessError) as e:
            return {'jsonrpc': '2.0', 'id': mid, 'result': {
                'content': [{'type': 'text', 'text': f'{name} failed: {e}'}], 'isError': True}}
    if mid is None:
        return None
    return {'jsonrpc': '2.0', 'id': mid, 'error': {'code': -32601, 'message': f'Method not found: {method}'}}


def main():
    lower_self()
    log(f"ready ({len(TOOLSPEC)} tools, mask {MASK}, Idle)")
    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            reply = {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32700, 'message': 'Parse error'}}
        else:
            reply = handle(msg) if isinstance(msg, dict) else {
                'jsonrpc': '2.0', 'id': None, 'error': {'code': -32600, 'message': 'Invalid Request'}}
        if reply is not None:
            sys.stdout.write(json.dumps(reply) + '\n')
            sys.stdout.flush()
    return 0


if __name__ == '__main__':
    sys.exit(main())
