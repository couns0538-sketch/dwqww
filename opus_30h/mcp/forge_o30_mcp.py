#!/usr/bin/env python3
"""forge_o30_mcp.py - Opus 30-h job: a small MCP server (stdio, JSON-RPC 2.0, standard library only) for the v2-net and
SPSA work. Same protocol handling as the R15 forge-uci server (own code).

Tools:
  net_info      header / size / checksum of a FORGENN2 v2 net file (o30_v2net.py info)
  net_score     holdout losses of a v2 net (o30_score_v2.exe): the crew's S31 subset of 013/014 and / or the jobA val
                holdout (20k-node labels), with the lock net's numbers for comparison
  runs_table    the table of every CPU fine-tune run under D:\\o30\\runs (o30_runs.py)
  spsa_status   pairs, W/L/D and current values of an SPSA run (tune_spsa.py status) + its last history row
  v2_bench      `bench <depth>` of a Forge exe with EvalFileV2 = a net (empty = off); node count and nps
Everything it starts runs at Idle on CPUs 0-1 (the server lowers itself first; children inherit). Read-only except the
scorer / engines' own stdout.
Run: C:\\Users\\Administrator\\grok-pc\\nnue\\.venv\\Scripts\\python.exe -I -B forge_o30_mcp.py
Register: bash setup_o30_mcp.sh    Self-test: python -I -B test_forge_o30_mcp.py
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.normpath(os.path.join(HERE, '..', 'a'))
B = os.path.normpath(os.path.join(HERE, '..', 'b'))
SERVER = {'name': 'forge-o30', 'version': '1.0.0'}
VERSIONS = ['2025-06-18', '2025-03-26', '2024-11-05']
PY = sys.executable
SCORER = r'D:\o30\tools_bin\o30_score_v2.exe'
SETS = {'s16': (r'F:\opus_scratch\sol_S31\inputs\prod\holdout_013_014_s16.pos', r'F:\opus_scratch\sol_S31\inputs\prod\holdout_013_014_s16.hce'),
        'jobA': (r'D:\o30\data\jobA_val.pos', r'D:\o30\data\jobA_val.hce')}
LOCK = {'s16': {'mse_b0.6': 0.014310027, 'mse_b1.0': 0.004572428}, 'jobA': {'mse_b0.6': 0.013272058}}


def log(msg):
    print(f'forge-o30: {msg}', file=sys.stderr, flush=True)


def lower_self():
    if os.name != 'nt':
        return
    import ctypes
    k32 = ctypes.windll.kernel32
    k32.GetCurrentProcess.restype = ctypes.c_void_p
    h = ctypes.c_void_p(k32.GetCurrentProcess())
    if not k32.SetPriorityClass(h, 0x40) or not k32.SetProcessAffinityMask(h, ctypes.c_size_t(0x3)):
        log('cannot set Idle / CPU mask - exiting')
        sys.exit(3)


def need_file(args, key):
    p = args.get(key)
    if not p or not os.path.isfile(p):
        raise ValueError(f'{key}: file not found: {p}')
    return p


def t_net_info(args):
    p = subprocess.run([PY, '-I', '-B', os.path.join(A, 'o30_v2net.py'), 'info', need_file(args, 'net')],
                       capture_output=True, text=True, timeout=120)
    return {'ok': p.returncode == 0, 'output': (p.stdout + p.stderr).strip()}


def t_net_score(args):
    net = need_file(args, 'net')
    which = args.get('set', 'both')
    names = ['s16', 'jobA'] if which == 'both' else [which]
    out = {}
    for n in names:
        if n not in SETS:
            raise ValueError(f'set must be s16, jobA or both, not {which}')
        pos, hce = SETS[n]
        p = subprocess.run([SCORER, '--net', net, '--pos', pos, '--hce', hce], capture_output=True, text=True, timeout=900)
        if p.returncode != 0:
            raise ValueError(f'scorer failed: {p.stderr.strip()}')
        r = json.loads(p.stdout.strip().splitlines()[-1])
        out[n] = {k: r[k] for k in r if k.startswith('mse') or k in ('rows', 'used', 'residual')}
        out[n]['lock_net'] = LOCK[n]
        out[n]['delta_b0.6'] = r['mse_b0.6'] - LOCK[n]['mse_b0.6']
    return out


def t_runs_table(args):
    p = subprocess.run([PY, '-I', '-B', os.path.join(A, 'o30_runs.py')] + (['--all'] if args.get('all') else []),
                       capture_output=True, text=True, timeout=120)
    return {'table': p.stdout.strip(), 'stderr': p.stderr.strip()}


def t_spsa_status(args):
    run = args.get('run_dir', '')
    if not os.path.isdir(run):
        raise ValueError(f'run_dir not found: {run}')
    p = subprocess.run([PY, '-I', '-B', os.path.join(B, 'tune_spsa.py'), 'status', run], capture_output=True, text=True, timeout=120)
    last = ''
    hist = os.path.join(run, 'history.csv')
    if os.path.isfile(hist):
        with open(hist, encoding='ascii') as f:
            lines = f.read().strip().splitlines()
        last = lines[0] + '\n' + lines[-1] if len(lines) > 1 else ''
    return {'status': p.stdout.strip(), 'history_last': last}


def t_v2_bench(args):
    exe = need_file(args, 'exe')
    depth = int(args.get('depth', 13))
    if not 1 <= depth <= 22:
        raise ValueError('depth must be 1..22')
    net = args.get('net', '')
    cmds = 'uci\n' + (f'setoption name EvalFileV2 value {net}\n' if net else '') + f'isready\nbench {depth}\n'
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    out, _ = p.communicate(cmds + 'quit\n', timeout=1800)
    m = re.search(r'info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)', out)
    loaded = re.search(r'info string (EvalFileV2 loaded .*|ERROR EvalFileV2 .*)', out)
    if not m:
        raise ValueError('no bench line: ' + out[-500:])
    return {'depth': int(m.group(1)), 'nodes': int(m.group(2)), 'ms': int(m.group(3)), 'nps': int(m.group(4)),
            'net_line': loaded.group(1) if loaded else ('(no net requested)' if not net else 'NO LOAD LINE')}


def schema(props, required=()):
    return {'type': 'object', 'properties': props, 'required': list(required), 'additionalProperties': False}


TOOLSPEC = {
    'net_info': (t_net_info, 'Header, size and FNV-1a checksum check of a FORGENN2 v2 net file.',
                 schema({'net': {'type': 'string', 'description': 'path of a .nnue2 file'}}, ['net'])),
    'net_score': (t_net_score, "Holdout MSE (b1.0 / b0.6 / b0.8) of a v2 net on the crew's S31 subset of 013/014 and / or "
                  'the jobA val holdout (20k-node labels), with the lock net numbers and the b0.6 difference.',
                  schema({'net': {'type': 'string'}, 'set': {'type': 'string', 'enum': ['s16', 'jobA', 'both']}}, ['net'])),
    'runs_table': (t_runs_table, 'Markdown table of every CPU fine-tune run (config, last / best holdout losses vs the '
                   'lock net, positions, training rate).', schema({'all': {'type': 'boolean'}})),
    'spsa_status': (t_spsa_status, 'Status of an SPSA run (pairs, W/L/D, start -> current value per parameter) and the '
                    'last history.csv row.', schema({'run_dir': {'type': 'string'}}, ['run_dir'])),
    'v2_bench': (t_v2_bench, "Run 'bench <depth>' on a Forge exe, optionally with EvalFileV2 = a net; returns nodes, "
                 'ms, nps and the engine load line.', schema({'exe': {'type': 'string'}, 'net': {'type': 'string'},
                                                               'depth': {'type': 'integer', 'minimum': 1, 'maximum': 22}}, ['exe'])),
}


def handle(msg):
    mid = msg.get('id')
    method = msg.get('method')
    if method == 'initialize':
        want = (msg.get('params') or {}).get('protocolVersion')
        return {'jsonrpc': '2.0', 'id': mid, 'result': {
            'protocolVersion': want if want in VERSIONS else VERSIONS[0],
            'capabilities': {'tools': {'listChanged': False}}, 'serverInfo': SERVER,
            'instructions': 'Forge v2 nets and SPSA (Opus 30-h job): Idle on CPUs 0-1; read-only on data and runs.'}}
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
    log(f'ready ({len(TOOLSPEC)} tools, Idle, CPUs 0-1)')
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
