#!/usr/bin/env python3
"""forge_sol_S46_promote_sim_20261027.py: auto-promote rule replay simulator (S46, opus 2026-10-27).

Replays a timeline of gate / confirm / file events against the AUTO-LOCK promotion rules and writes a deterministic
decision log (PROMOTE, HOLD, PENDING, REGATE, COMBINE_LIST, ROLLBACK, BLOCKED, WAIT, INELIGIBLE, REWORK, REBUILD,
LABEL, SKIP, VOID_RERUN, Z2_RELEASE, Z2_DROP, RECONCILE, ALERT, NOTE) with the reason for each line.
The rules come from a JSON config (config/rules_*.json), so a crew vote changes config, not code. The order of one
`tick` mirrors autopromote.ps1 896663b0 (live on the PC): in-flight reconcile -> rollback scan -> chain scan ->
race-hold / pick -> 24 h / chained-CR holds -> promote -> race-loser re-gates (CAP-LATE Z) -> Z-2 -> step-5 rebuild.
Pure stdlib, no I/O besides reading the config + fixture and writing --out. Same input -> byte-identical output.
It never reads or runs anything on the PC; the PC script itself was only read (see README for disagreements).
"""
import argparse
import copy
import datetime as dt
import json
import re
import sys

VERSION = 'S46 promote_sim 2026-10-27 v1'


def T(s):
    return dt.datetime.fromisoformat(s)


def S(t):
    return t.strftime('%Y-%m-%dT%H:%M')


class Sim:
    def __init__(self, rules, fx):
        self.R, self.fx = rules, fx
        ini = fx['init']
        self.now = T(ini['t'])
        self.lock = copy.deepcopy(ini['lock'])
        self.gates = [self._norm(g) for g in ini['gates']]
        self.res, self.ran_base = {}, {}
        self.started = set(ini.get('started', []))
        self.running = ini.get('running')
        self.files = set(ini.get('files', []))
        self.pause_until = dict(ini.get('pause_until', {}))
        self.src_dirs = set(ini.get('src_dirs', []))
        st0 = ini.get('state', {})
        self.st = {'seen': dict(st0.get('seen', {})), 'promotes': list(st0.get('promotes', [])), 'race': {}, 'rebase_todo': [],
                   'inflight': None, 'alerts': set(), 'rollbacks': []}
        self.crash_next, self.crashed, self.exe_fail, self.srand_k = False, False, {}, 0
        self.q1 = True
        self.out = []
        for g in self.gates:
            if g['tag'] in self.started or g['tag'] == self.running:
                self.started.add(g['tag'])
                self.ran_base[g['tag']] = g['base']
        for r in ini.get('results', []):
            self._result(r)

    # ------------------------------------------------------------------ helpers
    def _norm(self, g):
        d = {'status': None, 'confirm_of': None, 'options': [], 'sprt': [0, 10], 'nonreg': False, 'conc': 5, 'kind': 'net',
             'pooled': False, 'notes': '', 'srand': 0, 'openings_start': 0}
        d.update(copy.deepcopy(g))
        return d

    def L(self, action, subject, reason):
        self.out.append(f'{S(self.now)} | {action} | {subject} | {reason}')

    def alert(self, key, msg):
        if key in self.st['alerts']:
            return
        self.st['alerts'].add(key)
        self.L('ALERT', key, msg)

    def g(self, tag):
        hit = [x for x in self.gates if x['tag'] == tag]
        return hit[0] if hit else None

    def is_started(self, tag):
        return tag == self.running or tag in self.started

    def is_strength(self, g):
        return g['sprt'][0] == 0 and g['sprt'][1] > 0 and not g['nonreg']

    def ranb(self, g):
        return self.ran_base.get(g['tag'], g['base'])

    def verdict(self, tag):
        r = self.res.get(tag)
        if not r:
            return None
        if r.get('void'):   # driver r7 writes '# tag RESULT: **VOID**' and keeps the normal body, Verdict line included (CR HIGH-1)
            return 'VOID' if self.R['void_never_h1'] else r.get('verdict')
        return r.get('verdict')

    def chain(self):
        out, lk = [], self.lock
        while lk:
            out.append(lk)
            lk = lk.get('parent')
        return out

    def q1on(self):   # $Q1ON: set once per tick after the rollback scan, NOT recomputed after a promote (CR re-review MED-3 note)
        return self.q1

    def is_e32(self, tag):
        return self.R['rhq1']['enabled'] and self.q1on() and self.R['rhq1']['e32_pattern'] in tag

    def confirms_of(self, ptag):
        return [x for x in self.gates if x['confirm_of'] == ptag]

    def rerun_counts(self, c):
        if not c.get('ag_void_rerun_of'):
            return True
        sib = [x for x in self.gates if x.get('ag_void_rerun_of') and x['confirm_of'] == c['confirm_of']]
        return bool(sib) and sib[0]['tag'] == c['tag']

    def rival_off(self, tag):
        off = self.R['race_hold']['rival_off']
        if 'STOP' in off and f'STOP_{tag}' in self.files:
            return f'STOP_{tag} present'
        if 'PAUSE' in off and tag in self.pause_until and self.now < T(self.pause_until[tag]):
            return f'PAUSE_{tag}.txt until {self.pause_until[tag]}'
        if 'ABORTED' in off and f'ABORTED_{tag}' in self.files:
            return 'ABORTED.txt present'
        if 'VOID' in off and (self.res.get(tag) or {}).get('void'):
            return 'VOID.txt present'
        if 'STALLED' in off and tag in self.started and self.running and self.running != tag and not self.verdict(tag):
            return 'STALLED/PARTIAL: started, not running, no verdict'
        return ''

    def status_off(self, g):
        st = g['status'] or ''
        rx = self.R['race_hold']['rival_off_status_regex']
        return bool(rx) and re.search(rx, st) is not None

    def e48_state(self):
        e48 = self.R['rhq1']['e48_gate']
        cs = [c for c in self.confirms_of(e48) if self.rerun_counts(c)]
        h1 = [c for c in cs if (self.verdict(c['tag']) or '').startswith('H1 accepted')]
        if h1:
            return f'H1 {h1[0]["tag"]}'
        pend = [c for c in cs if not self.verdict(c['tag']) and not self.rival_off(c['tag']) and not self.status_off(c)]
        if pend:
            return 'PENDING ' + ','.join(c['tag'] for c in pend)
        return 'NONH1 ' + '; '.join(f"{c['tag']}='{self.verdict(c['tag'])}'" for c in cs)

    def e32_retired(self):
        if not self.R['rhq1']['enabled'] or not self.q1on():
            return False
        return self.e48_state().startswith('H1 ') or any((x['status'] or '').startswith('RETIRED_e32lane') for x in self.gates)

    def fresh_srand(self):
        used = {x['srand'] for x in self.gates} | {(r.get('run_info') or {}).get('srand') for r in self.res.values()}
        while True:
            self.srand_k += 1
            s = 700000000 + self.srand_k
            if s not in used:
                return s

    def max_start(self):
        return max([x['openings_start'] for x in self.gates] + [0])

    def manifest_ok(self, why):
        if self.R['edits_need_running_gate'] and not self.running:
            self.L('NOTE', why, 'manifest edit due but no gate is running (boundary edits only while a gate runs); next tick')
            return False
        return True

    def insert_after_running(self, newg):
        tags = [x['tag'] for x in self.gates]
        pos = tags.index(self.running) + 1 if self.running in tags else len(self.gates)
        self.gates.insert(pos, self._norm(newg))

    def _result(self, ev):
        r = self.res.setdefault(ev['tag'], {})
        for k in ('verdict', 'elo', 'err', 'games', 'csv', 'run_info'):
            if k in ev:
                r[k] = copy.deepcopy(ev[k])
        r['t'] = ev.get('t_result', ev.get('t', S(self.now)))
        r.setdefault('run_info', {'attempt': 1, 'fresh_srand': False}) if 'run_info' not in ev else None
        r.setdefault('csv', {'tl': 0, 'crash': 0, 'clean': 'CLEAN'}) if 'csv' not in ev else None
        self.started.add(ev['tag'])
        g = self.g(ev['tag'])
        if g is not None:
            self.ran_base.setdefault(ev['tag'], g['base'])

    # ------------------------------------------------------------------ events
    def run(self):
        for ev in self.fx['events']:
            self.now = T(ev['t'])
            k = ev['ev']
            if k in ('start', 'result', 'void', 'csv', 'run_info', 'tl') and self.g(ev['tag']) is None:
                self.L('NOTE', ev['tag'], f"event '{k}' ignored: this gate does not exist under these rules")
                continue
            if k in ('csv', 'run_info') and ev['tag'] not in self.res:
                self.L('NOTE', ev['tag'], f"event '{k}' ignored: no result yet")
                continue
            if k == 'tick':
                self.tick()
            elif k == 'start':
                self.running = ev['tag']
                self.started.add(ev['tag'])
                self.ran_base[ev['tag']] = self.g(ev['tag'])['base']
            elif k == 'idle':
                self.running = None
            elif k == 'result':
                self._result(ev)
                if self.running == ev['tag']:
                    self.running = ev.get('next')
                    if self.running:
                        self.started.add(self.running)
                        self.ran_base[self.running] = self.g(self.running)['base']
            elif k == 'csv':
                self.res[ev['tag']]['csv'] = ev['csv']
            elif k == 'run_info':
                self.res[ev['tag']]['run_info'] = ev['run_info']
            elif k == 'void':
                r = self.res.setdefault(ev['tag'], {'t': ev['t']})
                r.update({'void': True, 'cause': ev.get('cause', 'VOID.txt'), 'verdict': ev.get('verdict')})
                r.setdefault('csv', ev.get('csv', {'tl': 0, 'crash': 0, 'clean': 'CLEAN'}))   # Ledger-Sync also writes a row for a VOID gate (CR HIGH-1)
                r.setdefault('run_info', {'attempt': 1, 'fresh_srand': False})
                self.started.add(ev['tag'])
                if self.running == ev['tag']:
                    self.running = ev.get('next')
            elif k == 'file':
                self.files.add(ev['name'])
            elif k == 'pause':
                self.pause_until[ev['tag']] = ev['until']
            elif k == 'tl':
                r = self.res.setdefault(ev['tag'], {})
                r['log_tl'] = r.get('log_tl', 0) + ev.get('tl', 0)
                r['log_crash'] = r.get('log_crash', 0) + ev.get('crash', 0)
                r['event_game'] = ev.get('game')
            elif k == 'crash_next_promote':
                self.crash_next = True
            elif k == 'add_gate':
                if ev.get('after_running'):
                    self.insert_after_running(ev['gate'])
                else:
                    self.gates.append(self._norm(ev['gate']))
            elif k == 'exe_check_fail':
                self.exe_fail[ev['tag']] = ev['why']
            elif k == 'src_dir':
                self.src_dirs.add(ev['name'])
            else:
                raise ValueError(f'unknown event {k}')
        self.summary()
        return self.out

    # ------------------------------------------------------------------ one autopromote tick
    def tick(self):
        R = self.R
        self.L('TICK', self.lock['tag'], f"running '{self.running or ''}'")
        infblock = False
        inf = self.st['inflight']
        if inf:
            if self.lock['tag'] == inf['ltag']:
                if not any(p['tag'] == inf['ltag'] for p in self.st['promotes']):
                    self.st['promotes'].append({'n': inf['n'], 'tag': inf['ltag'], 'parent': inf['parent'], 'parent_sha': inf['parent_sha'], 'gate': inf['gate'],
                                                'confirm': inf['confirm'], 'sha': inf['sha'], 'kind': self.lock['kind'], 't': inf['t']})
                self.st['seen'][inf['gate']] = f"PROMOTED {inf['ltag']} (reconciled)"
                self.st['inflight'] = None
                self.L('RECONCILE', inf['ltag'], f"pointer already moved by the crashed tick; promote bookkeeping finished for {inf['gate']}")
                self.alert(f"inflight_ok_{inf['ltag']}", f"in-flight promote {inf['ltag']} reconciled; race losers {inf['race_losers']} need a manual check")
            else:
                self.L('BLOCKED', inf['ltag'], f"in-flight promote found but the pointer is {self.lock['tag']}: crash before the pointer write; nothing promoted until QA clears it")
                infblock = True
        self.rollback_scan()
        if infblock:
            return
        self.q1 = (self.lock['tag'] == 'h256_e12') if R['rhq1']['e32_scope_base_lock_only'] else True
        prom, wait_tags = self.chain_scan()
        prom, race_losers, race_win, race, rivals = self.race_hold(prom, wait_tags)
        chosen = self.spacing_holds(prom, race_losers, race_win)
        promoted = self.promote(chosen, race)
        if self.crashed:   # the simulated crash ends this tick (the process died after the pointer write)
            self.crashed = False
            return
        self.regate_losers(promoted, race_losers, race_win)
        self.z2()
        if promoted and race:
            for fr in race.get('finished_rivals', []):
                if not (self.verdict(fr['confirm']) or '').startswith('H1 accepted'):
                    self.L('REWORK', fr['gate'], f"RH-Q2: rival confirm {fr['confirm']} ended '{self.verdict(fr['confirm'])}'; not re-gated as a rival")
            self.st['race'] = {}
        self.step5(promoted)

    def rollback_scan(self):
        R, lk = self.R, self.lock
        if int(lk['n']) <= 0:
            return
        hits = []
        win = R['rollback']['window_games']
        for g in self.gates:
            if not self.is_started(g['tag']) or self.ranb(g) != lk['sha']:
                continue
            r = self.res.get(g['tag'], {})
            if win is not None and r.get('event_game') is not None and r['event_game'] > win:
                continue
            csv = r.get('csv') or {}
            if (R['rollback']['on_tl'] and (csv.get('tl', 0) > 0 or r.get('log_tl', 0) > 0)) or \
               (R['rollback']['on_crash'] and (csv.get('crash', 0) > 0 or r.get('log_crash', 0) > 0)):
                hits.append(f"{g['tag']} TL {max(csv.get('tl', 0), r.get('log_tl', 0))} crash {max(csv.get('crash', 0), r.get('log_crash', 0))}"
                            + (f" at game {r['event_game']}" if r.get('event_game') else ''))
        if not hits:
            return
        if not self.manifest_ok(f"rollback_{lk['n']}"):
            self.L('NOTE', lk['tag'], 'ROLLBACK due but deferred (no running gate): ' + '; '.join(hits))
            return
        pl = lk['parent']
        for g in self.gates:
            if self.is_started(g['tag']):
                continue
            if g.get('ag_rebuilt_on') == lk['tag'] and g.get('ag_prev'):
                pv = g['ag_prev']
                g.update({'exe': pv['exe'], 'sha': pv['sha'], 'base': pv['base'], 'srand': self.fresh_srand(), 'ag_rebuilt_on': f"ROLLED_BACK from {lk['tag']}"})
                self.L('RESTORE', g['tag'], f"rebuilt on {lk['tag']}: back to {pv['exe']} vs {pl['tag']}, fresh srand {g['srand']}")
            elif g['base'] == lk['sha']:
                g.update({'base': pl['sha'], 'srand': self.fresh_srand()})
                self.L('RESTORE', g['tag'], f"opponent {lk['tag']} withdrawn -> {pl['tag']}, fresh srand {g['srand']}")
        adds = []
        for g in list(self.gates):
            if not self.is_started(g['tag']) or g['tag'] == self.running or self.ranb(g) != lk['sha']:
                continue
            nt = f"{g['tag']}_rb{lk['n']}"
            if self.g(nt):
                continue
            ng = copy.deepcopy(g)
            ng.update({'tag': nt, 'srand': self.fresh_srand(), 'openings_start': self.max_start() + 3000, 'status': None, 'base': pl['sha']})
            if g.get('ag_prev'):
                ng.update({'exe': g['ag_prev']['exe'], 'sha': g['ag_prev']['sha']})
            adds.append(ng)
        for ng in adds:
            self.insert_after_running(ng)
            self.L('REGATE', ng['tag'], f"re-queued by rollback: played withdrawn {lk['tag']}; now vs {pl['tag']}, fresh srand {ng['srand']}")
        self.L('ROLLBACK', lk['tag'], f"pointer {lk['tag']} -> {pl['tag']}: " + '; '.join(hits))
        self.st['rollbacks'].append(lk['tag'])
        self.lock = pl

    def chain_scan(self):
        R, prom, wait_tags = self.R, [], []
        for c in [x for x in self.gates if x['confirm_of']]:
            p = self.g(c['confirm_of'])
            if not p:
                continue
            key = p['tag']
            if key in self.st['seen'] and not self.st['seen'][key].startswith('PENDING'):
                continue
            vp, vc = self.verdict(p['tag']), self.verdict(c['tag'])
            if 'VOID' in (vp, vc) and R['void_chain_not_marked']:
                self.L('NOTE', f"{p['tag']}+{c['tag']}", f"VOID ({p['tag'] if vp == 'VOID' else c['tag']}); not marked (a re-run may follow)")
                continue
            if not vp or not vc:
                continue
            why, wait = [], []
            for gx, v in ((p, vp), (c, vc)):
                if not v.startswith('H1 accepted'):
                    why.append(f"{gx['tag']} verdict '{v}'")
                if not self.is_strength(gx):
                    why.append(f"{gx['tag']} is not a strength-bounds [0,x] gate")
                r = self.res.get(gx['tag'], {})
                csv, ri = r.get('csv'), r.get('run_info')
                if csv is None:
                    (wait if R['wait_on_missing_data'] else why).append(f"{gx['tag']} has no FORGE_RESULTS.csv row yet")
                elif csv.get('tl') or csv.get('crash') or csv.get('clean') != 'CLEAN':
                    why.append(f"{gx['tag']} CSV TL {csv.get('tl')} crash {csv.get('crash')} clean '{csv.get('clean')}'")
                if ri is None:
                    (wait if R['wait_on_missing_data'] else why).append(f"{gx['tag']} RUN_INFO.json missing")
                elif ri.get('attempt', 1) != 1 or ri.get('fresh_srand'):
                    why.append(f"{gx['tag']} rerolled (attempt {ri.get('attempt')} fresh_srand {ri.get('fresh_srand')})")
                if gx['pooled']:
                    why.append(f"{gx['tag']} is pooled")
            lasting = [w for w in why if " verdict '" in w or 'not a strength' in w or 'is pooled' in w]
            if wait and not lasting:
                wait_tags.append(p['tag'])
                self.L('WAIT', f"{p['tag']}+{c['tag']}", 'WAIT_DATA: ' + '; '.join(wait) + '; not marked, retried next tick')
                if (self.now - T(self.res[c['tag']]['t'])).total_seconds() >= R['wait_data_alert_hours'] * 3600:
                    self.alert(f'waitdata_{key}', f"chain {p['tag']}+{c['tag']} has waited {R['wait_data_alert_hours']} h+ for data")
                continue
            why += wait
            sp = (self.res[p['tag']].get('run_info') or {}).get('srand', p['srand'])
            sc = (self.res[c['tag']].get('run_info') or {}).get('srand', c['srand'])
            if sp == sc:
                why.append(f'confirm srand {sc} = parent srand')
            if p['conc'] != c['conc']:
                why.append(f"confirm concurrency {c['conc']} != parent {p['conc']}")
            if self.ranb(p) != self.ranb(c):
                why.append(f'confirm opponent {self.ranb(c)} != parent opponent {self.ranb(p)}')
            if p['sha'] != c['sha']:
                why.append(f"confirm exe {c['sha']} != parent exe {p['sha']}")
            if why:
                self.st['seen'][key] = 'INELIGIBLE'
                self.L('INELIGIBLE', f"{p['tag']}+{c['tag']}", '; '.join(why))
                if vp.startswith('H1 accepted') and vc.startswith('H1 accepted'):
                    self.alert(f'inelig_{key}', f"H1+H1 chain {key} marked INELIGIBLE: {'; '.join(why)}")
                continue
            if self.ranb(p) != self.lock['sha'] and R['combine_list_on_stale_lock']:
                old = next((lk['tag'] for lk in self.chain() if lk['sha'] == self.ranb(p)), None) or \
                    next((pr['parent'] for pr in self.st['promotes'] if pr.get('parent_sha') == self.ranb(p)), 'an older lock')
                self.st['seen'][key] = f'COMBINE vs {self.ranb(p)}'
                self.L('COMBINE_LIST', f"{p['tag']}+{c['tag']}", f"H1+H1 but vs {old} ({self.ranb(p)}); current lock is {self.lock['tag']}; never auto-promoted")
                continue
            prom.append({'p': p, 'c': c, 't': T(self.res[c['tag']]['t'])})
        prom.sort(key=lambda e: e['t'])
        if not prom:
            self.L('NOTE', self.lock['tag'], 'no eligible H1+H1 chain vs the current lock')
        return prom, wait_tags

    def rec(self, p, c, role):
        rp, rc = self.res.get(p['tag'], {}), self.res.get(c['tag'], {})
        pool = None
        if rp.get('games') and rc.get('games') and rp.get('elo') is not None and rc.get('elo') is not None:
            pool = round((rp['elo'] * rp['games'] + rc['elo'] * rc['games']) / (rp['games'] + rc['games']), 2)
        return {'role': role, 'gate': p['tag'], 'confirm': c['tag'], 'celo': rc.get('elo') or 0.0, 'cerr': rc.get('err') or 0.0, 'pooled': pool}

    def race_hold(self, prom, wait_tags):
        R, race_losers, race_win, race, rivals = self.R, [], None, None, []
        if not prom or not R['race_hold']['enabled']:
            return prom, race_losers, race_win, race, rivals
        lock_sha, prom_tags = self.lock['sha'], [e['p']['tag'] for e in prom]
        parked = []
        for rc in [x for x in self.gates if x['confirm_of']]:
            rp = self.g(rc['confirm_of'])
            if not rp or rp['tag'] in prom_tags or not self.is_strength(rp):
                continue
            if not (self.verdict(rp['tag']) or '').startswith('H1 accepted') or self.ranb(rp) != lock_sha:
                continue
            if self.verdict(rc['tag']):
                continue
            if not self.rerun_counts(rc):
                parked.append(f"{rc['tag']} is a 2nd VOID re-run (only ONE re-run counts)")
                continue
            off = self.rival_off(rc['tag'])
            if off:
                parked.append(f"{rc['tag']} {off}")
                continue
            if self.status_off(rc):
                parked.append(f"{rc['tag']} status '{rc['status']}'")
                continue
            rivals.append({'p': rp, 'c': rc, 'state': 'running' if self.running == rc['tag'] else 'queued'})
        if parked:
            self.L('NOTE', 'race-hold', 'not counted as rivals: ' + '; '.join(parked))
        first = prom[0]
        cap_h = R['race_hold']['cap_hours']
        elig_t = first['t']
        cap_t = elig_t + dt.timedelta(hours=cap_h)
        age_h = (self.now - elig_t).total_seconds() / 3600
        rk = self.lock['tag']
        vh = R['void_hold']
        if vh['enabled'] and age_h < cap_h:
            for vc0 in [x for x in self.gates if x['confirm_of'] and not x.get('ag_void_rerun_of')]:
                vp0 = self.g(vc0['confirm_of'])
                if not vp0 or vp0['tag'] in prom_tags or not self.is_strength(vp0):
                    continue
                if not (self.verdict(vp0['tag']) or '').startswith('H1 accepted') or self.ranb(vp0) != lock_sha:
                    continue
                if self.verdict(vc0['tag']) != 'VOID':
                    continue
                if [x for x in self.gates if x.get('ag_void_rerun_of') and x['confirm_of'] == vp0['tag']]:
                    continue
                cause = self.res[vc0['tag']].get('cause', 'VOID')
                if not self.manifest_ok('void_rerun'):
                    rivals.append({'p': vp0, 'c': vc0, 'state': 'VOID; re-run queue pending'})
                    continue
                ng = copy.deepcopy(vc0)
                ng.update({'tag': f"{vc0['tag']}_vr1", 'srand': self.fresh_srand(), 'openings_start': self.max_start() + 3000,
                           'conc': vp0['conc'], 'confirm_of': vp0['tag'], 'ag_void_rerun_of': vc0['tag'], 'status': None})
                self.insert_after_running(ng)
                self.L('VOID_RERUN', ng['tag'], f"ONE re-run of VOID confirm {vc0['tag']} ({cause}): fresh srand {ng['srand']}, conc {ng['conc']}, never pooled; hold kept, same cap {S(cap_t)}")
                rivals.append({'p': vp0, 'c': self.g(ng['tag']), 'state': 'queued (VOID re-run)'})
        if rivals and age_h < cap_h:
            self.st['race'][rk] = {'rivals': [r['c']['tag'] for r in rivals], 'since': S(self.now)}
            for e in prom:
                self.st['seen'][e['p']['tag']] = 'PENDING RACEHOLD'
            self.L('HOLD', ','.join(f"{e['p']['tag']}+{e['c']['tag']}" for e in prom),
                   f"PROMOTE_HOLD (race-hold): other STRENGTH H1 confirm(s) on {rk} without verdict: "
                   + ', '.join(f"{r['c']['tag']} ({r['state']})" for r in rivals) + f"; cap {S(cap_t)} ({round(cap_h - age_h, 1)} h left)")
            return [], race_losers, race_win, race, rivals
        cap_exp, why = bool(rivals), ''
        if cap_exp:
            why = f"race-hold cap expired ({cap_h} h since {first['c']['tag']} finished {S(elig_t)}); unfinished rival(s) " + \
                  ', '.join(f"{r['c']['tag']} ({r['state']})" for r in rivals) + ' get a re-gate vs the new lock'
        recs = [{'ent': e, 'rec': self.rec(e['p'], e['c'], 'eligible')} for e in prom]
        if R['rhq1']['enabled'] and R['rhq1']['hold_when_e48_not_promotable'] and self.e32_retired() and recs \
                and all(self.is_e32(r['rec']['gate']) for r in recs):
            e48 = R['rhq1']['e48_gate']
            e48why = 'e48 chain WAIT_DATA' if e48 in wait_tags else (f"e48 chain seen '{self.st['seen'][e48]}'" if e48 in self.st['seen'] else 'e48 chain not eligible this tick')
            if age_h < cap_h:
                self.L('HOLD', ','.join(r['rec']['gate'] for r in recs), f"RH-Q1 HOLD: G104c is H1 but the e48 chain is not promotable ({e48why}); e32 not promoted alone; cap {S(cap_t)}")
                if e48 not in wait_tags:   # loud, except while the e48 chain only waits for lagging data (script: quiet)
                    self.alert('q1hold_' + '+'.join(r['rec']['gate'] for r in recs), f'RH-Q1 HOLD ({e48why}); crew decides')
                for e in prom:
                    self.st['seen'][e['p']['tag']] = 'PENDING Q1HOLD'
                return [], race_losers, race_win, race, rivals
            cap_exp, why = True, f'RH-Q1 FALLBACK after the {cap_h} h cap: e48 not promotable ({e48why}); promoting the e32 chain; crew review'
            self.alert('q1fallback', why)
        if len(recs) >= 2:
            q1 = [r for r in recs if self.is_e32(r['rec']['gate'])] if (R['rhq1']['enabled'] and self.e32_retired()) else []
            if len(q1) == len(recs):
                q1 = []
            rr = [r for r in recs if r not in q1]
            if len(rr) >= 2:
                srt = sorted(rr, key=lambda r: (-r['rec']['celo'], r['ent']['t']))
                a1, b1 = srt[0]['rec'], srt[1]['rec']
                de, me = abs(a1['celo'] - b1['celo']), max(a1['cerr'], b1['cerr'])
                if de < me:
                    srt = sorted(rr, key=lambda r: (-(r['rec']['pooled'] or 0.0), r['ent']['t']))
                    why = '; '.join(x for x in (why, f"TIE on confirm Elo (|dElo| {round(de, 2)} < max confirm error {me}): picked on pooled gate+confirm Elo {srt[0]['rec']['pooled']} vs {srt[1]['rec']['pooled']}") if x)
                else:
                    why = '; '.join(x for x in (why, f"picked on CONFIRM Elo {a1['celo']} vs {b1['celo']} (|dElo| {round(de, 2)} >= max confirm error {me})") if x)
            else:
                srt = list(rr)
            if q1:
                why = '; '.join(x for x in (why, 'RH-Q1 5/8: e32 lane retired once G104c H1 (confirm Elo not comparable, conc 7 vs 5); e32 chain(s) parked: ' + ', '.join(r['rec']['gate'] for r in q1)) if x)
                srt = srt + q1
            race_win = srt[0]
            for r in srt[1:]:
                r['rec']['role'] = 'parked-e32-retired' if r in q1 else 'lost-pick'
                race_losers.append(r)
            prom = [r['ent'] for r in srt]
        elif len(recs) == 1 and (cap_exp or rk in self.st['race']):
            race_win = recs[0]
            if not cap_exp:
                why = 'race-hold released: rival(s) ' + ', '.join(f"{t2}='{self.verdict(t2)}'" + (f' {self.rival_off(t2)}' if not self.verdict(t2) else '')
                                                                  for t2 in self.st['race'][rk]['rivals']) + ' reached a verdict or are no longer live'
        if race_win:
            for r in rivals:
                race_losers.append({'ent': {'p': r['p'], 'c': r['c'], 't': self.now}, 'rec': self.rec(r['p'], r['c'], 'unfinished-at-cap')})
            done = []
            if rk in self.st['race']:
                for t2 in self.st['race'][rk]['rivals']:
                    if t2 not in [r['c']['tag'] for r in rivals]:
                        c2 = self.g(t2)
                        if c2 and c2['confirm_of'] not in prom_tags:
                            done.append({'gate': c2['confirm_of'], 'confirm': t2})
            race = {'decision': why, 'finished_rivals': done}
            self.L('PICK', race_win['rec']['gate'], why or 'single eligible chain')
        return prom, race_losers, race_win, race, rivals

    def unpassed_chain(self):
        un = 0
        for lk in self.chain():
            if int(lk['n']) <= 0 or f"CR_PASS_AUTOLOCK_{lk['n']}" in self.files:
                break
            un += 1
        return un

    def spacing_holds(self, prom, race_losers, race_win):
        R, chosen = self.R, None
        lastp = max(self.st['promotes'], key=lambda p: T(p['t'])) if self.st['promotes'] else None
        loser_tags = {r['ent']['p']['tag']: r['rec']['role'] for r in race_losers}
        for e in prom:
            key, hold = e['p']['tag'], []
            if key in loser_tags:
                hold.append('RH-Q1: parked on the rework tail, NOT re-gated' if loser_tags[key] == 'parked-e32-retired'
                            else f"lost the race-hold pick to {race_win['rec']['gate']} (re-gate vs the new lock follows the promote)")
            exempt = bool(e['p'].get('ag_rebase_exempt24'))
            if not exempt and lastp and (self.now - T(lastp['t'])).total_seconds() < R['spacing_hours'] * 3600:
                hold.append(f"{R['spacing_hours']} h spacing: last auto-promote {lastp['tag']} at {lastp['t']}")
            un = self.unpassed_chain()
            if un >= R['max_chained_without_cr']:
                hold.append(f"{un} chained AUTO-LOCKs without CR_PASS_AUTOLOCK_<n>.txt (max {R['max_chained_without_cr']})")
            if chosen:
                hold.append(f"another chain ({chosen['p']['tag']}) promotes this tick")
            if hold:
                self.L('PENDING', f"{key}+{e['c']['tag']}", '; '.join(hold))
                if not self.st['seen'].get(key, '').startswith('PENDING'):
                    self.st['seen'][key] = 'PENDING'
                continue
            chosen = e
        return chosen

    def promote(self, chosen, race):
        R = self.R
        if not chosen:
            return None
        p, c = chosen['p'], chosen['c']
        if R['edits_need_running_gate'] and not self.running:
            self.L('NOTE', p['tag'], 'promote due but no gate is running; next tick')
            return None
        if p['tag'] in self.exe_fail:
            self.st['seen'][p['tag']] = 'CHECK_FAILED'
            self.L('BLOCKED', p['tag'], f"exe checks failed ({self.exe_fail[p['tag']]}); no promote")
            self.alert(f"ckfail_{p['tag']}", f"auto-promote {p['tag']} BLOCKED: exe checks failed ({self.exe_fail[p['tag']]})")
            return None
        kind = 'net' if p['kind'] == 'net' and self.lock['kind'] in ('base', 'net') else 'search'
        if p.get('ag_rebase_of') and kind != 'net' and R['cap_late_z']['z1_net_only']:
            self.st['seen'][p['tag']] = 'CHECK_FAILED Z not net-only'
            self.L('BLOCKED', p['tag'], f"CAP-LATE Z-1: re-gate of {p['ag_rebase_of']} is not net-only vs {self.lock['tag']}; no promote")
            return None
        nn = 1 + max([int(x['n']) for x in self.st['promotes']] + [int(self.lock['n']), 0])
        gt = re.sub(r'_vs_h256e12$', '', re.sub(r'^gate_', '', p['tag']))
        ltag = f'AUTOLOCK_{nn}_{gt}'
        newl = {'n': nn, 'tag': ltag, 'kind': kind, 'exe': p['exe'], 'sha': p['sha'], 'parent': self.lock}
        if self.crash_next:
            self.crash_next = False
            if R['inflight_record']:
                self.st['inflight'] = {'n': nn, 'ltag': ltag, 'gate': p['tag'], 'confirm': c['tag'], 'sha': p['sha'], 't': S(self.now),
                                       'parent': self.lock['tag'], 'parent_sha': self.lock['sha'], 'race_losers': []}
            self.lock = newl
            self.crashed = True
            self.L('CRASH', ltag, 'simulated crash after the AUTOLOCK dir + pointer write, before the state save (fixture event)')
            return None
        self.st['promotes'].append({'n': nn, 'tag': ltag, 'parent': self.lock['tag'], 'parent_sha': self.lock['sha'], 'gate': p['tag'],
                                    'confirm': c['tag'], 'sha': p['sha'], 'kind': kind, 't': S(self.now)})
        self.st['seen'][p['tag']] = f'PROMOTED {ltag}'
        self.L('PROMOTE', ltag, f"{p['tag']} H1 + {c['tag']} H1 vs {self.lock['tag']}; kind {kind}; exe {p['exe']} {p['sha']}; nps check warning-only")
        self.lock = newl
        return newl

    def regate_losers(self, promoted, race_losers, race_win):
        R = self.R
        if promoted and race_losers:
            for lz in race_losers:
                lp = lz['ent']['p']
                stem = re.sub(r'_vs_.*$', '', lp['tag'])
                nt = f"{stem}_rebase_vs_AL{promoted['n']}"
                if self.g(nt) or any(x['tag'] == nt for x in self.st['rebase_todo']):
                    continue
                if self.is_e32(lp['tag']) and self.e32_retired():
                    self.L('REWORK', lp['tag'], f"{lz['rec']['role']}: e32 lane retired (RH-Q1); H1 kept on record, NOT re-gated")
                    continue
                ng = {k: copy.deepcopy(v) for k, v in lp.items() if k not in ('confirm_of', 'ag_prev', 'ag_rebuilt_on', 'pooled', 'status')}
                z24 = stem in R['cap_late_z']['exempt24_stems'] or R['cap_late_z']['exempt24_all_regates']
                ng.update({'tag': nt, 'srand': self.fresh_srand(), 'openings_start': self.max_start() + 3000, 'base': promoted['sha'],
                           'ag_rebase_exempt24': z24, 'ag_rebase_of': lp['tag'], 'status': None})
                zst = self.e48_state() if z24 else ''
                if z24 and R['cap_late_z']['z2_hold_until_e48_h1'] and stem in R['cap_late_z']['exempt24_stems'] and not zst.startswith('H1 '):
                    ng['status'] = 'HELD_Z_until_G104c_H1'
                ng['_role'] = lz['rec']['role']
                self.st['rebase_todo'].append(ng)
        if self.st['rebase_todo']:
            adds = [x for x in self.st['rebase_todo'] if not self.g(x['tag'])]
            if adds and self.manifest_ok('race_rebase'):
                for ag in adds:
                    role = ag.pop('_role', '')
                    self.insert_after_running(ag)
                    self.L('REGATE', ag['tag'], f"re-gate of {ag['ag_rebase_of']} ({role}) vs {self.lock['tag']}: fresh srand {ag['srand']}, conc {ag['conc']}, "
                           f"exempt24 {ag['ag_rebase_exempt24']}" + (f", status {ag['status']}" if ag['status'] else '') + '; needs its own H1 + confirm')
                self.st['rebase_todo'] = []
            elif not adds:
                self.st['rebase_todo'] = []

    def z2(self):
        for hz in [x for x in self.gates if x['status'] == 'HELD_Z_until_G104c_H1']:
            if self.is_started(hz['tag']):
                continue
            zs = self.e48_state()
            if zs.startswith('PENDING'):
                continue
            if not self.manifest_ok(f"z2_{hz['tag']}"):
                continue
            if zs.startswith('H1 '):
                hz['status'] = None
                self.L('Z2_RELEASE', hz['tag'], f'CAP-LATE Z-2: {zs}; released to runnable (24 h waiver applies)')
            else:
                cs = [self.verdict(c['tag']) for c in self.confirms_of(self.R['rhq1']['e48_gate']) if self.rerun_counts(c)]
                zv = 'H0' if any((v or '').startswith('H0') for v in cs) else 'VOID' if 'VOID' in cs else 'NOH1'
                hz['status'] = f'DROPPED_Z_G104c_{zv}'
                self.L('Z2_DROP', hz['tag'], f'CAP-LATE Z-2: G104c did not end H1 ({zs}); never run; REWORK_LIST')

    def resolve_src(self, g):
        mode = self.R['step5']['src_resolution']
        if mode == 'exe_name':
            m = re.match(r'^forge_h256_(.+)\.exe$', g.get('exe', ''))
            name = f'src_h256_{m.group(1)}' if m else ''
            return name, bool(name) and name in self.src_dirs
        name = g.get('src_dir') or ''
        return name, bool(name) and name in self.src_dirs

    def step5(self, promoted):
        R = self.R
        nlk = promoted or (self.lock if int(self.lock['n']) > 0 and self.lock.get('parent') else None)
        if not nlk:
            return
        if R['edits_need_running_gate'] and not self.running:
            self.L('NOTE', nlk['tag'], 'rebuild/labels due but no gate is running; next tick')
            return
        old = nlk['parent']
        rb_on, nb = nlk['kind'] == 'net', 0
        for g in self.gates:
            if self.is_started(g['tag']) or self.verdict(g['tag']) or g['base'] != old['sha']:
                continue
            if g['sha'] == nlk['sha']:
                if 'lock vs itself' not in g['notes']:
                    g['notes'] += f" | vs {old['tag']}: its exe is now {nlk['tag']} (lock vs itself)"
                    self.L('LABEL', g['tag'], f"its exe is now {nlk['tag']}; lock vs itself is pointless; crew decides")
                continue
            src, ok = self.resolve_src(g)
            plain = not g['options'] and not g['confirm_of'] and g['kind'] == 'net'
            held = (g['status'] or '').startswith('HELD')
            if rb_on and plain and not held and not ok and R['step5']['unresolved'] == 'skip_alert':
                self.L('SKIP', g['tag'], f"net gate but source folder '{src or '(no src_dir)'}' not found; not rebuilt, keeps old opponent until fixed")
                self.alert(f"rbskip_{nlk['tag']}_{g['tag']}", f"rebuild on {nlk['tag']}: {g['tag']} skipped (source folder '{src or '(no src_dir)'}' unresolved)")
                continue
            if not rb_on or not plain or held or not ok:
                lab = f"vs {old['tag']}"
                if lab not in g['notes']:
                    g['notes'] += f' | {lab}'
                    self.L('LABEL', g['tag'], f"keeps old opponent {old['tag']} (lock moved to {nlk['tag']}; " +
                           ('search/option lock' if not rb_on else 'not a plain net gate' if not plain else 'HELD' if held else f"source folder '{src}' not found") + '); an H1 goes to COMBINE_LIST')
                continue
            if nb >= R['step5']['max_rebuild_per_tick']:
                self.L('SKIP', g['tag'], f"rebuild limit {R['step5']['max_rebuild_per_tick']} this tick; next tick")
                continue
            nb += 1
            gk = src[len('src_h256_'):] if src.startswith('src_h256_') else src
            prev = {'exe': g['exe'], 'sha': g['sha'], 'base': g['base'], 'srand': g['srand']}
            g.update({'exe': f"forge_h256_{gk}_AL{nlk['n']}.exe", 'sha': f"{g['sha']}~AL{nlk['n']}", 'base': nlk['sha'], 'srand': self.fresh_srand(),
                      'ag_rebuilt_on': nlk['tag'], 'ag_prev': prev})
            self.L('REBUILD', g['tag'], f"{src} + {nlk['tag']} tree -> {g['exe']}; opponent {nlk['tag']}; fresh srand {g['srand']}")

    def summary(self):
        self.L('END', 'lock', f"{self.lock['tag']} (n={self.lock['n']}); promotes " + (', '.join(f"{p['tag']}@{p['t']}" for p in self.st['promotes']) or 'none')
               + (f"; inflight {self.st['inflight']['ltag']}" if self.st['inflight'] else ''))
        for k in sorted(self.st['seen']):
            self.L('END', 'seen', f'{k} = {self.st["seen"][k]}')
        for g in self.gates:
            if g.get('ag_rebase_of') or g.get('ag_rebuilt_on') or g.get('ag_void_rerun_of') or g['tag'].endswith(('_rb1', '_rb2')):
                self.L('END', 'gate', f"{g['tag']} base {g['base']} srand {g['srand']} status {g['status']} exempt24 {g.get('ag_rebase_exempt24', False)}")


def load_rules(path, overrides=None):
    with open(path, encoding='utf-8') as f:
        rules = json.load(f)
    for k, v in (overrides or {}).items():
        cur = rules
        parts = k.split('.')
        for p in parts[:-1]:
            cur = cur[p]
        cur[parts[-1]] = v
    return rules


def simulate(rules, fx):
    return '\n'.join([f'# {VERSION} | rules {rules["name"]} | fixture {fx["name"]}'] + Sim(copy.deepcopy(rules), copy.deepcopy(fx)).run()) + '\n'


def main(argv=None):
    ap = argparse.ArgumentParser(description='S46 auto-promote rule replay simulator')
    ap.add_argument('--rules', required=True)
    ap.add_argument('--fixture', required=True)
    ap.add_argument('--set', action='append', default=[], help='rule override key=json, e.g. spacing_hours=12')
    ap.add_argument('--out')
    a = ap.parse_args(argv)
    ov = {}
    for s in a.set:
        k, v = s.split('=', 1)
        ov[k] = json.loads(v)
    rules = load_rules(a.rules, ov)
    with open(a.fixture, encoding='utf-8') as f:
        fx = json.load(f)
    txt = simulate(rules, fx)
    if a.out:
        with open(a.out, 'w', encoding='utf-8', newline='\n') as f:
            f.write(txt)
    else:
        sys.stdout.write(txt)
    return 0


if __name__ == '__main__':
    sys.exit(main())
