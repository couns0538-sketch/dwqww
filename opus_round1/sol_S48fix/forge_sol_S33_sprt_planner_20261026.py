"""ADVICE: finite-cap paired-score Gaussian SPRT planning, never a gate.

True Elo is logistic Elo: score=1/(1+10**(-Elo/400)). Hypothesis bounds
default to normalized Elo (nElo), matching the supplied QA/S06 convention.
The online empirical-population-variance Gaussian LLR is approximate, not
fastchess's exact arbitrary-profile GSPRT. The analytic result is a continuous
Brownian/delta-method approximation to that same statistic, with finite cap.

Exponential tilting preserves absent bins and pentanomial shape ratios.
Paired counts do not identify individual-game W/D/L or within-pair Pearson
correlation; dependence is modeled, not identified. Draw models assume two independent games
with the stated fixed per-game draw probability. Neither is a measured gain.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import platform
from numbers import Real
from pathlib import Path

import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.special import log_ndtr, logsumexp


DATE = '20261026'
C = 800.0 / math.log(10.0)
SCORES = np.array([0., .25, .5, .75, 1.])
_S06_FILENAME = 'forge_sol_S06_statistics_20261026.py'
_S06_ADJACENT = Path(__file__).resolve().parent / _S06_FILENAME
S06_DEPENDENCY = (_S06_ADJACENT if _S06_ADJACENT.exists()
                  else Path(__file__).resolve().parents[1] / 'S06' / _S06_FILENAME)
S06_DEPENDENCY_SHA256 = '4598c5839519af2ed4680b074669d097b9616dfe7c03c1afb7622b276efecb8a'
if (S06_DEPENDENCY.is_file()
        and hashlib.sha256(S06_DEPENDENCY.read_bytes()).hexdigest() != S06_DEPENDENCY_SHA256):
    raise RuntimeError('S06 dependency SHA256 differs from the frozen original')
PROFILES = {
    'G95': {'counts': [13,128,463,137,9], 'concurrency': 5, 'kind':'measured-pair-profile'},
    'G100r': {'counts': [5,121,458,154,12], 'concurrency': 5, 'kind':'measured-pair-profile'},
    'G119': {'counts': [9,130,435,163,13], 'concurrency': 5, 'kind':'measured-pair-profile'},
    'draw0.4': {'draw_ratio': .4, 'concurrency': None, 'kind':'independent-games-model'},
    'draw0.5': {'draw_ratio': .5, 'concurrency': None, 'kind':'independent-games-model'},
    'draw0.6': {'draw_ratio': .6, 'concurrency': None, 'kind':'independent-games-model'},
}
PROTOCOLS = (
    {'name':'n0_10_c1500','e0':0.,'e1':10.,'cap_games':1500},
    {'name':'n0_10_c2500','e0':0.,'e1':10.,'cap_games':2500},
    {'name':'n0_10_c3000','e0':0.,'e1':10.,'cap_games':3000},
    {'name':'n0_5_c3000','e0':0.,'e1':5.,'cap_games':3000},
    {'name':'n0_5_c4000','e0':0.,'e1':5.,'cap_games':4000},
    {'name':'nm1_4_c1500','e0':-1.,'e1':4.,'cap_games':1500},
    {'name':'nm3_1_c1500','e0':-3.,'e1':1.,'cap_games':1500},
)
# Fixed before any MC inspection; all six remain in a failed report.
VALIDATION_CELLS = (
    {'id':'V1','profile':'G119','true_elo':9.5,'protocol':'n0_10_c1500'},
    {'id':'V2','profile':'G95','true_elo':0.,'protocol':'n0_10_c2500'},
    {'id':'V3','profile':'G100r','true_elo':10.,'protocol':'n0_10_c3000'},
    {'id':'V4','profile':'draw0.4','true_elo':5.,'protocol':'n0_5_c4000'},
    {'id':'V5','profile':'draw0.5','true_elo':0.,'protocol':'nm1_4_c1500'},
    {'id':'V6','profile':'draw0.6','true_elo':-2.5,'protocol':'nm3_1_c1500'},
)
DEFAULT_SEED = 20261026033
VALIDATION_SEED = 202610263300


def _real(value, name):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(float(value)):
        raise ValueError(name + ' must be a finite real number')
    return float(value)


def _integer(value, name, minimum=1):
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value < minimum:
        raise ValueError(name + ' must be an integer >= ' + str(minimum))
    return int(value)


def logistic_score(elo):
    elo = _real(elo, 'true_elo')
    x = elo * math.log(10.) / 400.
    if x < 0:
        y = math.exp(x)
        return y / (1+y)
    return 1 / (1+math.exp(-x))


def _profile(values):
    try:
        if len(values) != 5 or any(isinstance(v, (bool, np.bool_)) for v in values):
            raise ValueError('profile must have five nonnegative finite weights')
        p = np.array([_real(v, 'profile weight') for v in values], dtype=float)
    except (TypeError, OverflowError):
        raise ValueError('profile must have five nonnegative finite weights') from None
    if np.any(p < 0) or not np.any(p > 0):
        raise ValueError('profile must contain positive mass and no negative mass')
    p /= p.max()  # Avoid overflowing the normalization of large finite weights.
    return p / p.sum()


def tilted_profile(profile, true_elo):
    """Exponential tilt to the logistic score; preserve zeros and shape ratios.

    p_i(theta) proportional to p_i exp(theta*x_i). Reject unreachable means
    instead of clipping or silently adding support. Counts need not be pooled
    or reconstructed as individual-game W/D/L.
    """
    p = _profile(profile)
    target = logistic_score(true_elo)
    support = SCORES[p > 0]
    lo, hi = float(support[0]), float(support[-1])
    if target < lo or target > hi:
        raise ValueError('true Elo score is outside the supplied profile support')
    if target == lo or target == hi:
        out = np.zeros(5)
        out[SCORES == target] = 1
        return out
    logp = np.full(5, -np.inf)
    logp[p > 0] = np.log(p[p > 0])
    def at(theta):
        logs = logp + theta*SCORES
        return np.exp(logs-logsumexp(logs))
    bound = 1.
    while float(at(-bound) @ SCORES) > target or float(at(bound) @ SCORES) < target:
        bound *= 2
    theta = brentq(lambda t: float(at(t) @ SCORES)-target, -bound, bound, xtol=1e-13)
    return at(theta)


def draw_profile(draw_ratio, true_elo):
    """Independent two-game pair model with fixed per-game draw probability.

    W=mu-D/2 and L=1-mu-D/2, where mu is logistic true Elo score.
    Convolution of [L,D,W] gives the five pair-score bins. Fixed draws can
    make extreme target means infeasible; those inputs are rejected.
    """
    d, mu = _real(draw_ratio, 'draw_ratio'), logistic_score(true_elo)
    if not 0 <= d <= 1 or mu < d/2 or mu > 1-d/2:
        raise ValueError('draw ratio and true Elo imply infeasible game probabilities')
    w, l = mu-d/2, 1-mu-d/2
    return np.convolve([l,d,w], [l,d,w])


def named_profile(name, true_elo):
    meta = PROFILES[name]
    return (draw_profile(meta['draw_ratio'], true_elo) if 'draw_ratio' in meta
            else tilted_profile(meta['counts'], true_elo))


def llr_from_counts(counts, e0=0., e1=10., units='nelo', alpha=.05, beta=.05):
    """Use the original frozen S06 module explicitly, never claim native exactness."""
    if not S06_DEPENDENCY.is_file():
        raise FileNotFoundError('required S06 dependency: ' + str(S06_DEPENDENCY))
    spec = importlib.util.spec_from_file_location('forge_sol_S06_statistics_20261026', S06_DEPENDENCY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.summarize_pentanomial(counts, e0=e0, e1=e1, units=units, alpha=alpha, beta=beta)['gaussian_llr']


def _protocol(protocol, units='nelo', alpha=.05, beta=.05):
    p = dict(protocol)
    p['e0'], p['e1'] = _real(p.get('e0',0.), 'e0'), _real(p.get('e1',10.), 'e1')
    p['cap_games'] = _integer(p.get('cap_games',1500), 'cap_games', 2)
    p['units'] = p.get('units', units)
    p['alpha'], p['beta'] = _real(p.get('alpha',alpha),'alpha'), _real(p.get('beta',beta),'beta')
    if p['cap_games'] % 2 or p['e0'] >= p['e1'] or p['units'] not in ('nelo','logistic'):
        raise ValueError('require even cap_games, e0 < e1, and nelo or logistic units')
    if not 0 < p['alpha'] < 1 or not 0 < p['beta'] < 1 or p['alpha']+p['beta'] >= 1:
        raise ValueError('alpha/beta must be positive with sum < 1')
    p['lower'] = math.log(p['beta']) - math.log1p(-p['alpha'])
    p['upper'] = math.log1p(-p['beta']) - math.log(p['alpha'])
    return p


def _validate_model_hypotheses(probabilities, protocol):
    variance = float(probabilities @ ((SCORES-float(probabilities @ SCORES))**2))
    if variance == 0:
        return  # Empirical variance is unavailable: both methods return cap.
    if protocol['units'] == 'nelo':
        scale = math.sqrt(2*variance)
        s0 = .5+(protocol['e0']/C)*scale
        s1 = .5+(protocol['e1']/C)*scale
    else:
        s0,s1 = logistic_score(protocol['e0']),logistic_score(protocol['e1'])
    if not (math.isfinite(s0) and math.isfinite(s1) and 0 <= s0 < s1 <= 1):
        raise ValueError('model hypothesis scores must be distinct and within [0,1]')


def _moments(paths):
    n = np.arange(1, paths.shape[1]+1, dtype=float)[None,:]
    total = np.cumsum(paths, axis=1, dtype=np.int64)
    squared = np.cumsum(paths.astype(np.int16)**2, axis=1, dtype=np.int64)
    mean = total / (4*n)
    variance = squared / (16*n) - mean*mean
    return n, mean, variance


def _nelo_statistic(n, mean, variance):
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.where(variance > 0,n*(mean-.5)/np.sqrt(variance),np.nan)


def _moment_llr(n, mean, variance, p, nelo_statistic=None):
    e0, e1 = p['e0'], p['e1']
    with np.errstate(divide='ignore', invalid='ignore'):
        if p['units'] == 'nelo':
            z = _nelo_statistic(n,mean,variance) if nelo_statistic is None else nelo_statistic
            value = (math.sqrt(2)*(e1-e0)/C)*z - ((e1-e0)*(e0+e1)/(C*C))*n
            # Since scores lie in [0,1], variance <= .25. These global
            # bounds guarantee feasible hypotheses without repeated arrays.
            if e0 >= -C/math.sqrt(2) and e1 <= C/math.sqrt(2):
                return value
            scale = np.sqrt(2*variance)
            s0,s1 = .5+(e0/C)*scale,.5+(e1/C)*scale
        else:
            s0,s1 = logistic_score(e0),logistic_score(e1)
            value = n*(s1-s0)*(2*mean-s0-s1)/(2*variance)
        valid = (variance > 0) & (s0 >= 0) & (s1 <= 1) & (s1 > s0)
    return np.where(valid, value, np.nan)


def online_llr(pair_categories, e0=0., e1=10., units='nelo'):
    """LLR at every completed pair; categories 0..4 mean scores 0,.25,..1.

    The first pair and any other zero-variance prefix have unavailable LLR,
    represented as NaN here (never a crossing). Public JSON summaries contain
    no NaNs. This helper is also an exact-model fixture interface.
    """
    paths = np.asarray(pair_categories)
    if (paths.ndim != 2 or paths.shape[1] == 0 or paths.dtype.kind not in 'iu'
            or np.any(paths < 0) or np.any(paths > 4)):
        raise ValueError('pair_categories must be a nonempty 2D integer array in 0..4')
    p = _protocol({'e0':e0,'e1':e1,'cap_games':2*paths.shape[1]}, units)
    return _moment_llr(*_moments(paths), p)


def _wilson(k, n):
    z, q = 1.959963984540054, k/n
    den = 1+z*z/n
    center = (q+z*z/(2*n))/den
    half = z*math.sqrt(q*(1-q)/n+z*z/(4*n*n))/den
    return [max(0.,center-half), min(1.,center+half)]


def _summary(games, outcome, terminal_elo, p, probabilities, true_elo, seed, profile, return_samples):
    runs = len(games)
    result = {
        'advice_only':True, 'exact_fastchess':False,
        'model':'approximate online empirical-variance Gaussian paired-score LLR',
        'true_elo':float(true_elo), 'true_elo_units':'logistic',
        'hypothesis_units':p['units'], 'e0':p['e0'], 'e1':p['e1'],
        'alpha':p['alpha'], 'beta':p['beta'], 'cap_games':p['cap_games'],
        'runs':runs, 'seed':seed, 'rng':'numpy.Generator.PCG64',
        'numpy_version':np.__version__, 'pair_probabilities':profile.tolist(),
        'python_version':platform.python_version(),
        'probabilities':probabilities,
        'probability_standard_error':{k:math.sqrt(v*(1-v)/runs) for k,v in probabilities.items()},
        'probability_wilson95':{k:_wilson(int(np.sum(outcome==k)),runs) for k in probabilities},
        'mean_games':float(np.mean(games)), 'median_games':float(np.median(games)),
        'mean_games_standard_error':float(np.std(games,ddof=1)/math.sqrt(runs)) if runs>1 else None,
        'finite_elo_terminal_count':int(np.isfinite(terminal_elo).sum()),
        'independent_modeled_replicates':True, 'observed_gates_pooled':False,
    }
    if return_samples:
        result['samples'] = {'games':games, 'outcome':outcome, 'terminal_elo':terminal_elo}
    return result


def simulate_protocols(profile, true_elo, protocols, *, runs=20000, seed=DEFAULT_SEED,
                       units='nelo', alpha=.05, beta=.05, return_samples=False, block_size=128):
    """Common modeled paths for alternative protocols, memory O(block*maxcap).

    Sharing random paths reduces contrast noise between protocol choices;
    it never combines gate observations. All crossings are checked after
    every completed pair, including the final pair at the cap. A crossing
    exactly at the cap is H0/H1; only uncrossed paths are classified as cap.
    Samples use string outcomes H1/H0/cap, games int64, terminal_elo float64.
    Terminal Elo at scores 0 or 1 is +/-infinity in optional raw samples;
    summary JSON remains finite. Conditional H1 bias must filter outcome=H1.
    """
    runs, seed = _integer(runs,'runs'), _integer(seed,'seed',0)
    block_size = _integer(block_size,'block_size')
    ps = [_protocol(x,units,alpha,beta) for x in protocols]
    if not ps:
        raise ValueError('at least one protocol is required')
    p = tilted_profile(profile, true_elo)
    for protocol in ps:
        _validate_model_hypotheses(p,protocol)
    max_pairs = max(x['cap_games']//2 for x in ps)
    rng = np.random.default_rng(seed)
    games = [np.empty(runs,dtype=np.int64) for _ in ps]
    outcomes = [np.empty(runs,dtype='<U3') for _ in ps]
    elos = [np.empty(runs,dtype=float) for _ in ps]
    cdf = np.cumsum(p)
    cdf[-1] = 1.
    for start in range(0,runs,block_size):
        stop = min(runs,start+block_size)
        paths = np.searchsorted(cdf,rng.random((stop-start,max_pairs))).astype(np.int8)
        n, mean, variance = _moments(paths)
        nelo_statistic = _nelo_statistic(n,mean,variance) if any(x['units']=='nelo' for x in ps) else None
        # Bounds repeated at several caps share the same LLR computation.
        cache = {}
        for i,protocol in enumerate(ps):
            key = (protocol['e0'],protocol['e1'],protocol['units'])
            if key not in cache:
                cache[key] = _moment_llr(n,mean,variance,protocol,nelo_statistic)
            llr = cache[key][:,:protocol['cap_games']//2]
            hit = (llr <= protocol['lower']) | (llr >= protocol['upper'])
            crossed = hit.any(axis=1)
            index = np.where(crossed,hit.argmax(axis=1),llr.shape[1]-1)
            row = np.arange(stop-start)
            terminal = llr[row,index]
            games[i][start:stop] = 2*(index+1)
            outcomes[i][start:stop] = np.where(crossed,np.where(terminal>=protocol['upper'],'H1','H0'),'cap')
            score = mean[row,index]
            with np.errstate(divide='ignore',invalid='ignore'):
                elos[i][start:stop] = (400/math.log(10))*(np.log(score)-np.log1p(-score))
    results = []
    for i,protocol in enumerate(ps):
        probs = {k:float(np.mean(outcomes[i]==k)) for k in ('H1','H0','cap')}
        result = _summary(games[i],outcomes[i],elos[i],protocol,probs,true_elo,seed,p,return_samples)
        result['common_random_numbers'] = len(ps)>1
        result['protocol_name'] = protocol.get('name')
        result['input_profile_weights'] = [_real(x,'profile weight') for x in profile]
        result['sampling_layout'] = {
            'block_size':block_size,'max_pairs':max_pairs,'order':'row-major, block_runs by max_pairs',
            'protocols':[{k:x[k] for k in ('name','e0','e1','cap_games','units','alpha','beta') if k in x} for x in ps],
        }
        results.append(result)
    return results


def simulate_cell(profile, true_elo, e0=0., e1=10., cap_games=1500, *,
                  runs=20000, seed=DEFAULT_SEED, units='nelo', alpha=.05, beta=.05,
                  return_samples=False, block_size=128):
    return simulate_protocols(profile,true_elo,[{'e0':e0,'e1':e1,'cap_games':cap_games}],
                              runs=runs,seed=seed,units=units,alpha=alpha,beta=beta,
                              return_samples=return_samples,block_size=block_size)[0]


def _lower_cdf(t, drift, variance, x, width):
    if t <= 0:
        return 0.
    sd = math.sqrt(variance*t)
    # Tail images beyond 12 standard deviations are negligible. At specified
    # S33 caps this uses 25 images; long horizons automatically use more.
    images = max(12,int(math.ceil((abs(drift)*t+12*sd)/(2*width)))+2)
    terms = []
    for j in range(-images,images+1):
        a = x+2*j*width
        r = abs(a)
        first = math.exp(drift*(r-x)/variance + float(log_ndtr((-r-drift*t)/sd)))
        second = math.exp(-drift*(r+x)/variance + float(log_ndtr((-r+drift*t)/sd)))
        terms.append(math.copysign(first+second,a))
    return math.fsum(terms)


def brownian_finite_cap(drift, variance, lower, upper, cap_pairs):
    """Absorbing Brownian OC/ASN with image-series first-passage CDFs.

    drift and variance are LLR moments per pair; start at LLR=0. Outcome
    probabilities integrate flux to each absorbing boundary up to the cap.
    Mean=2*integral survival dt; median is capped at the atom at 2*cap_pairs.
    Continuous monitoring omits discrete-pair overshoot and startup effects.
    """
    drift, variance = _real(drift,'drift'), _real(variance,'variance')
    lower, upper, tmax = _real(lower,'lower'), _real(upper,'upper'), _real(cap_pairs,'cap_pairs')
    if variance < 0 or not lower < 0 < upper or tmax <= 0:
        raise ValueError('need nonnegative variance, lower < 0 < upper, and positive cap')
    if variance == 0:
        time = upper/drift if drift>0 else lower/drift if drift<0 else math.inf
        outcome = ('H1' if drift>0 else 'H0') if time <= tmax else 'cap'
        return {'probabilities':{k:float(k==outcome) for k in ('H1','H0','cap')},
                'mean_games':2*min(time,tmax),'median_games':2*min(time,tmax)}
    x, width = -lower, upper-lower
    def probabilities(t):
        h0 = _lower_cdf(t,drift,variance,x,width)
        h1 = _lower_cdf(t,-drift,variance,width-x,width)
        cap = 1-h0-h1
        if min(h0,h1,cap) < -1e-8 or max(h0,h1,cap)>1+1e-8:
            raise ArithmeticError('Brownian image series failed probability checks')
        return {'H1':min(1.,max(0.,h1)),'H0':min(1.,max(0.,h0)),'cap':min(1.,max(0.,cap))}
    final = probabilities(tmax)
    mean = 2*quad(lambda t: probabilities(t)['cap'],0,tmax,epsabs=1e-7,epsrel=1e-9)[0]
    median = tmax if final['cap'] >= .5 else brentq(lambda t:probabilities(t)['cap']-.5,0,tmax)
    return {'probabilities':final,'mean_games':mean,'median_games':2*median}


def analytic_cell(profile, true_elo, e0=0., e1=10., cap_games=1500, *, units='nelo', alpha=.05, beta=.05):
    """Delta-method diffusion of the online empirical-variance LLR.

    nElo LLR=N*[sqrt(2)*Delta*(mean-.5)/(C*sd) - Delta*(e0+e1)/C²].
    The influence function includes the empirical variance's fluctuations;
    unlike a frozen-variance walk, its diffusion also depends on profile
    skew/kurtosis at nonzero true score. This is an asymptotic approximation.
    """
    protocol = _protocol({'e0':e0,'e1':e1,'cap_games':cap_games},units,alpha,beta)
    p = tilted_profile(profile,true_elo)
    _validate_model_hypotheses(p,protocol)
    mu = float(p @ SCORES)
    centered = SCORES-mu
    variance = float(p @ (centered**2))
    if variance <= 0:
        result = {'probabilities':{'H1':0.,'H0':0.,'cap':1.}, 'mean_games':float(cap_games),'median_games':float(cap_games)}
        drift = diffusion = 0.
    else:
        if units == 'nelo':
            h = math.sqrt(2)*(e1-e0)/(C*math.sqrt(variance))
            drift = h*(mu-.5) - (e1-e0)*(e0+e1)/(C*C)
            influence = h*(centered-(mu-.5)*(centered**2-variance)/(2*variance))
        else:
            s0,s1 = logistic_score(e0),logistic_score(e1)
            h = (s1-s0)/variance
            drift = h*(mu-(s0+s1)/2)
            influence = h*centered - drift*(centered**2-variance)/variance
        diffusion = float(p @ (influence**2))
        result = brownian_finite_cap(drift,diffusion,protocol['lower'],protocol['upper'],cap_games/2)
    result.update({'model':'approximate delta-method Brownian OC/ASN, finite cap',
                   'exact_fastchess':False,'advice_only':True,'drift_per_pair':drift,
                   'diffusion_variance_per_pair':diffusion,'true_elo_units':'logistic',
                   'hypothesis_units':units,'pair_variance':variance})
    return result


def grid_cells():
    return [{'profile':name,'true_elo':-5+2.5*i,'protocol':protocol['name']}
            for name in PROFILES for i in range(15) for protocol in PROTOCOLS]


def compare_validation(rows):
    if len(rows) != 6:
        raise ValueError('validation requires all six predeclared cells')
    keys = ('id','profile','true_elo','protocol')
    if any(tuple(row.get(k) for k in keys) != tuple(cell[k] for k in keys)
           for row,cell in zip(rows,VALIDATION_CELLS)):
        raise ValueError('validation identities/order must match all six predeclared cells')
    cells = []
    for row in rows:
        result = dict(row)
        result['absolute_differences'] = {k:abs(row['mc'][k]-row['analytic'][k]) for k in ('H1','H0','cap')}
        result['status'] = 'PASS' if max(result['absolute_differences'].values()) <= .03 else 'FAIL'
        cells.append(result)
    failed = [x['id'] for x in cells if x['status']=='FAIL']
    return {'status':'FAIL' if failed else 'PASS','threshold_absolute_probability':.03,
            'failed_cells':failed,'cells':cells,'posthoc_cell_selection':False}


def run_validation(*, runs=20000, seed=VALIDATION_SEED):
    if runs < 20000:
        raise ValueError('published validation requires >=20000 runs per cell')
    rows = []
    for i,cell in enumerate(VALIDATION_CELLS):
        p = named_profile(cell['profile'],cell['true_elo'])
        proto = next(x for x in PROTOCOLS if x['name']==cell['protocol'])
        kw = {k:proto[k] for k in ('e0','e1','cap_games')}
        mc = simulate_cell(p,cell['true_elo'],runs=runs,seed=seed+i,**kw)
        analytic = analytic_cell(p,cell['true_elo'],**kw)
        rows.append({**cell,'runs':runs,'seed':seed+i,'mc':mc['probabilities'],
                     'analytic':analytic['probabilities'],'mc_mean_games':mc['mean_games'],
                     'analytic_mean_games':analytic['mean_games'],'mc_median_games':mc['median_games'],
                     'analytic_median_games':analytic['median_games'],
                     'mc_wilson95':mc['probability_wilson95']})
    return compare_validation(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--screen',action='store_true',help='bounded performance/model screen only, never acceptance validation')
    parser.add_argument('--validate',action='store_true',help='all six fixed cells, >=20000 runs each')
    parser.add_argument('--full-grid',action='store_true',help='explicitly authorize 630 cells; default never runs this')
    parser.add_argument('--runs',type=int,default=20000)
    parser.add_argument('--seed',type=int,default=DEFAULT_SEED)
    parser.add_argument('--output-dir',type=Path,help='required new directory; existing paths and symlink ancestors are refused')
    args = parser.parse_args(argv)
    if not any((args.screen,args.validate,args.full_grid)):
        parser.print_help()
        return 0
    if args.runs <= 0 or args.seed < 0:
        parser.error('runs must be positive and seed must be nonnegative')
    if args.screen and args.runs>2000:
        parser.error('--screen must explicitly select --runs <=2000')
    if (args.validate or args.full_grid) and args.runs<20000:
        parser.error('--validate and --full-grid require >=20000 runs per cell')
    if args.output_dir is None:
        parser.error('--output-dir must name a new directory')
    destination = args.output_dir.absolute()
    if any(path.is_symlink() for path in (destination,*destination.parents)):
        parser.error('output directory and its parents must not be symlinks')
    try:
        destination.mkdir(parents=True,exist_ok=False)
    except OSError as exc:
        parser.error('cannot create new output directory: '+str(exc))
    args.output_dir = destination
    if args.screen:
        p = named_profile('G119',9.5)
        r = simulate_cell(p,9.5,runs=args.runs,seed=args.seed)
        r['analytic'] = analytic_cell(p,9.5)
        r['screen_only'] = True
        print(json.dumps(r,allow_nan=False,sort_keys=True))
    if args.validate:
        result = run_validation(runs=args.runs,seed=args.seed)
        out = args.output_dir / ('forge_sol_S33_six_cell_validation_'+DATE+'.json')
        try:
            with out.open('x') as f:
                f.write(json.dumps(result,indent=2,allow_nan=False)+'\n')
        except OSError as exc:
            parser.error('cannot create new validation output: '+str(exc))
        print(json.dumps({'validation':result['status'],'path':str(out)}))
    if args.full_grid:
        out = args.output_dir / ('forge_sol_S33_sprt_plan_table_'+DATE+'.csv')
        try:
            output = out.open('x',newline='')
        except OSError as exc:
            parser.error('cannot create new grid output: '+str(exc))
        with output as f:
            writer = csv.DictWriter(f,fieldnames=['profile','concurrency','kind','true_elo_logistic','protocol','hypothesis_units','e0','e1','cap_games','runs','seed','mc_H1','mc_H0','mc_cap','mc_mean_games','mc_median_games','a_H1','a_H0','a_cap','a_mean_games','a_median_games','max_abs_probability_difference'])
            writer.writeheader()
            for pi,name in enumerate(PROFILES):
                for ei in range(15):
                    elo, seed = -5+2.5*ei, args.seed+pi*100000+ei*1009
                    p = named_profile(name,elo)
                    results = simulate_protocols(p,elo,PROTOCOLS,runs=args.runs,seed=seed)
                    for protocol,mc in zip(PROTOCOLS,results):
                        a = analytic_cell(p,elo,**{k:protocol[k] for k in ('e0','e1','cap_games')})
                        row = {'profile':name,'concurrency':PROFILES[name]['concurrency'],'kind':PROFILES[name]['kind'],
                               'true_elo_logistic':elo,'protocol':protocol['name'],'hypothesis_units':'nelo',
                               'e0':protocol['e0'],'e1':protocol['e1'],'cap_games':protocol['cap_games'],
                               'runs':args.runs,'seed':seed,'mc_mean_games':mc['mean_games'],
                               'mc_median_games':mc['median_games'],'a_mean_games':a['mean_games'],
                               'a_median_games':a['median_games'],
                               'max_abs_probability_difference':max(abs(mc['probabilities'][k]-a['probabilities'][k]) for k in ('H1','H0','cap'))}
                        row.update({'mc_'+k:mc['probabilities'][k] for k in ('H1','H0','cap')})
                        row.update({'a_'+k:a['probabilities'][k] for k in ('H1','H0','cap')})
                        writer.writerow(row)
                    f.flush()
                    print(json.dumps({'group_complete':name,'true_elo':elo,'seed':seed}),flush=True)
        print(json.dumps({'full_grid_rows':630,'path':str(out),'advice_only':True}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
