"""Original S48 advisory provenance guard. No gate changes or ranking authority.

Missing metadata is unknown, including two equally missing fields. This bounded
guard checks only named fields; it does not authenticate a binary, book or run.
"""
from __future__ import annotations
import json
import math
import re

REQUIRED = ('concurrency', 'tc', 'book_sha256', 'opponent_exe_sha256', 'core_mask')
OPTIONAL = ('threads', 'hash_mb', 'engine_options')


def _normalize(field, value):
    if field in ('concurrency', 'threads', 'hash_mb'):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError('positive integer required')
        return value
    if field == 'tc':
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            raise ValueError('nonempty exact recorded time control required')
        return value
    if field.endswith('_sha256'):
        if not isinstance(value, str) or not re.fullmatch(r'[0-9a-fA-F]{64}',value):
            raise ValueError('full64 hexadecimal SHA256 required')
        return value.lower()
    if field == 'core_mask':
        if (not isinstance(value,list) or not value or
            any(isinstance(x,bool) or not isinstance(x,int) or x<0 for x in value) or
            len(value)!=len(set(value))):
            raise ValueError('nonempty unique logical-CPU integer list required; no inferred mask syntax')
        return sorted(value)
    if field == 'engine_options':
        if not isinstance(value,dict) or any(not isinstance(k,str) or not k for k in value):
            raise ValueError('exact recorded option-name map required')
        # Canonical JSON preserves distinctions such as boolean true vs integer1.
        return json.dumps(value,sort_keys=True,allow_nan=False,separators=(',',':'))
    raise ValueError('unsupported comparison field')


def comparability(left, right):
    """Return mismatches/unknowns without pooling rows or modifying inputs."""
    if not isinstance(left,dict) or not isinstance(right,dict):
        raise ValueError('each gate must be a metadata object')
    unknown, mismatches, checked = [], [], []
    for field in REQUIRED+tuple(f for f in OPTIONAL if f in left or f in right):
        values={}
        for side,gate in (('left',left),('right',right)):
            try:
                if field not in gate or gate[field] is None:
                    raise ValueError('missing recorded value')
                values[side]=_normalize(field,gate[field])
            except (ValueError,TypeError,OverflowError) as exc:
                unknown.append({'field':field,'side':side,'reason':str(exc)})
        if len(values)==2:
            checked.append(field)
            if values['left']!=values['right']:
                mismatches.append({'field':field,'left':values['left'],'right':values['right']})
    return {'schema':'forge_sol_S48_comparability_v1','left_gate':left.get('gate'),
            'right_gate':right.get('gate'),'can_compare':not unknown and not mismatches,
            'checked_fields':checked,'mismatches':mismatches,'unknown':unknown,
            'advice_only':True,'acceptance_authorized':False,
            'scope':'Only declared metadata fields are compared. Source/build, settings, runner integrity and evidence authenticity still require independent audit.'}


def selection_bias(samples, true_elo, *, outcome='H1', observed_elo=None):
    """Conditional model bias; MC uncertainty is not a gate confidence interval.

    A cap/no-decision sample must be conditioned on ``cap``, not on H1 winners.
    Non-finite selected Elo estimates block the mean; none are silently dropped.
    The assumed true Elo is an input to a sensitivity calculation, not known truth.
    """
    if isinstance(true_elo,bool) or not isinstance(true_elo,(int,float)) or not math.isfinite(true_elo):
        raise ValueError('assumed true logistic Elo must be finite')
    if observed_elo is not None and (isinstance(observed_elo,bool) or not isinstance(observed_elo,(int,float)) or not math.isfinite(observed_elo)):
        raise ValueError('observed Elo must be finite when supplied')
    if outcome not in ('H1','H0','cap') or not isinstance(samples,dict):
        raise ValueError('explicit H1/H0/cap selection and sample object required')
    outcomes=samples.get('outcome',[]);elos=samples.get('terminal_elo',[])
    if len(outcomes)!=len(elos) or any(x not in ('H1','H0','cap') for x in outcomes):
        raise ValueError('outcome and terminal Elo arrays must have equal length and valid categories')
    selected=[float(elo) for label,elo in zip(outcomes,elos) if label==outcome]
    nonfinite=sum(not math.isfinite(x) for x in selected)
    n=len(selected)
    result={'schema':'forge_sol_S48_selection_bias_v1','status':'MODELED_DIAGNOSTIC',
            'selection':outcome,'assumed_true_logistic_elo':float(true_elo),
            'observed_elo':observed_elo,'total_replicates':len(outcomes),'selected_replicates':n,
            'nonfinite_selected':nonfinite,'conditional_mean_elo':None,'bias_estimate':None,
            'bias_mc_standard_error':None,'bias_mc_ci95':None,
            'adjusted_elo_assuming_model':None,'adjusted_elo_mc_ci95':None,
            'corrected_observation_ci95':None,'advice_only':True,'acceptance_authorized':False,
            'limitations':['Conditional bias depends on the assumed true Elo and pair model.',
                          'MC interval measures simulation error, not observational or post-selection uncertainty.',
                          'No corrected gate confidence interval or unbiased strength estimate is established.']}
    if not n:
        result['status']='UNVERIFIED_NO_SELECTED_REPLICATES';return result
    if nonfinite:
        result['status']='UNVERIFIED_NONFINITE_SELECTED_ESTIMATES';return result
    mean=math.fsum(selected)/n;bias=mean-true_elo
    result.update(conditional_mean_elo=mean,bias_estimate=bias,selected_low_count=n<30)
    if observed_elo is not None:
        result['adjusted_elo_assuming_model']=observed_elo-bias
    if n>1:
        se=math.sqrt(math.fsum((x-mean)**2 for x in selected)/(n-1)/n)
        half=1.959963984540054*se
        result['bias_mc_standard_error']=se
        result['bias_mc_ci95']=[bias-half,bias+half]
        if observed_elo is not None:
            adjusted=result['adjusted_elo_assuming_model']
            result['adjusted_elo_mc_ci95']=[adjusted-half,adjusted+half]
    return result


def simulate_gate_bias(gate, *, profile=None, true_elo=None, runs=20000, seed=2026102648):
    """Model one gate, never borrow a profile from another concurrency.

    ``profile`` has counts and the source concurrency. Missing actual paired data
    produces UNVERIFIED, rather than a fabricated profile from W/D/L or CI.
    """
    if not isinstance(gate,dict):
        raise ValueError('gate metadata object required')
    if profile is None:
        return {'status':'UNVERIFIED_MISSING_PAIRED_PROFILE','gate':gate.get('gate'),
                'adjusted_elo_assuming_model':None,'corrected_observation_ci95':None,
                'acceptance_authorized':False,'reason':'Actual paired counts unavailable; no reconstruction from W/D/L.'}
    concurrency=_normalize('concurrency',gate.get('concurrency'))
    if not isinstance(profile,dict) or profile.get('concurrency')!=concurrency:
        raise ValueError('profile source concurrency differs or is unrecorded; do not pool or borrow')
    counts=profile.get('counts')
    if (not isinstance(counts,list) or len(counts)!=5 or
        any(isinstance(x,bool) or not isinstance(x,int) or x<0 for x in counts) or sum(counts)==0):
        raise ValueError('actual five nonnegative paired-count bins required')
    assumed=gate.get('observed_elo') if true_elo is None else true_elo
    if assumed is None:
        raise ValueError('explicit assumed true Elo or observed point required')
    # Lazy dependency: the provenance guard works with the standard library alone.
    from forge_sol_S33_sprt_planner_20261026 import simulate_cell
    simulated=simulate_cell(counts,assumed,e0=gate.get('e0',0),e1=gate.get('e1',10),
        cap_games=gate.get('cap_games',1500),runs=runs,seed=seed,units='nelo',return_samples=True)
    answer=selection_bias(simulated.pop('samples'),assumed,outcome=gate.get('selection','H1'),
                          observed_elo=gate.get('observed_elo'))
    answer.update(gate=gate.get('gate'),concurrency=concurrency,simulation=simulated,
                  profile_provenance=profile.get('provenance'),
                  assumed_point_source='observed plug-in sensitivity' if true_elo is None else 'caller assumption')
    return answer
