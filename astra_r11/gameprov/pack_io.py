"""Original stdlib I/O/format helpers; no engine or training dependencies."""
from __future__ import annotations
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import time

CHUNK_ROWS = 50_000
MAX_LINE = 1_048_576
ROLES = {'source', 'cohort', 'train', 'holdout013', 'holdout014'}
POPULATION_ROLES = {'train', 'holdout013', 'holdout014'}
# Empty deliberately: a request/pack cannot authorize its own invented history.
# Add a digest only after independent review of archived historical evidence.
TRUSTED_PRODUCTION_ORIGINS: frozenset[str] = frozenset()
# Binding trust is independent of archive trust. The value pins every population
# input identity to prevent reusing a real mapping against another row ordering.
TRUSTED_PRODUCTION_BINDINGS: dict[str, dict[str, str]] = {}
_ACTIVE_BUDGET = None
PRODUCTION = {
 'source001': ('source', 'forge', 466506, 'de27d81720c0e33f10e0fa95e48b1f619b1325bf35675cd2fcd016fe48f338a2'),
 'source002': ('source', 'forge', 3126714, '16f3d241c1080b21bd7d05a3a297ef4ff11b49dea025c6301383815e85cb55b0'),
 'holdout013': ('holdout013', 'forge', 10000000, 'fa383b67aa30b8df79d5989b8fc5a92b5edf615fcfca0f1b46085c47600e17b9'),
 'holdout014': ('holdout014', 'forge', 6388575, 'b2c8ec79a2f24b72d5c1a124a14f64cd46c04221ff405cb4409b755a75abbef0'),
 'cohort': ('cohort', 'jsonl', 1000000, 'a3cc03b258dfe3adbe5e5d84b8c08dec96261d0b9b6fb8c0d9e87b874829ed1e'),
 'filtered': ('train', 'jsonl', 999953, '0e73a87c2e1af035aed34f51fdd74daefc05833ce133f254845f09f23aeb5dce'),
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def safe_path(value, *, write=False):
    p = Path(value)
    raw = str(p).replace('\\', '/')
    need(p.is_absolute(), 'absolute file path required')
    need(raw.lower().startswith('d:/'), 'pack-tool I/O must remain on D:')
    need(not raw.lower().endswith('.nnue'), '.nnue access refused')
    need(not re.search(r'(?i)^(f:|d:/a10(?:/|$))', raw), 'forbidden drive/workspace')
    need(':' not in raw[2:] and not any(x in raw for x in ('\x00', '*', '?')), 'unsafe path')
    need(not any(x in ('.', '..') for x in raw.split('/')), 'dot path refused')
    forbidden={'queue.txt','queue_state.json','forge_queue_state.json','stop','pause','npt','nnue-pytorch-amd'}
    need(not any(x.lower() in forbidden for x in raw.split('/')), 'protected control/runtime path refused')
    if write:
        need(raw.lower().startswith('d:/a11/'), 'all output must be under D:/a11')
    # Validate lexical aliases before any filesystem traversal. Validate each
    # ancestor with lstat, root first; never stat a descendant of a junction.
    parts=p.parts[1:]
    need(all(not part.endswith(('.', ' ')) for part in parts),'Windows trailing-dot/space alias refused')
    reserved={'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),*(f'LPT{i}' for i in range(1,10))}
    need(all(part.split('.')[0].upper() not in reserved for part in parts),'Windows device alias refused')
    q=Path(p.anchor)
    for i,part in enumerate((None,*parts)):
        if part is not None:q=q/part
        try:s=os.lstat(q)
        except FileNotFoundError:break
        need(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&1024,
             'symlink/reparse point refused: '+str(q))
        if i<len(parts):need(stat.S_ISDIR(s.st_mode),'non-directory path ancestor')
    return p


def pack_path(root, relative):
    need(isinstance(relative,str) and relative and '\\' not in relative and ':' not in relative,
         'pack path must be relative POSIX path')
    need(not relative.startswith('/') and all(x not in ('','.','..') for x in relative.split('/')),
         'unsafe pack path')
    return safe_path(Path(root)/relative)


def unique(pairs):
    d={}
    for k,v in pairs:
        need(k not in d, 'duplicate JSON key: '+k)
        d[k]=v
    return d


def decode(raw):
    def fail(s): raise ValueError('nonfinite JSON: '+s)
    obj=json.loads(raw,object_pairs_hook=unique,parse_constant=fail)
    need(isinstance(obj,dict),'JSON object required')
    return obj


def encoded(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode('ascii')


def write_json(path, value, *, replace=False):
    path=safe_path(path,write=True)
    pulse()
    with path.open('wb' if replace else 'xb') as stream:
        stream.write(encoded(value)); stream.flush(); os.fsync(stream.fileno())


def hashes(path):
    md5=hashlib.md5(); sha=hashlib.sha256(); size=0
    with safe_path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            pulse()
            size+=len(block);md5.update(block);sha.update(block)
    return {'md5':md5.hexdigest(),'sha256':sha.hexdigest(),'bytes':size}


def floor(reservation=0):
    need(shutil.disk_usage('C:/').free>=30*1024**3,'C30GiB floor')
    need(shutil.disk_usage('D:/').free>=50*1024**3+reservation,'D50GiB floor/reservation')


def tree_files(root):
    root=safe_path(root)
    try:s=os.lstat(root)
    except FileNotFoundError:return
    if stat.S_ISREG(s.st_mode):
        yield root
        return
    need(stat.S_ISDIR(s.st_mode),'regular file/directory required')
    with os.scandir(root) as entries:
        children=sorted((Path(entry.path) for entry in entries),key=str)
    for child in children:
        child=safe_path(child)  # lstat ancestry before any descent/open.
        s=os.lstat(child)
        if stat.S_ISDIR(s.st_mode):yield from tree_files(child)
        else:
            need(stat.S_ISREG(s.st_mode),'nonregular artifact refused')
            yield child


def estimate_budget(manifest, *, verification=False):
    """Conservative peak-retained bytes, including SQLite journals and outputs.

    Origin/binding rows and bytes are mandatory and validated by consumed-byte
    scans. Admission measures source sizes before trusting byte reservations.
    This is a fail-closed upper reservation, not a throughput guarantee.
    """
    inputs=manifest['inputs'];origins=manifest['origins'];bindings=manifest['bindings']
    all_specs=inputs+origins+bindings
    raw=sum(s['bytes'] for s in all_specs)
    cohort=next(s for s in inputs if s['role']=='cohort')
    origin_bytes=sum(s['bytes'] for s in origins);origin_rows=sum(s['rows'] for s in origins)
    binding_bytes=sum(s['bytes'] for s in bindings);binding_rows=sum(s['rows'] for s in bindings)
    # Originals payload + B-tree/page overhead + rollback journal, and maps.
    index=4*cohort['bytes']+512*cohort['rows']+8*(origin_bytes+binding_bytes)+1024*(origin_rows+binding_rows)
    retained=(2*sum(s['bytes'] for s in inputs if s['role'] in POPULATION_ROLES)+2048*binding_rows) if binding_rows else 0
    if verification:
        # The emitted-row index duplicates retained payload; no original copies.
        return index+2*retained+64*1024**2
    gzip_worst=raw+raw//500+1024*len(all_specs)
    return gzip_worst+index+retained+64*1024**2


class ResourceBudget:
    def __init__(self,reservation,paths):
        need(type(reservation) is int and reservation>0,'positive bounded reservation required')
        self.reservation=reservation;self.paths=[safe_path(p,write=True) for p in paths]
        self.last=-1.0
        floor(reservation)
    def __enter__(self):
        global _ACTIVE_BUDGET
        self.previous=_ACTIVE_BUDGET
        self.check()
        _ACTIVE_BUDGET=self
        return self
    def __exit__(self,*_):
        global _ACTIVE_BUDGET
        _ACTIVE_BUDGET=self.previous
    def check(self):
        floor()
        now=time.monotonic()
        if now-self.last>=1:
            size=sum(os.lstat(p).st_size for root in self.paths for p in tree_files(root))
            need(size<=self.reservation,'retained-output/index reservation exceeded')
            self.last=now


def pulse():
    if _ACTIVE_BUDGET is not None:_ACTIVE_BUDGET.check()
    else:floor()


def lines(path, *, compressed=False):
    p=safe_path(path)
    opener=gzip.open if compressed else open
    with opener(p,'rb') as f:
        count=0;since_check=0
        while True:
            raw=f.readline(MAX_LINE+1)
            if not raw:break
            need(len(raw)<=MAX_LINE and raw.endswith(b'\n'),'invalid/oversize/unterminated row')
            count+=1;since_check+=len(raw)
            if count%4096==1 or since_check>=1024*1024:
                pulse();since_check=0
            yield raw


def state(fen):
    need(isinstance(fen,str),'FEN text required')
    fields=fen.split()
    need(len(fields)==6 and ' '.join(fields)==fen,'exact six-field FEN required')
    board,side,castling,ep,half,full=fields
    ranks=board.split('/')
    need(len(ranks)==8 and all(sum(int(c) if c in '12345678' else 1 for c in rank)==8 for rank in ranks),
         'invalid FEN board')
    need(all(c in 'prnbqkPRNBQK12345678/' for c in board),'invalid FEN piece')
    need(side in ('w','b') and (castling=='-' or re.fullmatch('K?Q?k?q?',castling) and castling), 'invalid FEN side/castling')
    need(ep=='-' or re.fullmatch('[a-h][36]',ep),'invalid FEN EP')
    need(half.isdecimal() and full.isdecimal() and int(full)>0,'invalid FEN clock')
    return fields


def raw_record(raw):
    text=raw.decode('utf-8').removesuffix('\n').removesuffix('\r')
    parts=text.split(' | ')
    need(len(parts)==3,'Forge row must be FEN | score | result')
    fen,score,result=parts; f=state(fen)
    need(re.fullmatch('-?[0-9]+',score) is not None,'invalid score')
    need(result in ('0','0.0','0.5','1','1.0'),'invalid raw result')
    return {'fen':fen,'ply':2*(int(f[5])-1)+(f[1]=='b'), 'raw_score':score,
            'result_white':{'0':-1,'0.0':-1,'0.5':0,'1':1,'1.0':1}[result], 'original_line':text}


def validate_request(req, fixture_trust=None):
    need(req.get('schema')==1 and req.get('scope') in ('production','fixture'),'unsupported schema/scope')
    need(isinstance(req.get('inputs'),list) and bool(req['inputs']),'inputs required')
    ids=set();roles={}
    for s in req['inputs']:
        need(isinstance(s,dict) and re.fullmatch('[a-zA-Z0-9_-]+',s.get('id','')),'invalid input id')
        need(s['id'] not in ids,'duplicate input id');ids.add(s['id'])
        need(s.get('role') in ROLES and s.get('format') in ('forge','jsonl'),'invalid input format/role')
        need(type(s.get('rows')) is int and s['rows']>0,'positive complete input rows required')
        need(re.fullmatch('[0-9a-f]{64}',s.get('sha256','')) is not None,'trusted input SHA256 required')
        roles[s['role']]=roles.get(s['role'],0)+1
    need(all(roles.get(r)==1 for r in ('cohort','train','holdout013','holdout014')),'complete cohort/train/two holdouts required')
    need(roles.get('source',0)>=1,'original raw source required')
    if req['scope']=='production':
        need({s['id']:(s['role'],s['format'],s['rows'],s['sha256']) for s in req['inputs']}==PRODUCTION,
             'production input identities/population differ from R10')
        need(not fixture_trust,'fixture trust cannot authorize production')
    need(isinstance(req.get('source_labels'),dict),'source_labels required')
    for label,input_id in req['source_labels'].items():
        need(isinstance(label,str) and input_id in ids,'unknown source mapping')
        need(next(s for s in req['inputs'] if s['id']==input_id)['role']=='source','source mapping must reference raw source')
    need(isinstance(req.get('origins'),list) and isinstance(req.get('bindings'),list),'origin/binding lists required')
    fixture_trust=fixture_trust or {'origins':set(),'bindings':{}}
    need(isinstance(fixture_trust,dict) and set(fixture_trust)=={'origins','bindings'},'explicit origin AND binding trust required')
    trust=TRUSTED_PRODUCTION_ORIGINS if req['scope']=='production' else frozenset(fixture_trust['origins'])
    binding_trust=TRUSTED_PRODUCTION_BINDINGS if req['scope']=='production' else fixture_trust['bindings']
    input_context={s['id']:s['sha256'] for s in req['inputs'] if s['role'] in POPULATION_ROLES}
    for origin in req['origins']:
        need(origin.get('format')=='archived-game-rows-v1','unsupported archived origin adapter')
        need(origin.get('sha256') in trust,'origin not authenticated by reviewed trusted registry')
    for spec in req['origins']+req['bindings']:
        need(type(spec.get('rows')) is int and spec['rows']>0 and type(spec.get('bytes')) is int and spec['bytes']>0,
             'bounded origin/binding row and byte metadata required')
        need(re.fullmatch('[0-9a-f]{64}',spec.get('sha256','')) is not None,'origin/binding SHA256 required')
    for binding in req['bindings']:
        need(binding['sha256'] in binding_trust,'row-to-game binding not authenticated by reviewed trusted registry')
        need(binding_trust[binding['sha256']]==input_context,'binding input source identities changed')
    return trust
