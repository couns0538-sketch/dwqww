#!/usr/bin/env python3
"""make_s46_fixtures.py (S46, opus 2026-10-27): writes fixtures/*.json for the promote simulator.
Each fixture = initial state + event timeline + hand-written `must` (ordered substrings) / `must_not` decisions taken from
the rule text (not from simulator output). Gate tags, conc and Elo values follow the real 2026-10-25/26 PC history
(G120 e32 s198 conc 7, G104 e48f006 conc 5, f029/f030/f031 net gates, G55/G56 suffixed source folders).
Deterministic; writes only into --out (default fixtures/ next to this file)."""
import argparse
import copy
import json
import os

L0 = {'tag': 'h256_e12', 'n': 0, 'sha': 'L0', 'kind': 'base', 'exe': 'forge_h256_e12.exe', 'parent': None}
G120T, G104T = 'gate120_e32f003rec_s198_vs_h256e12', 'gate104_e48f006_vs_h256e12'


def gate(tag, exe, sha, base, conc, srand, **kw):
    d = {'tag': tag, 'exe': exe, 'sha': sha, 'base': base, 'conc': conc, 'srand': srand, 'openings_start': srand % 100000}
    d.update(kw)
    return d


def al(n, sha, tag, parent, kind='net'):
    return {'tag': tag, 'n': n, 'sha': sha, 'kind': kind, 'exe': f'{tag}.exe', 'parent': parent}


AL1 = al(1, 'X120', 'AUTOLOCK_1_gate120_e32f003rec_s198', L0)
G120 = gate(G120T, 'forge_h256_s198.exe', 'X120', 'L0', 7, 344808634, src_dir='src_h256_e32f003rec_s198_ep32')
G120C = gate(G120T + '_confirm', 'forge_h256_s198.exe', 'X120', 'L0', 7, 559341020, confirm_of=G120T)
G104 = gate(G104T, 'forge_h256_e48f006.exe', 'X104', 'L0', 5, 1910442104, src_dir='src_h256_e48f006_ep48')
G104C = gate(G104T + '_confirm', 'forge_h256_e48f006.exe', 'X104', 'L0', 5, 1910442204, confirm_of=G104T)
FILL = gate('gate121_p23b_vs_h256e12', 'forge_h256_p23b.exe', 'X121', 'L0', 8, 401121, kind='search', options=['P23bTune=1'])


def ev(t, kind, **kw):
    d = {'t': t, 'ev': kind}
    d.update(kw)
    return d


def res(t, tag, verdict, elo, err, games, **kw):
    return ev(t, 'result', tag=tag, verdict=verdict, elo=elo, err=err, games=games, **kw)


H1 = 'H1 accepted'
G120_RES = res('2026-10-25T12:54', G120T, H1, 23.62, 11.9, 928)
G120C_RES = res('2026-10-25T14:36', G120T + '_confirm', H1, 14.46, 8.61, 1418)
G104_RES = res('2026-10-25T11:00', G104T, H1, 29.44, 13.23, 698)


def base_init(t, gates, running, results=(), **kw):
    d = {'t': t, 'lock': copy.deepcopy(L0), 'gates': copy.deepcopy(gates), 'running': running,
         'results': [{k: v for k, v in r.items() if k != 'ev'} for r in results]}
    d.update(kw)
    return d


FX = []


def fx(name, spec, about, init, events, must, must_not=()):
    FX.append({'name': name, 'spec_ref': spec, 'about': about, 'init': init, 'events': events, 'must': list(must), 'must_not': list(must_not)})


# (a) G120c H1 while G104c is pending -> hold
fx('a_race_hold_g120c_h1_g104c_pending', 'S46 (a)', 'G120+G120c H1+H1 vs h256_e12 while G104 is H1 and G104c is queued: race-hold, cap 12 h after G120c finished.',
   base_init('2026-10-25T14:40', [FILL, G120, G120C, G104, G104C], FILL['tag'], [G120_RES, G120C_RES, G104_RES]),
   [ev('2026-10-25T14:48', 'tick'), ev('2026-10-25T20:00', 'tick')],
   ['HOLD | gate120_e32f003rec_s198_vs_h256e12+gate120_e32f003rec_s198_vs_h256e12_confirm | PROMOTE_HOLD (race-hold)',
    'gate104_e48f006_vs_h256e12_confirm (queued); cap 2026-10-26T02:36', 'HOLD | gate120', '6.6 h left'], ['| PROMOTE |'])

# (b) both chains H1 -> rule-chosen winner promotes, loser re-gated vs the new lock with fresh srand
G130 = gate('gate130_e48f030_vs_AL1', 'forge_h256_e48f030_AL1.exe', 'X130', 'X120', 8, 1301, src_dir='src_h256_e48f030_AL1')
G130C = gate('gate130_e48f030_vs_AL1_confirm', 'forge_h256_e48f030_AL1.exe', 'X130', 'X120', 8, 1302, confirm_of=G130['tag'])
G131 = gate('gate131_e48f031_vs_AL1', 'forge_h256_e48f031_AL1.exe', 'X131', 'X120', 8, 1311, src_dir='src_h256_e48f031_AL1')
G131C = gate('gate131_e48f031_vs_AL1_confirm', 'forge_h256_e48f031_AL1.exe', 'X131', 'X120', 8, 1312, confirm_of=G131['tag'])
FILL1 = gate('gate132_spd_vs_AL1', 'forge_h256_spd_AL1.exe', 'X132', 'X120', 8, 1321, kind='search', options=['SpeedX=1'])
AL1_PROMOTED = {'promotes': [{'n': 1, 'tag': AL1['tag'], 'parent': 'h256_e12', 'parent_sha': 'L0', 'gate': G120T, 'confirm': G120T + '_confirm',
                              'sha': 'X120', 'kind': 'net', 't': '2026-10-25T17:18'}]}


def two_chain_init(c130, c131, g130=(12, 9, 1100), g131=(10, 9, 1200)):
    return base_init('2026-10-27T10:20', [FILL1, G130, G130C, G131, G131C], FILL1['tag'],
                     [res('2026-10-26T20:00', G130['tag'], H1, *g130), res('2026-10-26T20:30', G131['tag'], H1, *g131),
                      res('2026-10-27T10:00', G130C['tag'], H1, *c130), res('2026-10-27T10:10', G131C['tag'], H1, *c131)],
                     lock=copy.deepcopy(AL1), state=AL1_PROMOTED, files=['CR_PASS_AUTOLOCK_1'])


fx('b1_both_h1_pick_on_confirm_elo', 'S46 (b)', 'Two net chains vs AL1 are both H1+H1 in one tick: higher confirm Elo (15 +/- 8 vs 6 +/- 8, |d| 9 >= 8) wins and promotes AUTOLOCK_2; the loser is re-gated vs AUTOLOCK_2 with a fresh srand. CAP-LATE Z 8/8: the 24 h waiver is e48-only, so this re-gate is NOT exempt (the spec text "no 24 h wait" predates CAP-LATE Z; see README).',
   two_chain_init((15, 8, 1500), (6, 8, 1500)), [ev('2026-10-27T10:30', 'tick')],
   ['PICK | gate130_e48f030_vs_AL1 | picked on CONFIRM Elo 15 vs 6', 'PENDING | gate131_e48f031_vs_AL1+gate131_e48f031_vs_AL1_confirm | lost the race-hold pick',
    'PROMOTE | AUTOLOCK_2_gate130_e48f030_vs_AL1 |', 'REGATE | gate131_e48f031_rebase_vs_AL2 | re-gate of gate131_e48f031_vs_AL1 (lost-pick) vs AUTOLOCK_2_gate130_e48f030_vs_AL1: fresh srand',
    'exempt24 False'])
fx('b2_both_h1_tie_pooled_pick', 'S46 (b)', 'Confirm Elo 9 +/- 9 vs 6 +/- 8 is a tie (|d| 3 < 9): the games-weighted pooled gate+confirm Elo decides (7.31 vs 9.56), so the LOWER-confirm chain f031 wins.',
   two_chain_init((9, 9, 1500), (6, 8, 1500), g130=(5, 9, 1100), g131=(14, 9, 1200)), [ev('2026-10-27T10:30', 'tick')],
   ['PICK | gate131_e48f031_vs_AL1 | TIE on confirm Elo', 'pooled gate+confirm Elo 9.56 vs 7.31', 'PROMOTE | AUTOLOCK_2_gate131_e48f031_vs_AL1 |',
    'REGATE | gate130_e48f030_rebase_vs_AL2'])

# (c) TL in the first 300 games -> rollback
G56 = gate('gate56_auto000_vs_AL1', 'forge_h256_auto000_AL1.exe', 'X56', 'X120', 8, 5601)
G57 = gate('gate57_e20j_vs_AL1', 'forge_h256_e20j_AL1.exe', 'X57', 'X120', 8, 5701)
G58 = gate('gate58_e16q_vs_h256e12', 'forge_h256_e16q_AL1.exe', 'X58n', 'X120', 8, 5801, ag_rebuilt_on=AL1['tag'],
           ag_prev={'exe': 'forge_h256_e16q.exe', 'sha': 'X58', 'base': 'L0', 'srand': 5800})
G59 = gate('gate59_spd_vs_AL1', 'forge_h256_spd2.exe', 'X59', 'X120', 8, 5901, kind='search', options=['Spd=2'])


def rollback_fx(name, game, spec, about):
    fx(name, spec, about,
       base_init('2026-10-26T08:00', [G56, G57, G58, G59], G57['tag'], [], lock=copy.deepcopy(AL1), state=AL1_PROMOTED, started=[G56['tag']]),
       [res('2026-10-26T09:00', G56['tag'], 'cap with no decision', 2.0, 9.0, 1500, csv={'tl': 1, 'crash': 0, 'clean': 'NOT CLEAN'}),
        ev('2026-10-26T09:00', 'tl', tag=G56['tag'], tl=1, game=game), ev('2026-10-26T09:30', 'tick')],
       ['RESTORE | gate58_e16q_vs_h256e12 | rebuilt on AUTOLOCK_1_gate120_e32f003rec_s198: back to forge_h256_e16q.exe vs h256_e12',
        'RESTORE | gate59_spd_vs_AL1 | opponent AUTOLOCK_1_gate120_e32f003rec_s198 withdrawn -> h256_e12',
        'REGATE | gate56_auto000_vs_AL1_rb1 | re-queued by rollback', 'ROLLBACK | AUTOLOCK_1_gate120_e32f003rec_s198 | pointer AUTOLOCK_1_gate120_e32f003rec_s198 -> h256_e12',
        f'at game {game}', 'END | lock | h256_e12 (n=0)'], ['REGATE | gate57'])


rollback_fx('c_rollback_tl_in_first_300', 120, 'S46 (c)', 'A gate vs AUTOLOCK_1 has a time loss at game 120: pointer back to h256_e12, the gate rebuilt on AL1 restored, the unstarted AL1 gate moved back, the finished gate re-queued as _rb1 with a fresh srand; the running gate is left alone.')
rollback_fx('c2_rollback_tl_after_300_any_game', 900, 'S46 (c) note', 'Same, TL at game 900: autopromote.ps1 rolls back on a TL/crash in ANY later gate (rule 8), not only in the first 300 games as the S46 spec text says (README disagreement D1). A window of 300 makes this fixture fail (mutation check).')

# (d) two promotes inside 24 h -> second blocked
G140 = gate('gate140_e48f040_vs_AL1', 'forge_h256_e48f040_AL1.exe', 'X140', 'X120', 8, 1401)
G140C = gate('gate140_e48f040_vs_AL1_confirm', 'forge_h256_e48f040_AL1.exe', 'X140', 'X120', 8, 1402, confirm_of=G140['tag'])
fx('d_second_promote_inside_24h_blocked', 'S46 (d)', 'G120 chain promotes AUTOLOCK_1 at 17:18; a new chain vs AL1 is H1+H1 at 03:00 next day: PENDING (24 h spacing) until 17:18; promoted at the 17:30 tick (1 un-CR-passed AUTO-LOCK < 2).',
   base_init('2026-10-25T17:00', [FILL, G120, G120C], FILL['tag'], [G120_RES, G120C_RES]),
   [ev('2026-10-25T17:18', 'tick'), ev('2026-10-25T17:30', 'add_gate', gate=G140), ev('2026-10-25T17:31', 'add_gate', gate=G140C),
    ev('2026-10-25T18:00', 'start', tag=G140['tag']), res('2026-10-25T23:00', G140['tag'], H1, 18.0, 10.0, 900, next=G140C['tag']),
    res('2026-10-26T03:00', G140C['tag'], H1, 12.0, 9.0, 1300, next=FILL['tag']), ev('2026-10-26T03:30', 'tick'), ev('2026-10-26T17:00', 'tick'), ev('2026-10-26T17:30', 'tick')],
   ['PROMOTE | AUTOLOCK_1_gate120_e32f003rec_s198 |', 'PENDING | gate140_e48f040_vs_AL1+gate140_e48f040_vs_AL1_confirm | 24 h spacing: last auto-promote AUTOLOCK_1_gate120_e32f003rec_s198 at 2026-10-25T17:18',
    '2026-10-26T17:00 | PENDING | gate140', '2026-10-26T17:30 | PROMOTE | AUTOLOCK_2_gate140_e48f040_vs_AL1 |'])

# (e) hold reaches its cap
fx('e_hold_reaches_cap', 'S46 (e) + (v)', 'G120 chain on PROMOTE_HOLD while G104c runs; at 02:40 the 12 h cap (02:36) has passed: G120 promotes AUTOLOCK_1; the unfinished e48 chain is re-gated vs AL1 (fresh srand, conc 5, exempt24 True) and HELD_Z until G104c ends H1 (Z-2).',
   base_init('2026-10-25T14:40', [G120, G120C, G104, G104C, FILL], G104C['tag'], [G120_RES, G120C_RES, G104_RES]),
   [ev('2026-10-25T14:48', 'tick'), ev('2026-10-26T02:00', 'tick'), ev('2026-10-26T02:40', 'tick')],
   ['HOLD | gate120', 'gate104_e48f006_vs_h256e12_confirm (running)', '2026-10-26T02:00 | HOLD | gate120', '0.6 h left',
    'PICK | gate120_e32f003rec_s198_vs_h256e12 | race-hold cap expired (12 h since gate120_e32f003rec_s198_vs_h256e12_confirm finished 2026-10-25T14:36)',
    'PROMOTE | AUTOLOCK_1_gate120_e32f003rec_s198 |', 'REGATE | gate104_e48f006_rebase_vs_AL1 | re-gate of gate104_e48f006_vs_h256e12 (unfinished-at-cap)',
    'conc 5, exempt24 True, status HELD_Z_until_G104c_H1'])

# (f) H1 then confirm H0 -> no promote
G150 = gate('gate150_e48f050_vs_h256e12', 'forge_h256_e48f050.exe', 'X150', 'L0', 8, 1501)
G150C = gate('gate150_e48f050_vs_h256e12_confirm', 'forge_h256_e48f050.exe', 'X150', 'L0', 8, 1502, confirm_of=G150['tag'])
fx('f_h1_then_confirm_h0_no_promote', 'S46 (f)', 'Parent H1, confirm H0: INELIGIBLE for good, nothing promoted.',
   base_init('2026-10-25T20:00', [FILL, G150, G150C], FILL['tag'], [res('2026-10-25T16:00', G150['tag'], H1, 20.0, 10.0, 900),
                                                                    res('2026-10-25T19:50', G150C['tag'], 'H0 accepted', -3.0, 8.0, 1500)]),
   [ev('2026-10-25T20:10', 'tick'), ev('2026-10-25T20:40', 'tick')],
   ["INELIGIBLE | gate150_e48f050_vs_h256e12+gate150_e48f050_vs_h256e12_confirm | gate150_e48f050_vs_h256e12_confirm verdict 'H0 accepted'",
    'END | seen | gate150_e48f050_vs_h256e12 = INELIGIBLE'], ['| PROMOTE |'])

# (g) confirm vs a stale lock -> COMBINE_LIST
fx('g_confirm_vs_stale_lock_combine_list', 'S46 (g)', 'The lock moved to AUTOLOCK_1 while this chain ran vs h256_e12: H1+H1 vs the old lock goes to COMBINE_LIST, never promoted.',
   base_init('2026-10-25T20:00', [FILL1, G150, G150C], FILL1['tag'], [res('2026-10-25T15:00', G150['tag'], H1, 20.0, 10.0, 900),
                                                                      res('2026-10-25T19:50', G150C['tag'], H1, 11.0, 8.0, 1500)],
             lock=copy.deepcopy(AL1), state=AL1_PROMOTED),
   [ev('2026-10-25T20:10', 'tick')],
   ['COMBINE_LIST | gate150_e48f050_vs_h256e12+gate150_e48f050_vs_h256e12_confirm | H1+H1 but vs h256_e12 (L0); current lock is AUTOLOCK_1_gate120_e32f003rec_s198'],
   ['| PROMOTE |'])

# (h) third chained AUTO-LOCK without CR_PASS_AUTOLOCK -> held
AL2 = al(2, 'X131', 'AUTOLOCK_2_gate131_e48f031_vs_AL1', copy.deepcopy(AL1))
G160 = gate('gate160_e48f060_vs_AL2', 'forge_h256_e48f060_AL2.exe', 'X160', 'X131', 8, 1601)
G160C = gate('gate160_e48f060_vs_AL2_confirm', 'forge_h256_e48f060_AL2.exe', 'X160', 'X131', 8, 1602, confirm_of=G160['tag'])
FILL2 = gate('gate161_spd_vs_AL2', 'forge_h256_spd3.exe', 'X161', 'X131', 8, 1611, kind='search', options=['Spd=3'])
two_promotes = {'promotes': AL1_PROMOTED['promotes'] + [{'n': 2, 'tag': AL2['tag'], 'parent': AL1['tag'], 'parent_sha': 'X120', 'gate': 'gate131_e48f031_vs_AL1',
                                                         'confirm': 'gate131_e48f031_vs_AL1_confirm', 'sha': 'X131', 'kind': 'net', 't': '2026-10-26T18:00'}]}
fx('h_third_chained_autolock_needs_cr', 'S46 (h)', 'Current lock AUTOLOCK_2 (parent AUTOLOCK_1), no CR_PASS_AUTOLOCK file: a third chained AUTO-LOCK is held (max 2 without CR). CR_PASS_AUTOLOCK_2 appears -> promoted.',
   base_init('2026-10-27T20:00', [FILL2, G160, G160C], FILL2['tag'], [res('2026-10-27T12:00', G160['tag'], H1, 16.0, 10.0, 1000),
                                                                      res('2026-10-27T19:50', G160C['tag'], H1, 10.0, 8.0, 1500)],
             lock=copy.deepcopy(AL2), state=two_promotes),
   [ev('2026-10-27T20:30', 'tick'), ev('2026-10-27T21:00', 'file', name='CR_PASS_AUTOLOCK_2'), ev('2026-10-27T21:30', 'tick')],
   ['PENDING | gate160_e48f060_vs_AL2+gate160_e48f060_vs_AL2_confirm | 2 chained AUTO-LOCKs without CR_PASS_AUTOLOCK_<n>.txt (max 2)',
    '2026-10-27T21:30 | PROMOTE | AUTOLOCK_3_gate160_e48f060_vs_AL2 |'])

# (i) VOID confirm with a Verdict: H1 line never counts as H1
G170 = gate('gate170_e48f070_vs_h256e12', 'forge_h256_e48f070.exe', 'X170', 'L0', 8, 1701)
G170C = gate('gate170_e48f070_vs_h256e12_confirm', 'forge_h256_e48f070.exe', 'X170', 'L0', 8, 1702, confirm_of=G170['tag'])
fx('i_void_confirm_with_h1_line_never_h1', 'S46 rework (i) / CR HIGH-1', 'VOID.txt + a RESULT.md VOID header that still carries "Verdict: H1 accepted": never H1, chain not marked (a re-run may follow), nothing promoted.',
   base_init('2026-10-25T21:00', [FILL, G170, G170C], FILL['tag'], [res('2026-10-25T17:00', G170['tag'], H1, 18.0, 10.0, 900)]),
   [ev('2026-10-25T20:50', 'void', tag=G170C['tag'], verdict=H1, cause='engine option leak (ENGINE_OPTIONS_CHECK FAIL)'), ev('2026-10-25T21:10', 'tick')],
   ['NOTE | gate170_e48f070_vs_h256e12+gate170_e48f070_vs_h256e12_confirm | VOID (gate170_e48f070_vs_h256e12_confirm); not marked'], ['| PROMOTE |', 'INELIGIBLE'])

# (ii) lagging CSV -> wait and retry, never permanent INELIGIBLE
G180 = gate('gate180_e48f080_vs_h256e12', 'forge_h256_e48f080.exe', 'X180', 'L0', 8, 1801)
G180C = gate('gate180_e48f080_vs_h256e12_confirm', 'forge_h256_e48f080.exe', 'X180', 'L0', 8, 1802, confirm_of=G180['tag'])
fx('ii_lagging_csv_wait_then_promote', 'S46 rework (ii) / CR HIGH-2', 'The confirm RESULT.md is H1 but FORGE_RESULTS.csv has no row yet (Ledger-Sync lag): WAIT_DATA, not INELIGIBLE; the row arrives and the chain promotes.',
   base_init('2026-10-25T16:00', [FILL, G180, G180C], FILL['tag'], [res('2026-10-25T12:00', G180['tag'], H1, 18.0, 10.0, 900)]),
   [res('2026-10-25T16:00', G180C['tag'], H1, 12.0, 8.0, 1400, csv=None), ev('2026-10-25T16:05', 'tick'),
    ev('2026-10-25T16:20', 'csv', tag=G180C['tag'], csv={'tl': 0, 'crash': 0, 'clean': 'CLEAN'}), ev('2026-10-25T16:35', 'tick')],
   ['WAIT | gate180_e48f080_vs_h256e12+gate180_e48f080_vs_h256e12_confirm | WAIT_DATA: gate180_e48f080_vs_h256e12_confirm has no FORGE_RESULTS.csv row yet',
    '2026-10-25T16:35 | PROMOTE | AUTOLOCK_1_gate180_e48f080 |'], ['INELIGIBLE'])

# (iii) a rival confirm stopped by STOP/PAUSE/ABORTED is not a rival
fx('iii_stopped_rival_is_not_a_rival', 'S46 rework (iii) / CR MED-1 / RH-Q3', 'G104c is queued but STOP_<tag> is present: not a live rival, so no race-hold; the G120 chain promotes at once.',
   base_init('2026-10-25T14:40', [FILL, G120, G120C, G104, G104C], FILL['tag'], [G120_RES, G120C_RES, G104_RES], files=['STOP_' + G104C['tag']]),
   [ev('2026-10-25T14:48', 'tick')],
   ['NOTE | race-hold | not counted as rivals: gate104_e48f006_vs_h256e12_confirm STOP_gate104_e48f006_vs_h256e12_confirm present',
    'PROMOTE | AUTOLOCK_1_gate120_e32f003rec_s198 |'], ['| HOLD |'])

# (iv) crash between the lock-pointer write and the state save -> reconciled, no COMBINE_LIST
fx('iv_crash_after_pointer_reconciled', 'S46 rework (iv) / CR MED-4', 'The promote crashes after the AUTOLOCK dir + pointer write: the next tick finishes the bookkeeping from the in-flight record; the chain never lands on COMBINE_LIST.',
   base_init('2026-10-25T14:40', [FILL, G120, G120C], FILL['tag'], [G120_RES, G120C_RES]),
   [ev('2026-10-25T14:45', 'crash_next_promote'), ev('2026-10-25T14:48', 'tick'), ev('2026-10-25T15:18', 'tick')],
   ['CRASH | AUTOLOCK_1_gate120_e32f003rec_s198 |', '2026-10-25T15:18 | RECONCILE | AUTOLOCK_1_gate120_e32f003rec_s198 |',
    'END | seen | gate120_e32f003rec_s198_vs_h256e12 = PROMOTED AUTOLOCK_1_gate120_e32f003rec_s198 (reconciled)'], ['COMBINE_LIST'])

# (v) CAP-LATE Z
CAP_EVENTS = [ev('2026-10-25T14:48', 'tick'), ev('2026-10-26T02:40', 'tick')]
REGATE = 'gate104_e48f006_rebase_vs_AL1'
fx('v_cap_late_z_g104c_h1_releases_regate', 'S46 rework (v) / CAP-LATE Z 8/8 + Z-1/Z-2', 'The cap fires: e32 becomes AUTOLOCK_1; the e48 re-gate vs AL1 is HELD_Z. G104c then ends H1 vs h256_e12: that chain goes to COMBINE_LIST and Z-2 releases the re-gate, which (exempt from the 24 h rule) later promotes AUTOLOCK_2 as kind net only 8 h after AL1.',
   base_init('2026-10-25T14:40', [G120, G120C, G104, G104C, FILL], G104C['tag'], [G120_RES, G120C_RES, G104_RES]),
   CAP_EVENTS + [res('2026-10-26T04:00', G104C['tag'], H1, 7.9, 8.9, 1500, next=FILL['tag']), ev('2026-10-26T04:30', 'tick'),
                 ev('2026-10-26T05:00', 'start', tag=REGATE), res('2026-10-26T08:00', REGATE, H1, 10.0, 9.0, 900),
                 ev('2026-10-26T08:00', 'add_gate', after_running=False, gate=gate(REGATE + '_confirm', 'forge_h256_e48f006.exe', 'X104', 'X120', 5, 1910449999, confirm_of=REGATE)),
                 ev('2026-10-26T08:01', 'start', tag=REGATE + '_confirm'), res('2026-10-26T10:00', REGATE + '_confirm', H1, 8.0, 8.0, 1500, next=FILL['tag']),
                 ev('2026-10-26T10:30', 'tick')],
   ['PROMOTE | AUTOLOCK_1_gate120_e32f003rec_s198 |', 'status HELD_Z_until_G104c_H1',
    'COMBINE_LIST | gate104_e48f006_vs_h256e12+gate104_e48f006_vs_h256e12_confirm | H1+H1 but vs h256_e12',
    'Z2_RELEASE | gate104_e48f006_rebase_vs_AL1 | CAP-LATE Z-2: H1 gate104_e48f006_vs_h256e12_confirm',
    '2026-10-26T10:30 | PROMOTE | AUTOLOCK_2_gate104_e48f006_rebase_vs_AL1 | gate104_e48f006_rebase_vs_AL1 H1 + gate104_e48f006_rebase_vs_AL1_confirm H1 vs AUTOLOCK_1_gate120_e32f003rec_s198; kind net'],
   ['24 h spacing'])
fx('v2_cap_late_z_g104c_h0_drops_regate', 'S46 rework (v) / Z-2', 'Same cap promote; G104c then ends H0: the HELD_Z e48 re-gate is dropped to the rework list and never runs (RH-Q2).',
   base_init('2026-10-25T14:40', [G120, G120C, G104, G104C, FILL], G104C['tag'], [G120_RES, G120C_RES, G104_RES]),
   CAP_EVENTS + [res('2026-10-26T04:00', G104C['tag'], 'H0 accepted', -6.0, 8.9, 1500, next=FILL['tag']), ev('2026-10-26T04:30', 'tick')],
   ['status HELD_Z_until_G104c_H1', "INELIGIBLE | gate104_e48f006_vs_h256e12+gate104_e48f006_vs_h256e12_confirm | gate104_e48f006_vs_h256e12_confirm verdict 'H0 accepted'",
    'Z2_DROP | gate104_e48f006_rebase_vs_AL1 | CAP-LATE Z-2: G104c did not end H1', 'END | gate | gate104_e48f006_rebase_vs_AL1 base X120 srand', 'status DROPPED_Z_G104c_H0'],
   ['Z2_RELEASE'])

G104S = dict(G104, kind='search')
fx('v3_cap_late_z1_rebase_not_net_only_blocked', 'S46 rework (v) / CR Z-1', 'Same path as (v), but the e48 tree differs from AUTOLOCK_1 in more than src/nnue_weights.inc (kind search): its H1+H1 re-gate chain is BLOCKED by Z-1 and never promoted.',
   base_init('2026-10-25T14:40', [G120, G120C, G104S, G104C, FILL], G104C['tag'], [G120_RES, G120C_RES, G104_RES]),
   CAP_EVENTS + [res('2026-10-26T04:00', G104C['tag'], H1, 7.9, 8.9, 1500, next=FILL['tag']), ev('2026-10-26T04:30', 'tick'),
                 ev('2026-10-26T05:00', 'start', tag=REGATE), res('2026-10-26T08:00', REGATE, H1, 10.0, 9.0, 900),
                 ev('2026-10-26T08:00', 'add_gate', after_running=False, gate=gate(REGATE + '_confirm', 'forge_h256_e48f006.exe', 'X104', 'X120', 5, 1910449999, confirm_of=REGATE, kind='search')),
                 ev('2026-10-26T08:01', 'start', tag=REGATE + '_confirm'), res('2026-10-26T10:00', REGATE + '_confirm', H1, 8.0, 8.0, 1500, next=FILL['tag']),
                 ev('2026-10-26T10:30', 'tick')],
   ['Z2_RELEASE | gate104_e48f006_rebase_vs_AL1', 'BLOCKED | gate104_e48f006_rebase_vs_AL1 | CAP-LATE Z-1: re-gate of gate104_e48f006_vs_h256e12 is not net-only vs AUTOLOCK_1_gate120_e32f003rec_s198',
    'END | seen | gate104_e48f006_rebase_vs_AL1 = CHECK_FAILED Z not net-only'], ['PROMOTE | AUTOLOCK_2'])

# (vi) VOID-HOLD
VR1 = G104C['tag'] + '_vr1'
fx('vi_void_hold_one_rerun', 'S46 rework (vi) / VOID-HOLD 8/8', 'G104c goes VOID while G120 is held: ONE re-run is queued (fresh srand, conc 5), the hold stays inside the same cap; the re-run ends H1, so RH-Q1 picks e48 and G120 is parked (rework tail, no re-gate).',
   base_init('2026-10-25T14:40', [G120, G120C, G104, G104C, FILL], G104C['tag'], [G120_RES, G120C_RES, G104_RES]),
   [ev('2026-10-25T14:48', 'tick'), ev('2026-10-25T15:30', 'void', tag=G104C['tag'], verdict='cap with no decision', cause='engine option leak', next=FILL['tag']),
    ev('2026-10-25T15:31', 'start', tag=FILL['tag']), ev('2026-10-25T16:00', 'tick'), ev('2026-10-25T16:30', 'start', tag=VR1),
    res('2026-10-26T00:30', VR1, H1, 12.0, 10.0, 1100, next=FILL['tag']), ev('2026-10-26T01:00', 'tick')],
   ['VOID_RERUN | gate104_e48f006_vs_h256e12_confirm_vr1 | ONE re-run of VOID confirm gate104_e48f006_vs_h256e12_confirm (engine option leak)',
    'same cap 2026-10-26T02:36', '2026-10-25T16:00 | HOLD | gate120', 'gate104_e48f006_vs_h256e12_confirm_vr1 (queued (VOID re-run))',
    'PICK | gate104_e48f006_vs_h256e12 |', 'RH-Q1 5/8', 'PROMOTE | AUTOLOCK_1_gate104_e48f006 |', 'REWORK | gate120_e32f003rec_s198_vs_h256e12 | parked-e32-retired'],
   ['REGATE | gate120'])

# (vii) RH-Q2 + RH-Q3
G190 = gate('gate190_e48f090_vs_h256e12', 'forge_h256_e48f090.exe', 'X190', 'L0', 8, 1901)
G190C = gate('gate190_e48f090_vs_h256e12_confirm', 'forge_h256_e48f090.exe', 'X190', 'L0', 8, 1902, confirm_of=G190['tag'], status='HELD_NEEDS_CR: no CR pass yet')
fx('vii_rhq2_h0_rival_rework_rhq3_held_not_rival', 'S46 rework (vii) / RH-Q2, RH-Q3', 'A confirm in HELD status is not a rival (Q3); the live rival G104c ends H0: hold released, G120 promotes, G104 goes to the rework list and is not re-gated (Q2).',
   base_init('2026-10-25T14:40', [G120, G120C, G104, G104C, G190, G190C, FILL], G104C['tag'], [G120_RES, G120C_RES, G104_RES,
                                                                                                res('2026-10-25T10:00', G190['tag'], H1, 15.0, 10.0, 900)]),
   [ev('2026-10-25T14:48', 'tick'), res('2026-10-25T18:00', G104C['tag'], 'H0 accepted', -5.0, 9.0, 1500, next=FILL['tag']), ev('2026-10-25T18:30', 'tick')],
   ["NOTE | race-hold | not counted as rivals: gate190_e48f090_vs_h256e12_confirm status 'HELD_NEEDS_CR: no CR pass yet'", 'HOLD | gate120',
    "PICK | gate120_e32f003rec_s198_vs_h256e12 | race-hold released: rival(s) gate104_e48f006_vs_h256e12_confirm='H0 accepted'",
    'PROMOTE | AUTOLOCK_1_gate120_e32f003rec_s198 |', "REWORK | gate104_e48f006_vs_h256e12 | RH-Q2: rival confirm gate104_e48f006_vs_h256e12_confirm ended 'H0 accepted'"],
   ['REGATE | gate104'])

# (viii) the live state of 2026-10-25 16:15 CET (source folder names as listed read-only on the PC, 2026-10-27)
F029 = gate('gate_auto_e48f029_vs_h256e12', 'forge_h256_auto_e48f029.exe', 'X029', 'L0', 7, 2901, src_dir='src_h256_auto_e48f029')
F030 = gate('gate122_e48f030_vs_h256e12', 'forge_h256_f030.exe', 'X030', 'L0', 7, 3001, src_dir='src_h256_f030')
F034 = gate('gate124_e48f034_vs_h256e12', 'forge_h256_f034.exe', 'X034', 'L0', 7, 3401, src_dir='src_h256_f034')
F042 = gate('gate125_e48f042_vs_h256e12', 'forge_h256_f042.exe', 'X042', 'L0', 7, 4201, src_dir='src_h256_f042')
F031 = gate('gate123_e48f031_vs_h256e12', 'forge_h256_f031.exe', 'X031', 'L0', 7, 3101, src_dir='src_h256_f031')
F031C = gate('gate123_e48f031_vs_h256e12_confirm', 'forge_h256_f031.exe', 'X031', 'L0', 7, 3102, confirm_of=F031['tag'])
fx('viii_live_state_net_gates_retarget', 'S46 rework (viii)', 'Live state 16:15: G120c H1 on hold, G104c running, five e48 net gates queued vs h256_e12. At the cap e32 auto-locks: four net gates are rebuilt vs AUTOLOCK_1 with fresh srands (4 per tick), the search gate keeps h256_e12 (label). The driver starts the fifth (f031) vs h256_e12 before the next tick, so it is no longer rebuilt and its H1+H1 goes to COMBINE_LIST: never promoted vs the stale lock.',
   base_init('2026-10-25T16:15', [G120, G120C, G104, G104C, F029, F030, F034, F042, F031, FILL], G104C['tag'], [G120_RES, G120C_RES, G104_RES],
             src_dirs=['src_h256_auto_e48f029', 'src_h256_f030', 'src_h256_f034', 'src_h256_f042', 'src_h256_f031']),
   [ev('2026-10-25T16:18', 'tick'), ev('2026-10-26T02:40', 'tick'),
    res('2026-10-26T02:50', G104C['tag'], 'cap with no decision', 7.18, 8.49, 1500, next=F031['tag']), ev('2026-10-26T03:10', 'tick'),
    ev('2026-10-26T05:00', 'add_gate', after_running=True, gate=F031C), res('2026-10-26T05:00', F031['tag'], H1, 19.0, 11.0, 800, next=F031C['tag']),
    res('2026-10-26T07:00', F031C['tag'], H1, 9.0, 8.0, 1500, next=FILL['tag']), ev('2026-10-26T07:30', 'tick')],
   ['PROMOTE | AUTOLOCK_1_gate120_e32f003rec_s198 |', 'REBUILD | gate_auto_e48f029_vs_h256e12 | src_h256_auto_e48f029 + AUTOLOCK_1_gate120_e32f003rec_s198 tree',
    'REBUILD | gate122_e48f030_vs_h256e12 | src_h256_f030 +', "SKIP | gate123_e48f031_vs_h256e12 | rebuild limit 4 this tick",
    'LABEL | gate121_p23b_vs_h256e12 | keeps old opponent h256_e12', 'Z2_DROP | gate104_e48f006_rebase_vs_AL1',
    'COMBINE_LIST | gate123_e48f031_vs_h256e12+gate123_e48f031_vs_h256e12_confirm | H1+H1 but vs h256_e12'],
   ['PROMOTE | AUTOLOCK_2', 'REBUILD | gate123'])

# step-5 suffix regression fixture (N29, found 2026-10-25 18:01 CET on G55/G56); suffixed folders as listed read-only on the PC
S5 = [gate('gate98_e12rec_vs_h256e12', 'forge_h256_e12rec.exe', 'X98', 'L0', 8, 9801, src_dir='src_h256_e12rec'),
      gate('gate55_e20i_vs_h256e12', 'forge_h256_e20i.exe', 'X55', 'L0', 8, 5501, src_dir='src_h256_e20i_ep20'),
      gate('gate56_auto000_vs_h256e12', 'forge_h256_auto000.exe', 'X56b', 'L0', 8, 5601, src_dir='src_h256_auto000_ep16'),
      gate('gate70_k_vs_h256e12', 'forge_h256_k.exe', 'X70', 'L0', 8, 7001, src_dir='src_h256_k_ep16'),
      gate('gate119_e32f003rec_s197_vs_h256e12', 'forge_h256_s197.exe', 'X119', 'L0', 8, 11901, src_dir='src_h256_s197'),
      gate('gate99_e16x_vs_h256e12', 'forge_h256_e16x.exe', 'X99', 'L0', 8, 9901, src_dir='src_h256_e16x_ep16')]
fx('s5_step5_suffix_src_dir_resolution', 'S46 step-5 suffix regression (N29)', 'After a net AUTO-LOCK, step 5 must find the source folder of each queued net gate from the manifest src_dir, so the suffixed folders that exist on the PC (src_h256_e20i_ep20, src_h256_auto000_ep16, src_h256_k_ep16) resolve. The live script derives src_h256_<gk> from the exe name and silently kept the old opponent (G55/G56, 2026-10-25 18:01 CET). A missing folder is SKIPPED with a loud rbskip alert. 4 rebuilds per tick, the 5th on the next tick.',
   base_init('2026-10-25T14:40', [FILL, G120, G120C] + S5, FILL['tag'], [G120_RES, G120C_RES],
             src_dirs=['src_h256_e12rec', 'src_h256_e20i_ep20', 'src_h256_auto000_ep16', 'src_h256_k_ep16', 'src_h256_s197']),
   [ev('2026-10-25T14:48', 'tick'), ev('2026-10-25T15:18', 'tick')],
   ['PROMOTE | AUTOLOCK_1_gate120_e32f003rec_s198 |', 'REBUILD | gate98_e12rec_vs_h256e12 |', 'REBUILD | gate55_e20i_vs_h256e12 | src_h256_e20i_ep20 +',
    'REBUILD | gate56_auto000_vs_h256e12 | src_h256_auto000_ep16 +', 'REBUILD | gate70_k_vs_h256e12 | src_h256_k_ep16 +',
    "SKIP | gate99_e16x_vs_h256e12 | net gate but source folder 'src_h256_e16x_ep16' not found", 'ALERT | rbskip_',
    '2026-10-25T15:18 | REBUILD | gate119_e32f003rec_s197_vs_h256e12 | src_h256_s197 +'],
   ['LABEL | gate55', 'LABEL | gate56', 'LABEL | gate70', 'LABEL | gate99'])

# extra: RH-Q1 both H1 -> e48 wins regardless of Elo
fx('x_rhq1_both_h1_e48_wins', 'RH-Q1 5/8', 'Both chains H1+H1 vs h256_e12 in one tick; G120c has the higher confirm Elo (14.46 vs 7.9) but RH-Q1 promotes e48 (conc 7 vs 5 not comparable); G120 parked on the rework tail, not re-gated.',
   base_init('2026-10-25T14:40', [G120, G120C, G104, G104C, FILL], G104C['tag'], [G120_RES, G120C_RES, G104_RES]),
   [ev('2026-10-25T14:48', 'tick'), res('2026-10-25T20:00', G104C['tag'], H1, 7.9, 8.9, 1500, next=FILL['tag']), ev('2026-10-25T20:30', 'tick')],
   ['HOLD | gate120', 'PICK | gate104_e48f006_vs_h256e12 | RH-Q1 5/8: e32 lane retired', 'PROMOTE | AUTOLOCK_1_gate104_e48f006 |',
    'REWORK | gate120_e32f003rec_s198_vs_h256e12 | parked-e32-retired'], ['REGATE | gate120'])

# extra: MED-2 RH-Q1 hold when e48 is H1 but not promotable, FALLBACK at the cap
fx('y_med2_e48_not_promotable_hold_then_fallback', 'CR MED-2', 'G104c is H1 but the G104 CSV row says NOT CLEAN (a crash): the e48 chain is INELIGIBLE, the e32 chain is not promoted alone (RH-Q1 HOLD) until the 12 h cap, then promoted as a loud RH-Q1 FALLBACK.',
   base_init('2026-10-25T14:40', [G120, G120C, G104, G104C, FILL], FILL['tag'], [G120_RES, G120C_RES,
             res('2026-10-25T11:00', G104T, H1, 29.44, 13.23, 698, csv={'tl': 0, 'crash': 1, 'clean': 'NOT CLEAN'}),
             res('2026-10-25T14:00', G104C['tag'], H1, 9.0, 8.9, 1500)]),
   [ev('2026-10-25T14:48', 'tick'), ev('2026-10-26T02:40', 'tick')],
   ["INELIGIBLE | gate104_e48f006_vs_h256e12+gate104_e48f006_vs_h256e12_confirm | gate104_e48f006_vs_h256e12 CSV TL 0 crash 1 clean 'NOT CLEAN'",
    'HOLD | gate120_e32f003rec_s198_vs_h256e12 | RH-Q1 HOLD: G104c is H1 but the e48 chain is not promotable', 'ALERT | q1fallback |',
    'PROMOTE | AUTOLOCK_1_gate120_e32f003rec_s198 |'])

# extra: QA CRfix scenario G: G104c H1 but no CSV row yet -> e48 WAIT_DATA, quiet RH-Q1 hold; the row lands -> e48 promoted, G120 parked
fx('ii2_waitdata_e48_quiet_rhq1_hold', 'CR HIGH-2 + MED-2 (QA CRfix scenario G)', 'G104c RESULT.md is H1 but FORGE_RESULTS.csv has no row yet: the e48 chain WAITs (not marked); G104c H1 already retires the e32 lane, so the G120 chain is NOT promoted alone (RH-Q1 HOLD, quiet because e48 only waits for data). The row lands: e48 promotes AUTOLOCK_1, G120 parked.',
   base_init('2026-10-25T14:40', [G120, G120C, G104, G104C, FILL], FILL['tag'], [G120_RES, G120C_RES, G104_RES]),
   [res('2026-10-25T15:00', G104C['tag'], H1, 9.0, 8.9, 1500, csv=None), ev('2026-10-25T15:18', 'tick'),
    ev('2026-10-25T15:30', 'csv', tag=G104C['tag'], csv={'tl': 0, 'crash': 0, 'clean': 'CLEAN'}), ev('2026-10-25T15:48', 'tick')],
   ['WAIT | gate104_e48f006_vs_h256e12+gate104_e48f006_vs_h256e12_confirm | WAIT_DATA', 'HOLD | gate120_e32f003rec_s198_vs_h256e12 | RH-Q1 HOLD: G104c is H1 but the e48 chain is not promotable (e48 chain WAIT_DATA)',
    '2026-10-25T15:48 | PICK | gate104_e48f006_vs_h256e12 | RH-Q1 5/8', 'PROMOTE | AUTOLOCK_1_gate104_e48f006 |', 'REWORK | gate120_e32f003rec_s198_vs_h256e12 | parked-e32-retired'],
   ['ALERT | q1hold_', 'INELIGIBLE'])

# extra: QA CRfix scenario H: e48 wins the pick but its exe checks fail -> BLOCKED; then loud RH-Q1 hold; FALLBACK e32 at the cap
fx('z_exe_check_fail_blocked_then_fallback', 'rule 2 + CR MED-2 (QA CRfix scenario H)', 'Both chains H1+H1: RH-Q1 picks e48, but its exe checks fail (bench != gate prebench): BLOCKED + alert, no promote. Next tick G104 is CHECK_FAILED, the e32 chain is held loudly (RH-Q1 HOLD) until the 12 h cap, then promoted as RH-Q1 FALLBACK.',
   base_init('2026-10-25T14:40', [G120, G120C, G104, G104C, FILL], FILL['tag'], [G120_RES, G120C_RES, G104_RES, res('2026-10-25T14:30', G104C['tag'], H1, 9.0, 8.9, 1500)]),
   [ev('2026-10-25T14:45', 'exe_check_fail', tag=G104T, why='bench 328459/945640/3024381/9162399/20421972 != gate prebench'), ev('2026-10-25T14:48', 'tick'),
    ev('2026-10-25T15:18', 'tick'), ev('2026-10-26T02:40', 'tick')],
   ['PICK | gate104_e48f006_vs_h256e12 | RH-Q1 5/8', 'BLOCKED | gate104_e48f006_vs_h256e12 | exe checks failed', 'ALERT | ckfail_gate104_e48f006_vs_h256e12 |',
    "2026-10-25T15:18 | HOLD | gate120_e32f003rec_s198_vs_h256e12 | RH-Q1 HOLD: G104c is H1 but the e48 chain is not promotable (e48 chain seen 'CHECK_FAILED')",
    'ALERT | q1hold_gate120_e32f003rec_s198_vs_h256e12 |', '2026-10-26T02:40 | ALERT | q1fallback |', 'PROMOTE | AUTOLOCK_1_gate120_e32f003rec_s198 |'],
   ['PROMOTE | AUTOLOCK_1_gate104'])

# real replay: 2026-10-25 15:48-18:53 PC clock, as logged by the live autopromote.ps1 (autonomy/autopromote.log, copied read-only)
CAPV = 'Cap with no decision (LLR 1.23 inside (-2.94, 2.94)); nothing claimed'
F029R = gate('gate_auto_e48f029_vs_h256e12', 'forge_h256_auto_e48f029.exe', 'X029', 'L0', 7, 2901, src_dir='src_h256_auto_e48f029')
REAL_NET = [gate('gate122_e48f030_vs_h256e12', 'forge_h256_f030.exe', 'X030', 'L0', 7, 3001, src_dir='src_h256_f030'),
            gate('gate123_e48f031_vs_h256e12', 'forge_h256_f031.exe', 'X031', 'L0', 7, 3101, src_dir='src_h256_f031'),
            gate('gate103_e16f004_vs_h256e12', 'forge_h256_f004.exe', 'X004', 'L0', 5, 1031, src_dir='src_h256_f004'),
            gate('gate98_e12rec_vs_h256e12', 'forge_h256_e12rec.exe', 'X98r', 'L0', 5, 981, src_dir='src_h256_e12rec'),
            gate('gate105_e16f007_vs_h256e12', 'forge_h256_f007.exe', 'X007', 'L0', 5, 1051, src_dir='src_h256_f007'),
            gate('gate106_e20f008_vs_h256e12', 'forge_h256_f008.exe', 'X008', 'L0', 5, 1061, src_dir='src_h256_f008')]
fx('real_20261025_al1_promote_replay', 'real-file replay', 'Replay of the real 2026-10-25 PC timeline (PC clock = CET+1h): G120c H1 at 15:36, PROMOTE_HOLD at the 15:48-17:48 ticks while G104c ran, G104c ended capped, the 18:18 tick released the hold, promoted AUTOLOCK_1_gate120_e32f003rec_s198, put G104 on the rework list (RH-Q2) and rebuilt the first 4 queued net gates (f030, f031, f004, e12rec); the 18:53 tick rebuilt the next ones. Compared decision by decision with the real autopromote.log by s46_real_replay_compare.py.',
   base_init('2026-10-25T15:40', [G120, G120C, G104, G104C, F029R] + REAL_NET + [FILL], G104C['tag'],
             [res('2026-10-25T13:54', G120T, H1, 23.62, 11.9, 928), res('2026-10-25T12:00', G104T, H1, 29.44, 13.23, 698),
              res('2026-10-25T15:36', G120T + '_confirm', H1, 14.46, 8.61, 1418)],
             src_dirs=['src_h256_auto_e48f029', 'src_h256_f030', 'src_h256_f031', 'src_h256_f004', 'src_h256_e12rec', 'src_h256_f007', 'src_h256_f008']),
   [ev('2026-10-25T15:48', 'tick'), ev('2026-10-25T16:18', 'tick'), ev('2026-10-25T16:48', 'tick'), ev('2026-10-25T17:18', 'tick'), ev('2026-10-25T17:48', 'tick'),
    res('2026-10-25T18:00', G104C['tag'], CAPV, 7.18, 8.49, 1500, next=F029R['tag']), ev('2026-10-25T18:18', 'tick'), ev('2026-10-25T18:53', 'tick')],
   ['2026-10-25T15:48 | HOLD | gate120', '2026-10-25T17:48 | HOLD | gate120', "INELIGIBLE | gate104_e48f006_vs_h256e12+gate104_e48f006_vs_h256e12_confirm | gate104_e48f006_vs_h256e12_confirm verdict 'Cap with no decision",
    "PICK | gate120_e32f003rec_s198_vs_h256e12 | race-hold released: rival(s) gate104_e48f006_vs_h256e12_confirm='Cap with no decision", '2026-10-25T18:18 | PROMOTE | AUTOLOCK_1_gate120_e32f003rec_s198 |',
    "REWORK | gate104_e48f006_vs_h256e12 | RH-Q2: rival confirm gate104_e48f006_vs_h256e12_confirm ended 'Cap with no decision",
    'REBUILD | gate122_e48f030_vs_h256e12', 'REBUILD | gate123_e48f031_vs_h256e12', 'REBUILD | gate103_e16f004_vs_h256e12', 'REBUILD | gate98_e12rec_vs_h256e12',
    'SKIP | gate105_e16f007_vs_h256e12 | rebuild limit 4', '2026-10-25T18:53 | REBUILD | gate105_e16f007_vs_h256e12'],
   ['REGATE'])

# extra: L8 no running gate -> promote waits
fx('w_no_running_gate_promote_waits', 'CR L8 / rule 3 boundary', 'No gate is running (driver between gates): the promote waits for the next tick with a running gate.',
   base_init('2026-10-25T14:40', [FILL, G120, G120C], None, [G120_RES, G120C_RES]),
   [ev('2026-10-25T14:48', 'tick'), ev('2026-10-25T15:00', 'start', tag=FILL['tag']), ev('2026-10-25T15:18', 'tick')],
   ['NOTE | gate120_e32f003rec_s198_vs_h256e12 | promote due but no gate is running; next tick', '2026-10-25T15:18 | PROMOTE | AUTOLOCK_1_gate120_e32f003rec_s198 |'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures'))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for f in FX:
        with open(os.path.join(a.out, f['name'] + '.json'), 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(f, fh, indent=1, sort_keys=True)
            fh.write('\n')
    print(f'wrote {len(FX)} fixtures to {a.out}')


if __name__ == '__main__':
    main()
