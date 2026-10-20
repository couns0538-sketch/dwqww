"""Frozen five-bench grammar and whole-block performance analysis; no execution."""
import math,random,re,statistics
EXPECTED_NODES=321912
BENCHES_PER_PROCESS=5
BOOTSTRAP_SEED=20261027
BOOTSTRAP_DRAWS=10000
BENCH_LINE=re.compile(rb'info string bench depth ([1-9][0-9]*) nodes ([1-9][0-9]*) time ([1-9][0-9]*) nps ([1-9][0-9]*)(\r?\n)')
def parse_bench(raw):
    if not isinstance(raw,bytes):raise ValueError('Original benchmark bytes required')
    rows=raw.splitlines(keepends=True)
    if len(rows)!=BENCHES_PER_PROCESS:raise ValueError('Exactly five complete canonical rows required')
    records=[];endings=set()
    for line in rows:
        match=BENCH_LINE.fullmatch(line)
        if not match:raise ValueError('Noncanonical benchmark output')
        depth,nodes,millis,nps=map(int,match.groups()[:4]);endings.add(match[5])
        if depth!=11 or nodes!=EXPECTED_NODES or nps!=nodes*1000//millis:raise ValueError('Benchmark work/numeric signature differs')
        records.append({'depth':depth,'nodes':nodes,'time_ms':millis,'nps':nps})
    if len(endings)!=1:raise ValueError('Mixed benchmark line endings')
    return records

def positive(value):
    if type(value) not in (int,float) or not math.isfinite(value) or value<=0:raise ValueError('Metric must be finite positive number')
    return value

def block_logs(blocks,phase,count):
    if len(blocks)!=count:raise ValueError('Incomplete fixed block count')
    logs={'cpu':[],'wall':[]};identities=set()
    for index,block in enumerate(blocks):
        order='ABBA' if index%2==0 else 'BAAB'
        if block.get('phase')!=phase or block.get('block')!=index or block.get('order')!=order or len(block.get('samples',[]))!=4:raise ValueError('Block identity/order differs')
        for position,(sample,variant) in enumerate(zip(block['samples'],order)):
            identity=f'{phase}-{index:02d}-{position}'
            actual='baseline' if phase=='aa' or variant=='A' else 'candidate'
            if (sample.get('sample_id')!=identity or identity in identities or sample.get('phase')!=phase or sample.get('block')!=index or sample.get('index')!=position or sample.get('variant')!=variant or sample.get('binary_label')!=actual):raise ValueError('Sample identity/order/source differs')
            identities.add(identity)
        for metric in logs:
            values=[math.log(positive(sample[metric+'_seconds'])) for sample in block['samples']]
            logs[metric].append(sum(v if variant=='A' else -v for v,variant in zip(values,order))/2)
    return logs

def calibrate(blocks):
    logs=block_logs(blocks,'aa',15);result={}
    for metric,values in logs.items():
        median=statistics.median(values)
        passed=math.log(.99)<=median<=math.log(1.01) and all(math.log(.95)<=value<=math.log(1.05) for value in values)
        result[metric]={'block_ratios':[math.exp(v) for v in values],'median':math.exp(median),'passed':passed}
    result['passed']=all(result[m]['passed'] for m in logs)
    return result

def percentile(values,q):
    ordered=sorted(values);position=(len(ordered)-1)*q;low=math.floor(position);high=math.ceil(position)
    return ordered[low]+(ordered[high]-ordered[low])*(position-low)

def analyze_blocks(blocks):
    logs=block_logs(blocks,'ab',31);rng=random.Random(BOOTSTRAP_SEED);draws={key:[] for key in logs}
    for _ in range(BOOTSTRAP_DRAWS):
        indices=[rng.randrange(31) for _ in range(31)]
        for metric,values in logs.items():draws[metric].append(sum(values[i] for i in indices)/31)
    result={'bootstrap_seed':BOOTSTRAP_SEED,'bootstrap_draws':BOOTSTRAP_DRAWS,'resampling_unit':'whole counterbalanced four-sample block','percentile_method':'linear interpolation at (N-1)*q, q=.025/.975; same indices CPU/wall'}
    for metric,values in logs.items():
        result[metric]={'block_log_ratios':values,'block_ratios':[math.exp(v) for v in values],'geomean':math.exp(statistics.mean(values)),'ci95_lower':math.exp(percentile(draws[metric],.025)),'ci95_upper':math.exp(percentile(draws[metric],.975))}
    result['both_metrics_positive']=all(result[metric]['ci95_lower']>1 for metric in logs)
    return result
