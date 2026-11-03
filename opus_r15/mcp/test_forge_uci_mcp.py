#!/usr/bin/env python3
"""test_forge_uci_mcp.py - self-test of forge_uci_mcp.py over its real stdio transport (newline-delimited JSON-RPC).

Starts the server, then: initialize (+ initialized notification), tools/list (7 tools), uci_options / perft / bench /
pin_check on the lock copy D:\\o15\\base\\lock_copy.exe (sha256 fd3a5190...), gate_summary on a finished crew gate,
index_check, pc_status, plus error paths (unknown tool, missing exe, bad depth, unknown method, a line that is not
JSON). Exit 0 = every case as expected.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOCK = r'D:\o15\base\lock_copy.exe'
GATE = r'F:\forge_push\gate_stB_lmrttcapall1_vs_AL1'
p = subprocess.Popen([sys.executable, '-I', '-B', os.path.join(HERE, 'forge_uci_mcp.py')], stdin=subprocess.PIPE,
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
nid = 0


def rpc(method, params=None, raw=None):
    global nid
    if raw is not None:
        p.stdin.write(raw + '\n')
    else:
        nid += 1
        msg = {'jsonrpc': '2.0', 'id': nid, 'method': method}
        if params is not None:
            msg['params'] = params
        p.stdin.write(json.dumps(msg) + '\n')
    p.stdin.flush()
    return json.loads(p.stdout.readline())


def call(name, args):
    r = rpc('tools/call', {'name': name, 'arguments': args})
    res = r['result']
    return res.get('isError'), res.get('structuredContent'), res['content'][0]['text']


fails = 0


def check(name, ok, detail=''):
    global fails
    print(('PASS ' if ok else 'FAIL ') + name + (f': {detail}' if detail else ''))
    if not ok:
        fails += 1


init = rpc('initialize', {'protocolVersion': '2025-06-18', 'capabilities': {}, 'clientInfo': {'name': 'r15-test', 'version': '1'}})
check('initialize', init['result']['serverInfo']['name'] == 'forge-uci' and init['result']['protocolVersion'] == '2025-06-18',
      json.dumps(init['result']['serverInfo']))
p.stdin.write(json.dumps({'jsonrpc': '2.0', 'method': 'notifications/initialized'}) + '\n')
p.stdin.flush()
check('ping', rpc('ping')['result'] == {})
tools = rpc('tools/list')['result']['tools']
check('tools_list', sorted(t['name'] for t in tools) == sorted(
    ['pin_check', 'uci_options', 'bench', 'perft', 'gate_summary', 'index_check', 'pc_status']), str(len(tools)))
err, sc, _ = call('uci_options', {'exe': LOCK})
names = [o['name'] for o in sc['options']] if sc else []
check('uci_options', not err and 'LmrQuietBase' in names and 'Hash' in names, f"{sc['count'] if sc else '?'} options")
err, sc, _ = call('perft', {'exe': LOCK, 'depth': 3})
check('perft_startpos_d3', not err and sc['nodes'] == 8902, str(sc))
err, sc, _ = call('perft', {'exe': LOCK, 'depth': 4, 'fen': 'kiwipete'})
check('perft_kiwipete_d4', not err and sc['nodes'] == 4085603, str(sc))
err, sc, _ = call('bench', {'exe': LOCK, 'depth': 11})
check('bench_d11_lock_pin', not err and sc['nodes'] == 312866, str(sc))
err, sc, _ = call('bench', {'exe': LOCK, 'depth': 11, 'options': 'LmrQuietBase=86'})
check('bench_d11_live_option', not err and sc['nodes'] != 312866, str(sc))
err, sc, _ = call('pin_check', {'exe': LOCK})
check('pin_check_lock', not err and sc['exit_code'] == 0 and sc['record']['verdict'] == 'PASS', sc['output'].splitlines()[0] if sc else '')
err, sc, _ = call('gate_summary', {'gate_dir': GATE})
s = sc['summary'] if sc else {}
check('gate_summary', not err and s.get('w') == 326 and s.get('l') == 352 and abs(s.get('llr', 0) + 2.88) < 0.01 and not s.get('problems'),
      f"W {s.get('w')} L {s.get('l')} LLR {s.get('llr')}")
err, sc, _ = call('index_check', {'no_engine': True})
check('index_check', not err and sc['exit_code'] == 0, sc['output'].splitlines()[-1] if sc else '')
err, sc, _ = call('pc_status', {})
check('pc_status', not err and 'free C:' in sc['output'], sc['output'].splitlines()[0][:100] if sc else '')
err, _, text = call('no_such_tool', {})
check('unknown_tool_is_error', err is True, text)
err, _, text = call('bench', {'exe': r'D:\o15\base\no_such.exe'})
check('missing_exe_is_error', err is True, text)
err, _, text = call('perft', {'exe': LOCK, 'depth': 9})
check('bad_depth_is_error', err is True, text)
r = rpc('no/such/method')
check('unknown_method', r.get('error', {}).get('code') == -32601)
r = rpc(None, raw='this is not json')
check('parse_error', r.get('error', {}).get('code') == -32700)
p.stdin.close()
p.wait(timeout=30)
check('clean_exit', p.returncode == 0, f'exit {p.returncode}; stderr: {p.stderr.read().strip()[:120]}')
total = 18
print(f'{total - fails} / {total} checks as expected')
print('ALL PASS' if fails == 0 else f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
