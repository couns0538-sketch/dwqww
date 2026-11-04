#!/usr/bin/env python3
"""test_forge_o30_mcp.py - self-test of forge_o30_mcp.py over the real stdio transport (own code).
Checks: initialize, tools/list (5 tools), net_info on the committed random test net (OK, 4 king buckets, mirrored),
net_score of the lock net written as v2 on the S31 subset (= 0.014310027 / 0.004572428, delta 0), runs_table returns a
table, spsa_status on a missing dir is an error result, an unknown tool is an error, a bad JSON line is a parse error.
Exit 0 = PASS."""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRV = os.path.join(HERE, 'forge_o30_mcp.py')
NET = os.path.normpath(os.path.join(HERE, '..', 'a', 'testnets', 'rand_kbrank4m_ob8_s2.nnue2'))
LOCKV2 = r'D:\o30\nets\lockv2\lock_kbone_ob1.nnue2'


def main():
    p = subprocess.Popen([sys.executable, '-I', '-B', SRV], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    n = [0]

    def call(method, params=None, raw=None):
        n[0] += 1
        p.stdin.write((raw if raw is not None else json.dumps({'jsonrpc': '2.0', 'id': n[0], 'method': method,
                                                                 'params': params or {}})) + '\n')
        p.stdin.flush()
        return json.loads(p.stdout.readline())

    fails = []

    def check(ok, what):
        print(('ok   ' if ok else 'FAIL ') + what)
        if not ok:
            fails.append(what)

    r = call('initialize', {'protocolVersion': '2025-06-18'})
    check(r['result']['serverInfo']['name'] == 'forge-o30', 'initialize')
    r = call('tools/list')
    names = sorted(t['name'] for t in r['result']['tools'])
    check(names == ['net_info', 'net_score', 'runs_table', 'spsa_status', 'v2_bench'], f'tools/list {names}')
    r = call('tools/call', {'name': 'net_info', 'arguments': {'net': NET}})
    out = r['result']['structuredContent']['output']
    check(r['result']['structuredContent']['ok'] and 'king buckets 4' in out and 'mirrored' in out, 'net_info test net')
    r = call('tools/call', {'name': 'net_score', 'arguments': {'net': LOCKV2, 'set': 's16'}})
    s = r['result']['structuredContent']['s16']
    check(abs(s['mse_b0.6'] - 0.014310027) < 1e-9 and abs(s['mse_b1.0'] - 0.004572428) < 1e-9, f'net_score lock as v2 {s["mse_b0.6"]}')
    r = call('tools/call', {'name': 'runs_table', 'arguments': {}})
    check(r['result']['structuredContent']['table'].startswith('| run |'), 'runs_table')
    r = call('tools/call', {'name': 'spsa_status', 'arguments': {'run_dir': r'D:\o30\spsa\no_such_run'}})
    check(r['result']['isError'], 'spsa_status missing dir is an error')
    r = call('tools/call', {'name': 'no_such_tool', 'arguments': {}})
    check(r['result']['isError'], 'unknown tool is an error')
    r = call(None, raw='{not json')
    check(r.get('error', {}).get('code') == -32700, 'parse error')
    p.stdin.close()
    p.wait(timeout=60)
    print('SELFTEST ' + ('PASS' if not fails else f'FAIL ({len(fails)})'))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
