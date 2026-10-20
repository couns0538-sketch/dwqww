"""Frozen preparation gates and byte/mode integrity; no engine execution."""
import hashlib,json,os,re,stat
from pathlib import Path,PurePosixPath
BASELINE='61f598056572dfade6994af8ad2e38817cd28aa3'
CANDIDATE='PENDING_FROZEN_CANDIDATE_20_SHA'
FLAGS='-O3 -DNDEBUG -march=x86-64-v3 -mtune=generic -fno-fast-math -ffp-contract=off -fno-lto'
WORKFLOW='.github/workflows/forge-hosted-pawn-span-performance.yml'
READY='PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH'
REQUIRED_PROOFS=(
 'validation/lazy-runtime-psqt-20261020/root-verification/NATIVE.json',
 'validation/lazy-runtime-psqt-20261020/root-verification/WINDOWS.json',
 'validation/pawn-span-fill-20261020/root-verification/NATIVE.json',
 'validation/pawn-span-fill-20261020/root-verification/WINDOWS.json',
 'validation/pawn-span-fill-native-20261020/ROOT-FROZEN-SOURCE-GATES.json',
 'validation/pawn-span-fill-native-20261020/FINAL-RECEIPT.json',
 'validation/pawn-span-fill-native-20261020/release-parity-wrapper-attempt1/summary.json',
 'validation/pawn-span-fill-20261020/independent-review/SOURCE-CHECK.json',
 'validation/pawn-span-fill-20261020/independent-review/PROBE-RECEIPT.json',
 'validation/pawn-span-fill-20261020/independent-review/public-diff-attempt1/RESULT.json',
 'validation/hosted-pawn-span-performance-20261020/ROOT-PREPARATION-REVIEW.json',
 'validation/hosted-pawn-span-performance-20261020/ROOT-ONE-ATTEMPT-AUTHORIZATION.json',
 'validation/hosted-pawn-span-performance-20261020/independent-review/REVIEW.json',
)

STDIN=b'bench 11\n'*5+b'quit\n'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def safe(root,name):
    if not isinstance(name,str):raise ValueError('Evidence path must be string')
    p=PurePosixPath(name);target=Path(root)/name
    if p.is_absolute() or '..' in p.parts or p.as_posix()!=name or not target.is_file() or target.is_symlink() or not target.resolve().is_relative_to(Path(root).resolve()):raise ValueError('Missing/unsafe evidence '+name)
    return target

def require_ready(cfg):
    fixed={'status':READY,'baseline_sha':BASELINE,'candidate_sha':CANDIDATE,'compiler':'g++-14','release_flags':FLAGS,'attempts':1,'fault_retries':0,
           'bench_depth':11,'expected_nodes':321912,'benches_per_process':5,'excluded_warmup_order':'ABBA','aa_blocks':15,'ab_blocks':31,'bootstrap_seed':20261028,'bootstrap_draws':10000,'sample_timeout_seconds':60,'timing_work_seconds':3600,'build_work_seconds':690,
           'source_gates_status':'PASSED','parity_review_status':'PASSED','capture_review_status':'PASSED','root_review_status':'PASSED','independent_review_status':'PASSED','workflow_status':'FROZEN','operational_qualification_status':'authorized_for_one_fresh_host_calibration_attempt_with_prior_anomalies_unresolved'}
    if any(cfg.get(k)!=v or type(cfg.get(k)) is not type(v) for k,v in fixed.items()):raise ValueError('Protocol remains blocked or differs from frozen design')
    if not cfg.get('correctness_evidence_sha256') or not re.fullmatch('[0-9a-f]{64}',str(cfg.get('workflow_sha256',''))):raise ValueError('Proof/workflow freeze missing')
    if cfg.get('mandatory_finite_proof_paths')!=list(REQUIRED_PROOFS) or not set(REQUIRED_PROOFS).issubset(cfg['correctness_evidence_sha256']):raise ValueError('Full current/native/Windows/parity proof binding missing')
    if set(cfg.get('transport_captures',{}))!={'baseline','candidate'}:raise ValueError('Actual five-command captures pending')

def inventory(repo,package):
    repo=Path(repo).resolve();package=Path(package).resolve();manifest=package/'PACKAGE-SHA256SUMS';rows={};order=[]
    for line in manifest.read_text().splitlines():
        digest,name=line.split('  ',1)
        if not re.fullmatch('[0-9a-f]{64}',digest) or name in rows:raise ValueError('Malformed package inventory')
        path=safe(repo,name);rows[name]=digest;order.append(name)
        if sha(path)!=digest:raise ValueError('Package hash mismatch '+name)
    actual=sorted([p.relative_to(repo).as_posix() for p in package.rglob('*') if p.is_file() and p!=manifest]+[WORKFLOW])
    if order!=actual or any('__pycache__' in Path(n).parts or n.endswith('.pyc') for n in actual):raise ValueError('Package set/order changed')
    return [repo/n for n in order]+[manifest]

def proof_paths(repo,cfg):
    paths=[]
    for name,digest in cfg['correctness_evidence_sha256'].items():
        path=safe(repo,name)
        if not isinstance(digest,str) or not re.fullmatch('[0-9a-f]{64}',digest) or sha(path)!=digest:raise ValueError('Correctness proof changed '+name)
        paths.append(path)
    return paths

def snapshot(paths):
    result={}
    for path in sorted(set(map(Path,paths)),key=lambda p:p.as_posix()):
        if not path.is_file() or path.is_symlink():raise ValueError('Missing/unsafe frozen input '+str(path))
        result[str(path)]={'sha256':sha(path),'mode':stat.S_IMODE(path.stat().st_mode)}
    return result

def rehash(frozen):
    mismatches=[];observed={}
    for name,expected in frozen.items():
        try:observed[name]=snapshot([Path(name)])[name]
        except (ValueError,OSError) as error:observed[name]={'error':repr(error)}
        if observed[name]!=expected:mismatches.append(name)
    return {'status':'failed' if mismatches else 'passed','mismatches':mismatches,'observed':observed}

def transport_paths(repo,cfg,analysis):
    consumed=[]
    for label,commit in [('baseline',BASELINE),('candidate',CANDIDATE)]:
        entry=cfg['transport_captures'][label]
        if entry.get('source_commit')!=commit or not re.fullmatch('[0-9a-f]{64}',str(entry.get('engine_sha256',''))):raise ValueError('Capture source/binary provenance missing')
        paths={key:safe(repo,entry[key+'_path']) for key in ('stdin','stdout','stderr','facts','provenance')}
        if any(entry[key+'_path'] not in cfg['correctness_evidence_sha256'] for key in paths):raise ValueError('Capture originals not bound into correctness proofs')
        if paths['stdin'].read_bytes()!=STDIN or paths['stderr'].read_bytes():raise ValueError('Original five-command transport differs')
        analysis.parse_bench(paths['stdout'].read_bytes())
        facts=json.loads(paths['facts'].read_text())
        provenance=json.loads(paths['provenance'].read_text());capture=provenance.get('captures',{}).get(label,{})
        before=capture.get('binary_sha256_before',{});after=capture.get('binary_sha256_after',{})
        source=capture.get('source_sha256_before',{})
        if (provenance.get('status')!='PASS_BOTH_ACTUAL_FIVE_COMMAND_CAPTURES_NOT_SPEED_EVIDENCE' or
                capture.get('status')!='PASS_ACTUAL_FIVE_CANONICAL_ROWS' or capture.get('rows')!=5 or
                capture.get('source_commit')!=commit or before!=after or set(before)!={'forge','libforge_core.a'} or
                before.get('forge')!=entry['engine_sha256'] or any(not re.fullmatch('[0-9a-f]{64}',str(v)) for v in before.values()) or
                capture.get('process_facts')!=facts or not source or source!=capture.get('source_sha256_after') or
                facts.get('command')!=[capture.get('binary_paths',{}).get('forge')]):raise ValueError('Actual capture label/source/binary/process provenance differs')
        manifest_name=entry['source_manifest_path'];manifest=safe(repo,manifest_name)
        if manifest_name not in cfg['correctness_evidence_sha256'] or sha(manifest)!=capture.get('source_manifest_sha256'):raise ValueError('Actual capture source manifest provenance differs')
        source_record=json.loads(manifest.read_text())
        if source_record.get('inputs',source_record)!=source:raise ValueError('Actual capture source inventory provenance differs')
        if (facts.get('returncode_before_verdict')!=0 or facts.get('returncode')!=0 or facts.get('timed_out') is not False or facts.get('owned_group_empty_before_verdict') is not True or facts.get('owned_group_empty_after_cleanup') is not True):raise ValueError('Actual transport process was not normal')
        for stream in ('stdin','stdout','stderr'):
            if facts.get(stream+'_sha256')!=sha(paths[stream]) or capture.get(stream+'_sha256')!=sha(paths[stream]) or not str(facts.get(stream,'')).endswith('/'+entry[stream+'_path']):raise ValueError('Original transport stream provenance differs')
        consumed.append(manifest)
        consumed.extend(paths.values())
    return consumed

def host_context():
    import platform
    result={'platform':platform.platform(),'python':platform.python_version(),'affinity':sorted(os.sched_getaffinity(0))}
    for name in ['/proc/cpuinfo','/proc/loadavg','/proc/self/cgroup','/sys/fs/cgroup/cpu.max','/sys/fs/cgroup/cpu.stat','/proc/pressure/cpu','/proc/pressure/memory']:
        try:result[name]=Path(name).read_text()
        except OSError as error:result[name]={'error':repr(error)}
    return result
