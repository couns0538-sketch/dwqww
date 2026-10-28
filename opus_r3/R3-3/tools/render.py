"""Render GATE_PROPOSALS.md, GATE_ENTRIES.json and SRAND_CHECK.md for R3-3 from the collected data.

Usage: python -I -B render.py <workdir F:/opus_scratch/r3/R3-3> <outdir>
Reads (relative to workdir): tools/entries.py, scan/srands.json, scan/summary_all.json, scan/fs_scan.json,
scan/git_scan.json (optional), pins/*_pins.json, exe_map.json, model/sprt_cap_model.json, pc_copies/*.
"""
import glob
import hashlib
import importlib.util
import json
import os
import re
import sys

W = sys.argv[1]
OUT = sys.argv[2]
BIN = r'C:\Users\Administrator\grok-pc\forge_push\bin'
FC = r'C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe'
BOOK = r'C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn'
GATE_OUT = r'F:\forge_push'
EXE_SRC = r'F:\opus_scratch\r3\exe'
BASE_NAME = 'base_r3_off'
EARLY = {'games': 750, 'elo_max': -8, 'llr_max': -1.5,
         'rule': 'net-only early stop, crew vote 8/8 2026-10-25: first block >= 750 games with Elo < -8 AND LLR < -1.5 -> H0-early; net goes on the rework list, never dropped; re-gate fresh, never pooled'}


def jload(p):
    return json.load(open(os.path.join(W, p), encoding='utf-8'))


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


spec = importlib.util.spec_from_file_location('entries', os.path.join(W, 'tools', 'entries.py'))
ent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ent)
AL1 = ent.AL1
srands = jload('scan/srands.json')
exe_map = jload('exe_map.json')
model = jload('model/sprt_cap_model.json')
pins = {}
pin_src = {}
for p in sorted(glob.glob(os.path.join(W, 'pins', '*_pins.json'))):
    d = json.load(open(p))
    for label, r in d['runs'].items():
        pins.setdefault(label, r['pins'])
        pin_src.setdefault(label, os.path.basename(p))
switch_ids = {}
sw_path = os.path.join(W, 'pins', 'switch_identity.json')
if os.path.exists(sw_path):
    switch_ids = json.load(open(sw_path))
head = exe_map.get('head') or None
PROBE_HEAD = '2047348a'


def exe_name(key):
    return exe_map['exes'][key]['name']


def exe_sha(key):
    s = exe_map['exes'][key]['sha256']
    return s.upper() if s else None


def pins_str(v):
    return '/'.join(str(x) for x in v)


rows = []
for n, e in enumerate(ent.E, 1):
    eid = 'R3-%02d' % n
    e['id'] = eid
    e['n'] = n
    e['tag'] = 'gateR3_%02d_%s_vs_r3base' % (n, e['slug'])
    e['cand'] = 'cand_r3_' + e['slug']
    e['okf'] = 'CR_PASS_r3_%s.ok' % e['slug']
    e['srand'] = srands['chosen_srand'][eid]
    e['start'] = srands['openings_start'][eid]
    e['threads'], e['hash'], e['conc'] = (4, 64, 2) if e['smp'] else (1, 16, 8)
    # prebench
    on = None
    on_src = ''
    if e['options']:
        if e['pins_label'] and e['pins_label'] in pins:
            on = pins[e['pins_label']]
            rep = e['pins_on_report']
            if rep:
                on_src = 'measured on the %s probe build, %s; %s the job REPORT' % (
                    PROBE_HEAD, pin_src[e['pins_label']], 'matches' if rep == on else 'DIFFERS FROM')
            else:
                on_src = 'measured on the %s probe build, %s' % (PROBE_HEAD, pin_src[e['pins_label']])
        elif e['exe'] in switch_ids and switch_ids[e['exe']].get('on'):
            sw = switch_ids[e['exe']]
            on = sw['on']
            on_src = 'measured on a %s switch build, sha256 %s…%s' % (
                sw.get('head', PROBE_HEAD), sw.get('exe_sha256', '')[:12],
                ('; matches the job REPORT' if e['pins_on_report'] == on else '; DIFFERS FROM the job REPORT') if e['pins_on_report'] and e['pins_on_report'] != AL1 else '')
        elif e['pins_on_report']:
            on = e['pins_on_report']
            on_src = 'from the job REPORT (not measured here: needs the final exe)'
        else:
            on_src = 'needs the trained net: measure on the final exe with the net before install'
    e['on'] = on
    e['on_src'] = on_src
    if e['slug'] == 'h512':
        e['off_src'] = 'NOT AL1: the H512 exe compiles its own net; fill with its 5 bench pins before install'
    elif e['exe'] in switch_ids and switch_ids[e['exe']].get('off'):
        e['off_src'] = 'AL1 pins, measured on a %s switch build' % switch_ids[e['exe']].get('head', PROBE_HEAD)
        assert switch_ids[e['exe']]['off'] == AL1, e['slug']
    elif e['exe'] in ('stack',):
        e['off_src'] = 'AL1 pins, measured on the %s probe build, identity ALL OK' % PROBE_HEAD
    else:
        e['off_src'] = 'AL1 pins expected (node-exact switch per its REPORT); the runner re-checks'
    rows.append(e)


def manifest_entry(e):
    m = {
        'gate': e['id'], 'tag': e['tag'], 'cand': e['cand'], 'exe': exe_name(e['exe']),
        'sha256': exe_sha(e['exe']) or '<FILL: sha256 of %s>' % exe_name(e['exe']),
        'ok': e['okf'], 'options': e['options'], 'srand': e['srand'], 'runner': 'forge_queue.ps1 v3-6day r7',
        'base_override': {'name': BASE_NAME, 'exe': exe_name('base'),
                          'sha256': exe_sha('base') or '<FILL: sha256 of forge_r3_base.exe>', 'options': []},
        'openings_start': e['start'], 'prebench_depths': [11, 13, 16, 20, 22],
        'prebench': {'cand_off': AL1},
        'longer_tc_confirm_if_h1': bool(e['longer_tc']), 'watch_time': True,
        'sprt': {'elo0': 0, 'elo1': 5, 'nonreg': False}, 'confirm_first': True, 'concurrency': e['conc'],
    }
    if e['slug'] == 'h512':
        m['prebench']['cand_off'] = '<FILL: 5 bench pins of forge_r3_h512.exe (its own net)>'
    if e['options']:
        m['prebench']['cand_on'] = e['on'] if e['on'] else '<FILL: 5 ON pins measured with the trained net>'
    if e['early_stop']:
        m['early_stop'] = EARLY
    if e['tier'] in ('A', 'D') or e['slug'] == 'nnueint16':
        m['nps'] = True
    if e['smp']:
        m['threads'] = e['threads']
        m['hash'] = e['hash']
        m['status'] = 'HELD_NEEDS_RUNNER_THREADS: r7 hard-codes Threads=1/Hash=16 (Build-Args, Static-ArgCheck, Void-Check); this gate needs Threads=4 Hash=64 on both sides'
    if e['status'] == 'blocked-net':
        m['status'] = 'HELD_NEEDS_TRAINED_NET: no trained net exists; fill NNUEFile/exe, cand_on pins and sha256 first'
    if e['status'] == 'held-crew':
        m['status'] = 'HELD_NEEDS_CREW_VOTE: CR policy (S-A2 REPORT) says H256 nets are float-only; remove this status after a crew vote'
    if e['slug'] == 'histrework3':
        m['run_if'] = {'gate_tag': [x for x in rows if x['slug'] == 'histrework2'][0]['tag'], 'min_elo': 0}
    if e.get('tc'):
        m['tc'] = e['tc']
    m['notes'] = ('R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of '
                  'opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: %s.' % e['job'])
    m['driver_note'] = ('%s vs %s (forge_r3_base.exe, no options). %s, SPRT [0,5] normalized a=b=0.05, cap 1500, '
                        'T%d H%d OwnBook false, 8moves_v3 random start %d, srand %d, conc %d, watch_time, confirm_first%s.'
                        % (e['feature'], BASE_NAME, e.get('tc') or '10+0.1', e['threads'], e['hash'], e['start'],
                           e['srand'], e['conc'], ', LTC confirm on H1' if e['longer_tc'] else ''))
    return m


def compact_json(obj):
    s = json.dumps(obj, indent=1, ensure_ascii=True)
    s = re.sub(r'\[\s*\n\s*((?:-?\d+,\s*\n\s*)*-?\d+)\s*\n\s*\]', lambda m: '[' + re.sub(r'\s*\n\s*', ' ', m.group(1)) + ']', s)
    s = re.sub(r'\[\s*\n\s*("[^"\n]*"(?:,\s*\n\s*"[^"\n]*")*)\s*\n\s*\]', lambda m: '[' + re.sub(r',\s*\n\s*', ', ', m.group(1)) + ']', s)
    return s


def fc_cmd(e):
    out = GATE_OUT + '\\' + e['tag']
    a = [FC, '-engine', 'name=' + e['cand'], 'cmd=%s\\%s' % (BIN, exe_name(e['exe'])),
         'option.Threads=%d' % e['threads'], 'option.Hash=%d' % e['hash'], 'option.OwnBook=false'] + list(e['options'])
    a += ['-engine', 'name=' + BASE_NAME, 'cmd=%s\\%s' % (BIN, exe_name('base')),
          'option.Threads=%d' % e['threads'], 'option.Hash=%d' % e['hash'], 'option.OwnBook=false']
    a += ['-each', 'tc=%s' % (e.get('tc') or '10+0.1'), 'timemargin=1000', 'proto=uci', '-openings', 'file=' + BOOK,
          'format=pgn', 'order=random', 'start=%d' % e['start'], '-srand', str(e['srand']), '-games', '2', '-repeat',
          '-rounds', '750', '-concurrency', str(e['conc']), '-sprt', 'elo0=0', 'elo1=5', 'alpha=0.05', 'beta=0.05',
          'model=normalized', '-ratinginterval', '10', '-recover', '-event', 'forge_' + e['tag'],
          '-pgnout', 'file=%s\\%s.pgn' % (out, e['tag']), 'timeleft=true',
          '-log', 'file=%s\\engine_io.log' % out, 'level=warn', 'engine=true', 'append=false']
    return ' '.join(a)


STATUS_TXT = {
    'runnable': 'ready for the r7 queue (after exe install + CR ok flag)',
    'conditional': 'ready, conditional (see notes)',
    'needs-runner': 'HELD: needs Threads=4 on both sides (r7 runner change or a manual run)',
    'blocked-net': 'BLOCKED: needs a trained net',
    'held-crew': 'HELD: CR policy (H256 nets float-only) needs a crew vote',
}
TIER_TXT = {'A': 'node-exact speed / no search change', 'B': 'tree-changing search/eval (Threads 1)',
            'C': 'SMP only (Threads 4)', 'D': 'trained net needed'}

L = []
P = L.append
sha_ready = all(exe_map['exes'][k]['sha256'] for k in ('base', 'stack', 'nnueo2', 'nozero', 'speedstack', 'ttprefetch', 'lazyacc', 'int16'))
P('# R3-3 Gate proposals for the opus-r3-stack features')
P('')
P('One ready gate entry per feature, ranked, with a new srand each. **Proposals only:** no gate was started, and nothing '
  'was written to the gate queue (`autorestart\\forge_gates.json`), `forge_push`, `F:\\forge_push` or any lock folder. '
  'PC files were read through copies. Expectations are labelled as such; **there is no Elo claim.**')
P('')
P('- **Stack:** the entries were checked on `opus-r3-stack` @ `%s` (probe build of the default recipe, sha256 `893ea34d…`, '
  'identity ALL OK, every runtime option\'s ON pins measured at d11-d22). Final head and exe sha256: section 6%s.'
  % (PROBE_HEAD, '' if sha_ready else ' (**pending: filled when the main session reports the final exes**)'))
P('- **Shape of every entry:** one change against the all-OFF engine. Candidate = `forge_r3_stack.exe` + one runtime '
  'option, or `forge_r3_<switch>.exe` (+ that switch\'s own option where it has one). Opponent = `forge_r3_base.exe` '
  '(the same default build) without options, named `%s`.' % BASE_NAME)
P('- **Files:** this document; `GATE_ENTRIES.json` (the same %d manifest objects, ready to append by the owner); '
  '`SRAND_CHECK.md` (how the srands were checked).' % len(rows))
P('- Machine exclusive: no (pins and scans ran at nice 19 next to a conc-8 gate, NNUE training and self-play).')
P('')
P('## 1. Settings shared by every entry (from the live runner, read-only copy)')
P('')
P('| setting | value | source |')
P('|---|---|---|')
P('| runner | `forge_queue.ps1 v3-6day r7` (`C:\\Users\\Administrator\\grok-pc\\forge_push\\autorestart\\forge_queue.ps1`, copy sha256 `%s`) | runner header |' % sha(os.path.join(W, 'pc_copies', 'forge_queue.ps1'))[:16])
P('| fastchess | 1.8.2, `%s` | runner `$FC` |' % FC)
P('| time control | `tc=10+0.1 timemargin=1000` on both engines (entries may set a per-gate `tc`; none does) | Build-Args, `6_gate/GATE_RULES.md` |')
P('| engines | `option.Threads=1 option.Hash=16 option.OwnBook=false` on both sides; SMP entries R3-21..23: `Threads=4 Hash=64` on both sides | Build-Args (hard-coded), O1 / O1-LTT REPORTs |')
P('| openings | `%s` (sha256 `5835239F…`, 34,700 openings) `format=pgn order=random start=<entry>`; starts 390001 + 3000·(n−1) (live manifest max 366001; 369001-387001 left for automatic confirm gates) | runner `$BOOK`, manifest convention (+3000 per gate) |' % BOOK)
P('| games | `-games 2 -repeat -rounds 750`: **cap 1500 games** = 750 colour-reversed pairs, pentanomial | runner `$ROUNDS` |')
P('| SPRT | `-sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized` (manifest `"sprt": {"elo0": 0, "elo1": 5, "nonreg": false}`); LLR bounds ±2.94 | user spec; PC alpha/beta/model |')
P('| concurrency | 8, as G122-G125 and G28-G47 (SMP entries: 2, i.e. 2 games × 4 threads = the same 8 busy threads) | manifest |')
P('| priority / CPUs | BelowNormal, affinity `0xFFF0` (CPUs 4-15; CPUs 0-3 belong to the NNUE trainer) | runner `$AFF` |')
P('| output | `F:\\forge_push\\<tag>\\` (new gate folders since 2026-10-27): `<tag>.pgn`, `<tag>.log`, `engine_io.log`, `RESULT.md`, `RUN_INFO.json` | runner `$DNEW` |')
P('| other args | `-ratinginterval 10 -recover -event forge_<tag> -pgnout file=…\\<tag>.pgn timeleft=true -log file=…\\engine_io.log level=warn engine=true append=false` | Build-Args |')
P('| exes | the runner only starts `%s\\<exe>` and checks its sha256 (Preflight). The main session builds them in `%s\\`; **the owner copies them to `bin\\`** (not done here) | Preflight |' % (BIN, EXE_SRC))
P('| runner checks | pre-gate bench d11/13/16/20/22: cand OFF must equal `prebench.cand_off`, cand ON `prebench.cand_on`; `uci` must advertise each option; static arg check (base exactly Threads/Hash/OwnBook, candidate those plus exactly the entry\'s options); `engine_io.log` setoption check after game 1, game 10 and at the end (VOID rule) | Run-Gate, Static-ArgCheck, Void-Check |')
P('| ok flag | each entry waits for `C:\\Users\\Administrator\\grok-pc\\forge_push\\CR_PASS_r3_<slug>.ok` (Code Review writes it); without it the runner holds the gate | Gate-Status |')
P('| held entries | SMP, blocked-net and pending-merge entries carry `"status": "HELD_…"`, so the runner holds them even if appended unchanged | Gate-Status (`^HELD`) |')
P('| confirm | `confirm_first: true`: an H1 queues one confirm gate right after (fresh srand and openings, cap 1500); with `longer_tc_confirm_if_h1: true` the confirm runs at the runner\'s `$LONG_TC` = 60+0.6 | H1-Confirm |')
P('| early stop | net entries only (crew rule): first block ≥ 750 games with Elo < −8 and LLR < −1.5 → H0-early | EarlyStop-Eval |')
P('')
P('## 2. What happens at the cap, and what 1500 games at [0,5] can decide')
P('')
P('- **At the cap:** after 1500 games with the LLR inside (−2.94, +2.94) the runner writes the verdict "Cap with no '
  'decision (LLR … inside (−2.94, 2.94)); nothing claimed", queues nothing and moves to the next gate. The Elo ± in '
  'RESULT.md is information only (GATE_RULES.md wording: "cap with no decision"). Results are never pooled; a re-run is a new gate with a new srand.')
mb = model['bounds']
P('- **Approx model (not fastchess figures):** normal approximation of the normalized GSPRT, checked after every pair, '
  '%d simulated runs per true value (`tools/sprt_cap_model.py`, seed %d). fastchess uses the exact constrained-MLE GSPRT, '
  'which differs by up to about 0.1 LLR near H1 stops (forge-gate-stats skill).' % (model['paths'], model['seed']))
r = model['ledger_nelo_per_elo']
P('- **Units:** the bounds are in normalized Elo (nElo). On this PC\'s draw-heavy gates nElo ≈ %.1f × Elo (median of %d '
  'ledger rows with |Elo| ≥ 3, range %.1f-%.1f; e.g. G125: Elo 6.02, nElo 11.85).' % (r['median'], r['n_rows_abs_elo_ge_3'], r['min'], r['max']))
P('')
P('| true nElo | [0,5]: P(H1) | P(H0) | P(cap) | mean games | [0,10]: P(H1) | P(H0) | P(cap) |')
P('|---:|---:|---:|---:|---:|---:|---:|---:|')
for a, b in zip(mb['[0,5]']['rows'], mb['[0,10]']['rows']):
    P('| %+d | %.3f | %.3f | %.3f | %d | %.3f | %.3f | %.3f |' % (a['theta_nelo'], a['P_H1'], a['P_H0'], a['P_cap'], a['mean_games'], b['P_H1'], b['P_H0'], b['P_cap']))
P('')
import csv as _csv
_cnt = {'opt': {}, 'all': {}}
for _r in _csv.DictReader(open(os.path.join(W, 'pc_copies', 'FORGE_RESULTS.csv'), encoding='utf-8-sig')):
    _v = _r.get('verdict', '')
    _k = ('H1' if 'H1 accepted' in _v else 'H0-early' if 'H0-early' in _v else 'H0' if 'H0 accepted' in _v
          else 'cap' if 'Cap with no decision' in _v else 'non-regression H1' if 'NON-REGRESSION' in _v else 'other')
    _cnt['all'][_k] = _cnt['all'].get(_k, 0) + 1
    if (_r.get('cand_options') or '').strip():
        _cnt['opt'][_k] = _cnt['opt'].get(_k, 0) + 1
_fmt = lambda c: ', '.join('%s %d' % kv for kv in sorted(c.items(), key=lambda kv: -kv[1]))
P('- To end with H1 **at** the cap, [0,5] needs an observed score of about **%+.0f nElo** (H0: %+.0f); [0,10] needs %+.0f (H0: %+.0f). '
  'With [0,5] the LLR moves about half as fast as with [0,10] for the same data.'
  % (mb['[0,5]']['observed_nelo_needed_at_cap_for_H1'], mb['[0,5]']['for_H0'], mb['[0,10]']['observed_nelo_needed_at_cap_for_H1'], mb['[0,10]']['for_H0']))
P('- PC ledger (FORGE_RESULTS.csv copy, %d rows, mostly [0,10]): option gates (candidate options set) ended %s; all gates %s.'
  % (sum(_cnt['all'].values()), _fmt(_cnt['opt']), _fmt(_cnt['all'])))
_r5 = {r_['theta_nelo']: r_ for r_ in mb['[0,5]']['rows']}
_r10 = {r_['theta_nelo']: r_ for r_ in mb['[0,10]']['rows']}
P('- **Regressions:** a true −20 nElo (about −%.0f Elo here) ends H0 in %.1f%% of [0,5] runs but %.0f%% of [0,10] runs '
  '(approx model): with [0,5]/1500 the SPRT gives almost no early warning of a small regression, so read the final '
  'Elo ± of every capped run (RESULT.md) before acting on it.'
  % (20 / r['median'], 100 * _r5[-20]['P_H0'], 100 * _r10[-20]['P_H0']))
P('- **Expectation (approx model):** for the effect sizes these features can plausibly have (node-exact speed-ups of '
  '0-4%, small search changes), almost every entry is expected to end "cap with no decision"; only a large gain or '
  'loss decides. The crew held a [0,5] gate for this reason (manifest entry e32c: "needs a driver with per-gate cap_games", '
  'r7 hard-codes the 1500 cap). The owner keeps the user\'s [0,5]/1500 spec or changes it (section 7).')
P('- On an H1 the runner\'s verdict text is hard-coded "H1 accepted (SPRT [0,10] normalized, …)"; the settings line '
  'and the LLR line of RESULT.md show the real [0,5] bounds.')
P('')
P('## 3. Ranking and recommended run order')
P('')
P('Ranked by expected gain against risk (expectations, not measurements). Tiers: **A** node-exact speed or no search '
  'change (small but safe), **B** tree-changing search/eval (uncertain), **C** SMP-only (needs Threads 4 on both sides), '
  '**D** needs a trained net (blocked). The run order is the ID order; IDs 01-20 can run in the r7 queue as they are '
  '(R3-15 conditional, R3-20 held), 21-23 need the runner change, 24-29 need nets.')
P('')
P('| rank / ID | feature | tier | expected gain (expectation) | risk | status | reason |')
P('|---|---|---|---|---|---|---|')
for e in rows:
    P('| %s | %s | %s | %s | %s | %s | %s |' % (e['id'], e['feature'], e['tier'], e['gain'], e['risk'], STATUS_TXT[e['status']], e['reason']))
P('')
P('**Run order notes.**')
P('- R3-01/R3-02 first: the two largest node-exact speed-ups, zero search risk; a regression there would point at a build problem.')
P('- R3-03..R3-09: the tree-changing features with the best prior evidence, the C2 correction keys first (each bit separately, as C2 asks).')
P('- R3-10 FORGE_SPEEDSTACK contains R3-16 (MaterialKeyTable, compile-time form) and R3-17 (child TT prefetch): run R3-16/17 only if the owner wants the runtime forms gated too.')
P('- R3-15 runs only if R3-08 ends with Elo ≥ 0 (`run_if`), R3-19 is last per the A1 plan, R3-20 waits for a crew vote (CR policy).')
P('- R3-13 (HardDeadline) needs a candidate built from a head that contains the R3-1 fix 5792074a.')
P('- R3-21..23 (SMP) wait for runner support; R3-24..29 wait for trained nets (order inside D = expected value: king buckets first, threats/pure/H512 last).')
P('')
P('## 4. Entries')
for e in rows:
    m = manifest_entry(e)
    P('')
    P('### %s · %s' % (e['id'], e['feature']))
    P('')
    P('| field | value |')
    P('|---|---|')
    P('| status | %s; tier %s, %s |' % (STATUS_TXT[e['status']], e['tier'], TIER_TXT[e['tier']]))
    shs = exe_sha(e['exe'])
    P('| candidate | `%s` = `%s\\%s` → install as `%s\\%s`; sha256 `%s`; build: %s |' % (
        e['cand'], EXE_SRC, exe_name(e['exe']), BIN, exe_name(e['exe']), shs or 'FILL (main session)', ent.EXES[e['exe']][1]))
    P('| opponent | `%s` = `%s` (no options); sha256 `%s` |' % (BASE_NAME, exe_name('base'), exe_sha('base') or 'FILL (main session)'))
    P('| UCI option(s), candidate only | %s |' % (' '.join('`%s`' % o for o in e['options']) if e['options'] else 'none (the build switch is the change)'))
    P('| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |')
    P('| TC / engines | `%s timemargin=1000`; Threads=%d Hash=%d OwnBook=false on both sides |' % (e.get('tc') or '10+0.1', e['threads'], e['hash']))
    P('| book / concurrency | 8moves_v3.pgn `order=random start=%d`; concurrency %d |' % (e['start'], e['conc']))
    P('| srand | **%d** (new; checked in SRAND_CHECK.md)%s |' % (e['srand'], ('; test-plan row %s' % e['test_plan']) if e['test_plan'] else ''))
    P('| tag / ok flag | `%s` / `%s` |' % (e['tag'], e['okf']))
    P('| prebench cand_off | %s (%s) |' % ('FILL' if e['slug'] == 'h512' else pins_str(AL1), e['off_src']))
    if e['options']:
        P('| prebench cand_on | %s (%s) |' % (pins_str(e['on']) if e['on'] else 'FILL', e['on_src']))
    P('| confirm | %s |' % ('H1 → confirm right after at 60+0.6 (`longer_tc_confirm_if_h1`)' if e['longer_tc'] else 'H1 → confirm right after at 10+0.1'))
    P('| expectation (not a claim) | gain: %s; risk: %s; at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |' % (e['gain'], e['risk']))
    P('')
    P('Evidence (%s):' % e['job'])
    for f in e['facts']:
        P('- ' + f)
    for nt in e['notes']:
        P('- Note: ' + nt)
    if e['smp']:
        P('- Note: the r7 runner cannot run this entry as is: Build-Args, Static-ArgCheck and Void-Check hard-code '
          'Threads=1/Hash=16 for both engines (a Threads=4 option on the candidate alone would be VOID and would not be '
          'the SMP test). It needs a per-gate threads/hash field in the runner (owner/CR decision) or a manual run of '
          'the command below while the queue is idle (the runner launches nothing while any fastchess.exe is alive). '
          'At concurrency 2 a 1500-game gate needs about 4 times the slot time of a conc-8 gate (r7 budgets 2.75 h per '
          'gate, so roughly 11 h).')
    if e['status'] == 'blocked-net':
        P('- Note: replace `<…NET.fnn2>` by the absolute path of the trained net (no spaces, readable by the engine) and '
          'fill `cand_on` with its 5 bench pins; the engine exits with status 2 if the net and options do not match '
          '(fail-loud rule), so a wrong path shows up as a start-up failure, never as a lock-vs-lock match.')
    P('')
    P('Manifest entry (append-ready; the owner adds it, not this job):')
    P('')
    P('```json')
    P(compact_json(m))
    P('```')
    P('')
    P('fastchess command as the r7 Build-Args would build it (%s):' % (
        'started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`'
        if not e['smp'] else 'runner change or manual run; same priority/affinity/output conventions'))
    P('')
    P('```')
    P(fc_cmd(e))
    P('```')
P('')
P('## 5. Not gated')
P('')
P('| item | why no gate |')
P('|---|---|')
for a, b in ent.NO_GATE:
    P('| %s | %s |' % (a, b))
P('')
P('## 6. Exes (built by the main session from the final opus-r3-stack head)')
P('')
P('Final head: `%s`.' % (head or 'FILL (main session)'))
P('')
P('| key | file in %s | build | sha256 | entries |' % EXE_SRC)
P('|---|---|---|---|---|')
for k, (nm, how) in ent.EXES.items():
    used = [e['id'] for e in rows if e['exe'] == k] + (['all (opponent)'] if k == 'base' else [])
    P('| %s | `%s` | %s | `%s` | %s |' % (k, exe_map['exes'][k]['name'], how, exe_sha(k) or 'FILL', ', '.join(used) or '-'))
P('')
P('Before install, per exe: identity (bench d11-d22, perft5, kiwipete) for the default and node-exact switch builds, '
  'and the ON pins of each entry; the runner repeats the bench before every gate and aborts on any mismatch.')
P('')
P('## 7. Owner decisions (noted, not applied)')
P('')
P('1. **[0,5] with a 1500 cap decides only large effects** (section 2). Options: keep it (most entries end "cap with no '
  'decision", the Elo ± is still useful), raise the cap (r7 hard-codes 1500; e32c precedent), or use the PC\'s usual '
  '[0,10]. `6_gate/GATE_RULES.md` specifies a non-regression SPRT [−3,1] for node-identical speed changes (R3-01, 02, 10, '
  '13, 16, 17, 18; S29 and S11 proposed the same).')
P('2. **SMP entries** need Threads=4/Hash=64 on both sides: a runner change or manual runs (R3-21..23 notes).')
P('3. **Confirm TC:** `longer_tc_confirm_if_h1` makes the r7 confirm 60+0.6 (`$LONG_TC`); the test plan asks for 40+0.4 '
  'after an H1 of an EVAL change. O8 (CorrExt) and O6 (threats) want 40+0.4 as the primary gate: set `"tc": "40+0.4"` on '
  'R3-14/R3-27 if that rule should apply.')
P('4. **Runner blind spot for node-exact options:** the "option did not apply" test compares ON pins with the h256_e12 '
  'numbers (`$LOCKBENCH` 308972/…), not AL1; for options whose ON pins equal AL1 (R3-12, 13, 16, 17, 18, 21-23) it cannot '
  'fire. The setoption/advertise VOID check still runs, and LocklessTT, TtChildPrefetch and NnueLazyAcc print an '
  '"info string … active" line into engine_io.log.')
P('5. **Srand bookkeeping:** `common_autonomy.ps1` Used-Srands reads RUN_INFO only under `D:\\grok-pc-data\\forge_push`; '
  'gate folders made since 2026-10-27 are on `F:\\forge_push`, so retry srands recorded there are outside its set '
  '(SRAND_CHECK.md). The test-plan srands of these features (G-B1 …) were not reused, because the user asked for new ones.')
P('6. **Opponent:** every entry uses `forge_r3_base.exe` (OFF stack build), not the AL1 lock exe. The stack\'s default '
  'build is node-identical to AL1 but carries the OFF-path costs of the merged runtime options (e.g. A1 about 1% on a '
  'quiet runner), which both sides share here; a gate against the AL1 exe would include them.')
P('')
P('## 8. Provenance')
P('')
P('- Read-only copies (in `F:\\opus_scratch\\r3\\R3-3\\pc_copies\\`):')
for fn in sorted(os.listdir(os.path.join(W, 'pc_copies'))):
    P('  - `%s` sha256 `%s`' % (fn, sha(os.path.join(W, 'pc_copies', fn))))
P('- Job REPORTs: `opus_round1/<JOB>/REPORT.md` on opus-r3-stack (O1, O1-LTT, O2, O4-O8, C1-C6, sol_A1, sol_S11, sol_S13, '
  'sol_S14, sol_S29, sol_S41, sol_SIT), `opus_round1/sol_S12|sol_SA2|sol_SA4/REPORT.md` on their branches; '
  'R3-1 cross-checks `opus_r3/R3-1/logs/` @ 2047348a.')
P('- Tools: `opus_r3/R3-3/tools/` (`srand_scan.py`, `make_cands.py`, `choose_srands.py`, `measure_pins.py`, '
  '`run_pins.sh`, `sprt_cap_model.py`, `entries.py`, `render.py`, `summarize_scan.py`, `dump_manifest.py`, `show_entries.py`).')
md = '\n'.join(L) + '\n'

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, 'GATE_PROPOSALS.md'), 'w', newline='\n', encoding='utf-8') as fh:
    fh.write(md)
with open(os.path.join(OUT, 'GATE_ENTRIES.json'), 'w', newline='\n', encoding='utf-8') as fh:
    fh.write(compact_json([manifest_entry(e) for e in rows]) + '\n')
# tag substring check (runner matches tags inside fastchess command lines)
tags = [e['tag'] for e in rows]
for t in tags:
    assert sum(1 for u in tags if t in u) == 1, t
print('rendered', len(rows), 'entries; md lines', len(L))
