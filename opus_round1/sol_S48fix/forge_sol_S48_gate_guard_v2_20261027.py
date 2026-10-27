"""S48 v2 — gate comparability guard and stopped-Elo (winner's-curse) bias. ADVICE ONLY.

Opus fix-up of Sol's forge_sol_S48_gate_guard_20261026.py (sha256 21713b32..., unchanged, not edited).
No gate, rule, lock or ranking is changed or authorized by anything here.

Fix-ups (SOL_LEFTOVERS_FOR_CLAUDE.md section 3):
  S48-1  simulate_gate_bias() requires explicit e0, e1, cap_games, selection and early_stop in the gate
         (v1 lines 141-143 silently used 0 / 10 / 1500 / 'H1'); missing or invalid values raise ValueError.
  S48-2  comparability() also compares the base (opponent) exe SHA256, the SPRT bounds/model and the cap, and
         records per side the candidate exe SHA256, candidate/base net md5 and the openings seed.
         mode='rank' (two candidates vs one base): candidate identity is reported, a shared openings seed is
         noted. mode='replicate' (confirm of the same candidate): candidate identity must match and the
         openings seed must differ (a confirm needs new openings + seed).
  S48-3  hash_mb accepts 16, '16', '16MB', '16 MB', '16MiB' (and GB/GiB x1024); tc strings are normalized
         ('tc=10+0.1', '10.0+0.10', '0:10+0.1' -> '10+0.1'; '+0' is dropped; moves/ prefix kept).
  S48-4  simulation grids (per-replicate samples) are written only by write_grid(), which refuses any path
         inside a git work tree; only its small manifest (sha256, size, location) belongs in git, the grid
         goes to a GitHub release asset or stays in scratch.
Model labels: every simulated number carries 'model'. 'exact' = fastchess 1.8.2 exact GSPRT (S44
implementation, numpy only); 'approx' = Sol's S33 Gaussian online-LLR planner (needs scipy) and is labelled
'approx model'. Real gate figures are quoted as fastchess printed them (RESULT.md), never recomputed values.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import os
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

SCHEMA_COMPARE = 'forge_sol_S48_comparability_v2'
REQUIRED = ('concurrency', 'tc', 'book_sha256', 'base_exe_sha256', 'core_mask', 'sprt', 'cap_games')
OPTIONAL = ('threads', 'hash_mb', 'engine_options', 'base_net_md5')
IDENTITY = ('cand_exe_sha256', 'cand_net_md5')
SEED = 'openings_seed'
SELECTIONS = ('H1', 'H0', 'cap', 'H0-early')
APPROX_LABEL = 'approx model: S33 Gaussian online-LLR planner (not fastchess exact GSPRT)'


# ----------------------------------------------------------------------------------------------- normalizers
def normalize_hash_mb(value):
    """Positive MB integer from 16, '16', '16MB', '16 MB', '16mb', '16MiB', '1GB' (=1024); else ValueError."""
    if isinstance(value, bool):
        raise ValueError('hash_mb: boolean is not a size')
    if isinstance(value, int):
        if value < 1:
            raise ValueError('hash_mb must be >= 1')
        return value
    if not isinstance(value, str):
        raise ValueError('hash_mb must be an integer or a size string like "64MB"')
    m = re.fullmatch(r'\s*([0-9]+)\s*(MB|MIB|M|GB|GIB|G)?\s*', value.upper())
    if not m:
        raise ValueError('hash_mb string must look like 64, 64MB, 64 MB, 64MiB or 1GB')
    n = int(m.group(1)) * (1024 if (m.group(2) or 'MB').startswith('G') else 1)
    if n < 1:
        raise ValueError('hash_mb must be >= 1')
    return n


def _dec(text):
    try:
        d = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError('tc: not a number: ' + repr(text)) from exc
    if not d.is_finite() or d < 0:
        raise ValueError('tc: negative or non-finite value')
    return d


def _fmt(d):
    s = format(d.normalize(), 'f')
    return s.rstrip('0').rstrip('.') if '.' in s else s


def normalize_tc(value):
    """Canonical fastchess/cutechess time control '[moves/]seconds[+increment]' (seconds as plain decimals).

    Accepts an optional 'tc=' prefix, 'm:ss' base time, surrounding blanks and redundant zeros; '+0' is dropped.
    Rejects empty strings, units, negative or non-numeric parts and anything else (no guessing).
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError('tc must be a nonempty string')
    t = value.strip()
    if t.lower().startswith('tc='):
        t = t[3:]
    m = re.fullmatch(r'(?:([0-9]+)/)?([0-9]+(?:\.[0-9]+)?|[0-9]+:[0-5][0-9](?:\.[0-9]+)?)(?:\+([0-9]+(?:\.[0-9]+)?))?', t)
    if not m:
        raise ValueError('tc not of the form [moves/]base[+inc]: ' + repr(value))
    moves, base, inc = m.group(1), m.group(2), m.group(3)
    if ':' in base:
        mins, secs = base.split(':')
        base_d = Decimal(int(mins)) * 60 + _dec(secs)
    else:
        base_d = _dec(base)
    if base_d == 0:
        raise ValueError('tc base time must be > 0')
    out = (str(int(moves)) + '/' if moves is not None else '') + _fmt(base_d)
    if inc is not None and _dec(inc) != 0:
        out += '+' + _fmt(_dec(inc))
    if moves is not None and int(moves) < 1:
        raise ValueError('tc moves must be >= 1')
    return out


def normalize_sprt(value):
    if not isinstance(value, dict):
        raise ValueError('sprt must be a dict with elo0, elo1, alpha, beta, model')
    out = {}
    for k in ('elo0', 'elo1', 'alpha', 'beta'):
        v = value.get(k)
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            raise ValueError('sprt.%s must be a finite number' % k)
        out[k] = float(v)
    if not out['elo0'] < out['elo1']:
        raise ValueError('sprt requires elo0 < elo1')
    if not (0 < out['alpha'] < 1 and 0 < out['beta'] < 1):
        raise ValueError('sprt alpha/beta must be in (0,1)')
    model = value.get('model')
    if model not in ('normalized', 'logistic', 'bayesian'):
        raise ValueError('sprt.model must be normalized, logistic or bayesian')
    out['model'] = model
    return out


def normalize_seed(value):
    if not isinstance(value, dict):
        raise ValueError('openings_seed must be a dict with srand and openings_start')
    out = {}
    for k in ('srand', 'openings_start'):
        v = value.get(k)
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise ValueError('openings_seed.%s must be a nonnegative integer' % k)
        out[k] = v
    return out


def _normalize(field, value):
    if field == 'concurrency':
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 8:
            raise ValueError('recorded concurrency must be an integer in 1..8')
        return value
    if field == 'threads':
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError('positive integer required')
        return value
    if field == 'hash_mb':
        return normalize_hash_mb(value)
    if field == 'cap_games':
        if isinstance(value, bool) or not isinstance(value, int) or value < 2 or value % 2:
            raise ValueError('cap_games must be an even integer >= 2')
        return value
    if field == 'tc':
        return normalize_tc(value)
    if field.endswith('_sha256'):
        if not isinstance(value, str) or not re.fullmatch(r'[0-9a-fA-F]{64}', value):
            raise ValueError('full 64-hex SHA256 required')
        return value.lower()
    if field.endswith('_md5'):
        if not isinstance(value, str) or not re.fullmatch(r'[0-9a-fA-F]{32}', value):
            raise ValueError('full 32-hex md5 required')
        return value.lower()
    if field == 'core_mask':
        if (not isinstance(value, list) or not value or
                any(isinstance(x, bool) or not isinstance(x, int) or x < 0 for x in value) or
                len(value) != len(set(value))):
            raise ValueError('nonempty unique logical-CPU integer list required; no inferred mask syntax')
        return sorted(value)
    if field == 'engine_options':
        if not isinstance(value, dict) or any(not isinstance(k, str) or not k for k in value):
            raise ValueError('exact recorded option-name map required')
        return json.dumps(value, sort_keys=True, allow_nan=False, separators=(',', ':'))
    if field == 'sprt':
        return normalize_sprt(value)
    if field == SEED:
        return normalize_seed(value)
    raise ValueError('unsupported comparison field')


def _base_exe(gate):
    """base_exe_sha256, with Sol's v1 name opponent_exe_sha256 accepted; both present must agree."""
    a, b = gate.get('base_exe_sha256'), gate.get('opponent_exe_sha256')
    if a is not None and b is not None and str(a).lower() != str(b).lower():
        raise ValueError('base_exe_sha256 and opponent_exe_sha256 disagree')
    return a if a is not None else b


def _value(gate, field):
    v = _base_exe(gate) if field == 'base_exe_sha256' else gate.get(field)
    if v is None:
        raise ValueError('missing recorded value')
    return _normalize(field, v)


# ----------------------------------------------------------------------------------------------- comparability
def comparability(left, right, *, mode='rank'):
    """Mismatches/unknowns between two gates' metadata; never pools, ranks or mutates inputs.

    can_compare is True only if every REQUIRED field (and every OPTIONAL field present on either side) is
    recorded and equal on both sides, plus the mode rule for candidate identity and openings seed.
    """
    if not isinstance(left, dict) or not isinstance(right, dict):
        raise ValueError('each gate must be a metadata object')
    if mode not in ('rank', 'replicate'):
        raise ValueError("mode must be 'rank' or 'replicate'")
    unknown, mismatches, checked, notes = [], [], [], []
    fields = REQUIRED + tuple(f for f in OPTIONAL if f in left or f in right)
    for field in fields:
        values = {}
        for side, gate in (('left', left), ('right', right)):
            try:
                values[side] = _value(gate, field)
            except (ValueError, TypeError, OverflowError) as exc:
                unknown.append({'field': field, 'side': side, 'reason': str(exc)})
        if len(values) == 2:
            checked.append(field)
            if values['left'] != values['right']:
                mismatches.append({'field': field, 'left': values['left'], 'right': values['right']})
    identity = {}
    for field in IDENTITY + (SEED,):
        row = {}
        for side, gate in (('left', left), ('right', right)):
            try:
                row[side] = _value(gate, field)
            except (ValueError, TypeError, OverflowError) as exc:
                row[side] = None
                row[side + '_reason'] = str(exc)
        row['equal'] = (row['left'] == row['right']) if row['left'] is not None and row['right'] is not None else None
        identity[field] = row
    same_cand = None
    if identity['cand_exe_sha256']['equal'] is not None:
        same_cand = identity['cand_exe_sha256']['equal']
        if identity['cand_net_md5']['equal'] is False:
            same_cand = False
    seed = identity[SEED]
    if mode == 'replicate':
        for field in IDENTITY:
            row = identity[field]
            if row['equal'] is None and field == 'cand_exe_sha256':
                unknown.append({'field': field, 'side': 'both', 'reason': 'replicate needs recorded candidate identity'})
            elif row['equal'] is False:
                mismatches.append({'field': field, 'left': row['left'], 'right': row['right']})
        if seed['equal'] is None:
            unknown.append({'field': SEED, 'side': 'both', 'reason': 'replicate needs both openings seeds recorded'})
        elif seed['equal']:
            mismatches.append({'field': SEED, 'left': seed['left'], 'right': seed['right'],
                               'reason': 'a confirm/replicate must use new openings and a new srand'})
    else:
        if seed['equal']:
            notes.append('same openings seed on both gates (srand reuse; the crew rule asks for a new srand per gate)')
        if same_cand:
            notes.append('same candidate on both gates: use mode="replicate" for a confirm comparison')
    return {'schema': SCHEMA_COMPARE, 'mode': mode, 'left_gate': left.get('gate'), 'right_gate': right.get('gate'),
            'can_compare': not unknown and not mismatches, 'checked_fields': checked, 'mismatches': mismatches,
            'unknown': unknown, 'identity': identity, 'same_candidate': same_cand, 'notes': notes,
            'advice_only': True, 'acceptance_authorized': False,
            'scope': 'Only declared metadata fields are compared. Source/build, runner integrity and evidence '
                     'authenticity still require independent audit. Never pool gates.'}


# ----------------------------------------------------------------------------------------------- selection bias
def selection_bias(samples, true_elo, *, outcome, observed_elo=None):
    """Conditional model bias E[stopped Elo | outcome] - true Elo (Sol's v1 semantics; outcome now required).

    MC uncertainty is simulation error only, not a gate confidence interval. Non-finite selected estimates
    block the mean; none are dropped. Outcomes may include 'H0-early' (queue net early stop, exact model).
    """
    if isinstance(true_elo, bool) or not isinstance(true_elo, (int, float)) or not math.isfinite(true_elo):
        raise ValueError('assumed true logistic Elo must be finite')
    if observed_elo is not None and (isinstance(observed_elo, bool) or not isinstance(observed_elo, (int, float))
                                     or not math.isfinite(observed_elo)):
        raise ValueError('observed Elo must be finite when supplied')
    if outcome not in SELECTIONS or not isinstance(samples, dict):
        raise ValueError('explicit H1/H0/cap/H0-early selection and sample object required')
    outcomes = samples.get('outcome', [])
    elos = samples.get('terminal_elo', [])
    if len(outcomes) != len(elos) or any(x not in SELECTIONS for x in outcomes):
        raise ValueError('outcome and terminal Elo arrays must have equal length and valid categories')
    selected = [float(e) for label, e in zip(outcomes, elos) if label == outcome]
    nonfinite = sum(not math.isfinite(x) for x in selected)
    n = len(selected)
    result = {'schema': 'forge_sol_S48_selection_bias_v2', 'status': 'MODELED_DIAGNOSTIC', 'selection': outcome,
              'assumed_true_logistic_elo': float(true_elo), 'observed_elo': observed_elo,
              'total_replicates': len(outcomes), 'selected_replicates': n,
              'outcome_counts': {k: outcomes.count(k) for k in SELECTIONS},
              'nonfinite_selected': nonfinite, 'conditional_mean_elo': None, 'bias_estimate': None,
              'bias_mc_standard_error': None, 'bias_mc_ci95': None, 'adjusted_elo_assuming_model': None,
              'adjusted_elo_mc_ci95': None, 'corrected_observation_ci95': None, 'advice_only': True,
              'acceptance_authorized': False,
              'limitations': ['Conditional bias depends on the assumed true Elo and the pair model.',
                              'MC interval measures simulation error, not observational or post-selection uncertainty.',
                              'No corrected gate confidence interval or unbiased strength estimate is established.']}
    if not n:
        result['status'] = 'UNVERIFIED_NO_SELECTED_REPLICATES'
        return result
    if nonfinite:
        result['status'] = 'UNVERIFIED_NONFINITE_SELECTED_ESTIMATES'
        return result
    mean = math.fsum(selected) / n
    bias = mean - true_elo
    result.update(conditional_mean_elo=mean, bias_estimate=bias, selected_low_count=n < 30)
    if observed_elo is not None:
        result['adjusted_elo_assuming_model'] = observed_elo - bias
    if n > 1:
        se = math.sqrt(math.fsum((x - mean) ** 2 for x in selected) / (n - 1) / n)
        half = 1.959963984540054 * se
        result['bias_mc_standard_error'] = se
        result['bias_mc_ci95'] = [bias - half, bias + half]
        if observed_elo is not None:
            adj = result['adjusted_elo_assuming_model']
            result['adjusted_elo_mc_ci95'] = [adj - half, adj + half]
    return result


def _required(gate, key):
    if key not in gate or gate[key] is None:
        raise ValueError('gate.%s is required (no silent default)' % key)
    return gate[key]


def gate_rule(gate):
    """Validated stopping rule of a gate dict: e0, e1, cap_games, selection, early_stop (all required keys)."""
    e0, e1 = _required(gate, 'e0'), _required(gate, 'e1')
    for name, v in (('e0', e0), ('e1', e1)):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            raise ValueError('gate.%s must be a finite number' % name)
    if not e0 < e1:
        raise ValueError('gate requires e0 < e1')
    cap = _normalize('cap_games', _required(gate, 'cap_games'))
    selection = _required(gate, 'selection')
    if selection not in SELECTIONS:
        raise ValueError('gate.selection must be one of ' + ', '.join(SELECTIONS))
    if 'early_stop' not in gate:
        raise ValueError('gate.early_stop is required (None = no early stop; no silent default)')
    early = gate['early_stop']
    if early is not None:
        if (not isinstance(early, dict) or any(k not in early for k in ('games', 'elo_max', 'llr_max'))):
            raise ValueError('gate.early_stop must be None or {games, elo_max, llr_max}')
        early = (int(early['games']), float(early['elo_max']), float(early['llr_max']))
    if selection == 'H0-early' and early is None:
        raise ValueError('selection H0-early needs an early_stop rule')
    return float(e0), float(e1), cap, selection, early


def simulate_gate_bias(gate, *, profile=None, true_elo=None, runs=20000, seed=2026102748, model='exact',
                       grid_out=None, allow_git_grid=False):
    """Model one gate's stopped-Elo selection bias; never borrow a profile from another concurrency.

    gate must carry e0, e1, cap_games, selection and early_stop (S48-1). profile = {'counts': [5 ints],
    'concurrency': int, 'provenance': str}. true_elo None means the observed point is used as a plug-in
    sensitivity assumption (labelled). model 'exact' (fastchess GSPRT, numpy) or 'approx' (Sol's S33
    planner, scipy; no early-stop support). grid_out: optional NEW path for the per-replicate samples
    (write_grid; refused inside a git work tree, S48-4).
    """
    if not isinstance(gate, dict):
        raise ValueError('gate metadata object required')
    e0, e1, cap, selection, early = gate_rule(gate)
    if profile is None:
        return {'status': 'UNVERIFIED_MISSING_PAIRED_PROFILE', 'gate': gate.get('gate'),
                'adjusted_elo_assuming_model': None, 'corrected_observation_ci95': None,
                'acceptance_authorized': False, 'reason': 'Actual paired counts unavailable; no reconstruction from W/D/L.'}
    concurrency = _normalize('concurrency', gate.get('concurrency'))
    if not isinstance(profile, dict) or _normalize('concurrency', profile.get('concurrency')) != concurrency:
        raise ValueError('profile source concurrency differs or is unrecorded; do not pool or borrow')
    counts = profile.get('counts')
    if (not isinstance(counts, list) or len(counts) != 5 or
            any(isinstance(x, bool) or not isinstance(x, int) or x < 0 for x in counts) or sum(counts) == 0):
        raise ValueError('actual five nonnegative paired-count bins required')
    assumed = gate.get('observed_elo') if true_elo is None else true_elo
    if assumed is None:
        raise ValueError('explicit assumed true Elo or observed point required')
    if model == 'exact':
        from forge_sol_S48_exact_sprt_v2_20261027 import MODEL_LABEL, simulate_samples
        samples, stats = simulate_samples(counts, e0, e1, cap, early, float(assumed), runs, seed)
        simulation = {'model': MODEL_LABEL, 'runs': runs, 'seed': seed, 'rng': 'numpy.default_rng (PCG64)',
                      'e0': e0, 'e1': e1, 'cap_games': cap, 'early_stop': early, 'exact_llr_stats': stats,
                      'profile': 'gate Ptnml + 0.5 per cell, exponentially tilted to the assumed true Elo'}
    elif model == 'approx':
        if early is not None:
            raise ValueError("model 'approx' (S33 planner) cannot apply an early-stop rule; use model='exact'")
        from forge_sol_S33_sprt_planner_20261026 import simulate_cell  # needs numpy + scipy
        simulated = simulate_cell(counts, float(assumed), e0=e0, e1=e1, cap_games=cap, runs=runs, seed=seed,
                                  units='nelo', return_samples=True)
        raw = simulated.pop('samples')
        samples = {'outcome': [str(x) for x in raw['outcome']], 'games': [int(x) for x in raw['games']],
                   'terminal_elo': [float(x) for x in raw['terminal_elo']]}
        simulation = dict(simulated, model=APPROX_LABEL)
    else:
        raise ValueError("model must be 'exact' or 'approx'")
    answer = selection_bias(samples, float(assumed), outcome=selection, observed_elo=gate.get('observed_elo'))
    answer.update(gate=gate.get('gate'), concurrency=concurrency, simulation=simulation,
                  model=simulation['model'], profile_provenance=profile.get('provenance'),
                  assumed_point_source='observed plug-in sensitivity' if true_elo is None else 'caller assumption')
    if grid_out is not None:
        answer['grid'] = write_grid(grid_out, [dict(gate=gate.get('gate'), assumed_true_elo=float(assumed),
                                                    model=simulation['model'], seed=seed, **samples)],
                                    allow_git=allow_git_grid)
    return answer


# ----------------------------------------------------------------------------------------------- S48-4 grids
def git_work_tree_of(path):
    """The enclosing git work tree root of path (file or directory, existing or not), or None."""
    p = Path(path).resolve()
    for parent in [p, *p.parents]:
        if (parent / '.git').exists():
            return parent
    return None


def write_grid(path, rows, *, allow_git=False):
    """Write simulation rows as deterministic jsonl.gz to a NEW path outside any git work tree.

    Returns a small manifest (path, bytes, sha256, rows) — the only part meant for git. Big grids belong in a
    GitHub release asset or in scratch, never in a commit (QA S48-4). allow_git=True is an explicit override.
    """
    path = Path(path)
    tree = git_work_tree_of(path)
    if tree is not None and not allow_git:
        raise ValueError('simulation grid output is inside the git work tree %s; write it to scratch and attach it '
                         'as a release asset (only the manifest goes into git)' % tree)
    if path.exists() or path.is_symlink():
        raise ValueError('grid output already exists: %s' % path)
    if not path.parent.is_dir():
        raise ValueError('grid output parent directory must exist: %s' % path.parent)
    payload = ''.join(json.dumps(r, sort_keys=True, allow_nan=False, separators=(',', ':')) + '\n' for r in rows)
    with open(path, 'xb') as raw:
        with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0, compresslevel=9) as gz:
            gz.write(payload.encode('utf-8'))
    data = path.read_bytes()
    return {'schema': 'forge_sol_S48_grid_manifest_v2', 'file': path.name, 'location': str(path.resolve()),
            'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'rows': len(rows),
            'in_git': tree is not None, 'policy': 'grid not committed; release asset or scratch only (S48-4)'}


# ----------------------------------------------------------------------------------------------- real gate files
_SETTINGS = re.compile(r'Settings: fastchess ([0-9.]+), (\S+) timemargin=([0-9]+), (.*?), (\S+) order=random '
                       r'start=([0-9]+), srand ([0-9]+), ([0-9]+)-game cap, concurrency ([0-9]+), SPRT (\w+) '
                       r'\[(-?[0-9.]+),(-?[0-9.]+)\] a=b=([0-9.]+)')


def _mask_cpus(affinity):
    """'0xFFF0 (CPUs 4-15)' -> [4..15]; the hex mask and the bracketed range must agree, else None."""
    if not isinstance(affinity, str):
        return None
    m = re.match(r'\s*0x([0-9A-Fa-f]+)\s*(?:\(CPUs ([0-9]+)-([0-9]+)\))?\s*$', affinity)
    if not m:
        return None
    mask = int(m.group(1), 16)
    cpus = [i for i in range(64) if mask >> i & 1]
    if m.group(2) is not None and cpus != list(range(int(m.group(2)), int(m.group(3)) + 1)):
        return None
    return cpus or None


def _argv_options(argv, name):
    """option.K=V pairs of the -engine block whose name=<name> in a fastchess argv string."""
    out = {}
    for block in re.split(r'(?=-engine )', argv or ''):
        if re.search(r'\bname=' + re.escape(name) + r'(\s|$)', block):
            for k, v in re.findall(r'option\.([A-Za-z][A-Za-z0-9 _]*?)=(\S+)', block):
                out[k] = v
    return out


def from_gate_files(result_md, run_info):
    """Gate metadata for comparability()/simulate_gate_bias() from a PC gate's RESULT.md + RUN_INFO.json.

    Concurrency comes from RUN_INFO when recorded, else from the RESULT.md settings line (old RUN_INFO files
    have null). Fields that cannot be read stay absent (= unknown), never guessed.
    """
    text = Path(result_md).read_text(encoding='utf-8-sig')
    info = json.loads(Path(run_info).read_text(encoding='utf-8-sig'))
    m = _SETTINGS.search(text)
    if not m:
        raise ValueError('RESULT.md settings line not recognized: %s' % result_md)
    conc_md = int(m.group(9))
    conc = info.get('concurrency')
    if conc is not None and conc != conc_md:
        raise ValueError('RUN_INFO concurrency %s differs from RESULT.md %s' % (conc, conc_md))
    argv = info.get('argv') or ''
    g = {'gate': info.get('tag'), 'concurrency': conc if conc is not None else conc_md,
         'concurrency_source': 'RUN_INFO' if conc is not None else 'RESULT.md settings line',
         'fastchess': m.group(1), 'timemargin_ms': int(m.group(3)), 'cap_games': int(m.group(8)),
         'openings_seed': {'srand': int(m.group(7)), 'openings_start': int(m.group(6))},
         'book_file': m.group(5)}
    tc_argv = re.search(r'\btc=(\S+)', argv)
    g['tc'] = normalize_tc(tc_argv.group(1) if tc_argv else m.group(2))
    sprt_argv = re.search(r'-sprt elo0=(\S+) elo1=(\S+) alpha=(\S+) beta=(\S+) model=(\S+)', argv)
    if sprt_argv:
        g['sprt'] = {'elo0': float(sprt_argv.group(1)), 'elo1': float(sprt_argv.group(2)),
                     'alpha': float(sprt_argv.group(3)), 'beta': float(sprt_argv.group(4)),
                     'model': sprt_argv.group(5)}
    else:
        ab = float(m.group(13))
        g['sprt'] = {'elo0': float(m.group(11)), 'elo1': float(m.group(12)), 'alpha': ab, 'beta': ab,
                     'model': m.group(10)}
    g['e0'], g['e1'] = g['sprt']['elo0'], g['sprt']['elo1']
    if info.get('cap_games') is not None and info['cap_games'] != g['cap_games']:
        raise ValueError('RUN_INFO cap differs from RESULT.md')
    book = info.get('book')
    if isinstance(book, dict) and book.get('sha256'):
        g['book_sha256'] = str(book['sha256']).lower()
    cand, base = info.get('candidate') or {}, info.get('base') or {}
    if base.get('sha256'):
        g['base_exe_sha256'] = str(base['sha256']).lower()
    if cand.get('sha256'):
        g['cand_exe_sha256'] = str(cand['sha256']).lower()
    g['cand_name'], g['base_name'] = cand.get('name'), base.get('name')
    cpus = _mask_cpus(info.get('affinity'))
    if cpus:
        g['core_mask'] = cpus
    copt, bopt = _argv_options(argv, cand.get('name') or '\x00'), _argv_options(argv, base.get('name') or '\x00')
    if copt or bopt:
        g['engine_options'] = {'candidate': copt, 'base': bopt}
        th = {copt.get('Threads'), bopt.get('Threads')}
        hs = {copt.get('Hash'), bopt.get('Hash')}
        if len(th) == 1 and None not in th:
            g['threads'] = int(th.pop())
        if len(hs) == 1 and None not in hs:
            g['hash_mb'] = normalize_hash_mb(hs.pop())
    es = info.get('early_stop')
    g['early_stop'] = ({'games': es['games'], 'elo_max': es['elo_max'], 'llr_max': es['llr_max']}
                       if isinstance(es, dict) else None)
    g['early_stop_source'] = 'RUN_INFO.early_stop' if 'early_stop' in info else 'absent in RUN_INFO (no early stop)'
    pt = re.search(r'Ptnml\(0-2\): \[([^\]]*)\]\s+complete pairs = ([0-9]+)', text)
    g['ptnml'] = [int(x) for x in pt.group(1).split(',')]
    games = re.search(r'Games: ([0-9]+)\s+W/L/D \(candidate view\): ([0-9]+) / ([0-9]+) / ([0-9]+)', text)
    g['games'] = int(games.group(1))
    e = re.search(r'Elo: (-?[0-9.]+) \+/- ([0-9.]+)\s+nElo: (-?[0-9.]+) \+/- ([0-9.]+)', text)
    g['fastchess_printed'] = {'elo': float(e.group(1)), 'elo_err': float(e.group(2)), 'nelo': float(e.group(3)),
                              'nelo_err': float(e.group(4)),
                              'llr': float(re.search(r'LLR: (-?[0-9.]+)\s+bounds', text).group(1))}
    g['observed_elo'] = g['fastchess_printed']['elo']
    v = re.search(r'\*\*Verdict: ([^*]*)\*\*', text).group(1).strip()
    g['verdict_text'] = v
    g['selection'] = ('H1' if v.startswith('H1 accepted') else 'H0-early' if v.startswith('H0-early')
                      else 'H0' if v.startswith('H0 accepted') else 'cap' if v.lower().startswith('cap') else None)
    g['clean'] = ': CLEAN' in text
    g['sources'] = {'RESULT.md': hashlib.sha256(Path(result_md).read_bytes()).hexdigest(),
                    'RUN_INFO.json': hashlib.sha256(Path(run_info).read_bytes()).hexdigest()}
    return g
