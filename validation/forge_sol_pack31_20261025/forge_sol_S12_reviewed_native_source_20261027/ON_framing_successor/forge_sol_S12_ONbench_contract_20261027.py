"""Strict raw S12 ON bench framing; never launch or rewrite engine output.

The normal OFF S25 parser remains unchanged. ON permits exactly the source's
active-once line, eight typed per-search stats, then the fixed bench terminal.
For repeated benches in one process only the first block has an active line.
"""
import hashlib
import re

REFERENCES={11:308972,13:745494,16:2460422,20:11901452,22:31111774}
FIELDS=('refreshes','updates','zero_dirty_edges','copies_avoided','alias_hits','evaluations')
UINT=r'(?:0|[1-9][0-9]*)'
STATS=re.compile(('info string NnueLazyAcc stats '+
    ' '.join(name+' ('+UINT+')' for name in FIELDS)).encode('ascii'))
SUMMARY=re.compile(('info string bench depth ('+UINT+') nodes ('+UINT+') time ('+UINT+') nps ('+UINT+')').encode('ascii'))
ACTIVE=b'info string NnueLazyAcc active'


class ContractError(ValueError):
    def __init__(self,code):self.code=code;super().__init__(code)


def require(okay,code):
    if not okay:raise ContractError(code)


def uint(raw):
    require(len(raw)<=20,'counter_uint64_overflow')
    value=int(raw)
    require(0<=value<2**64,'counter_uint64_overflow')
    return value


def body(line):
    if line.endswith(b'\r\n'):return line[:-2]
    require(line.endswith(b'\n'),'missing_line_ending')
    return line[:-1]


def inspect_ON_bench_sequence(stdout,stderr,receipt,references):
    """Validate complete original bytes and a closed captured-process receipt.

    Call only after normal owned transport closure. No lines are discarded and
    no normalized derivative is presented as the original stdout/EOF evidence.
    Synthetic tests label themselves as fixtures; this function runs no engine.
    """
    result={'status':'FAIL','errors':[],'benchmarks':[],'active_lines':0,
            'parser_scope':'S12 runtime ON only; normal OFF parser unchanged'}
    try:
        require(type(stdout) is bytes and type(stderr) is bytes,'raw_byte_streams_required')
        require(type(receipt) is dict,'closed_capture_receipt_required')
        require(type(receipt.get('returncode')) is int and receipt['returncode']==0,'bench_exit')
        require(all(receipt.get(name) is True for name in (
            'stdout_complete','stderr_complete','close_protocol_valid','reader_queues_cleared')),'incomplete_or_open_capture')
        require(not stderr,'bench_stderr')
        captures=receipt.get('captures')
        require(type(captures) is dict,'original_capture_records_required')
        for name,raw in (('stdout',stdout),('stderr',stderr)):
            record=captures.get(name)
            require(type(record) is dict and type(record.get('bytes')) is int and record['bytes']==len(raw)
                and record.get('sha256')==hashlib.sha256(raw).hexdigest(),'original_capture_hash_or_length_differs')
        require(type(references) in (tuple,list) and 1<=len(references)<=5,'unsupported_bench_sequence')
        for row in references:
            require(type(row) in (tuple,list) and len(row)==2 and all(type(x) is int for x in row)
                and row[0] in REFERENCES and REFERENCES[row[0]]==row[1],'unknown_fixed_reference')
        require(0<len(stdout)<=8192*len(references),'raw_ON_frame_size')
        lines=stdout.splitlines(keepends=True)
        # Exactly one active line at the first search, eight stats per bench,
        # one terminal per bench, and no bytes before/between/after the grammar.
        require(len(lines)==1+9*len(references),'ON_frame_line_count')
        require(body(lines[0])==ACTIVE,'active_once_prefix')
        result['active_lines']=1
        cursor=1
        for depth,nodes in references:
            stats=[];totals={key:0 for key in FIELDS}
            for _ in range(8):
                match=STATS.fullmatch(body(lines[cursor]));cursor+=1
                require(match is not None,'malformed_or_unexpected_ON_stats')
                item={key:uint(raw) for key,raw in zip(FIELDS,match.groups())}
                require(item['refreshes']>=1 and item['evaluations']>=1
                    and item['copies_avoided']==item['zero_dirty_edges']
                    and item['alias_hits']<=item['evaluations'],'inconsistent_ON_counters')
                for key,value in item.items():
                    totals[key]+=value
                    require(totals[key]<2**64,'aggregate_counter_uint64_overflow')
                stats.append(item)
            require(totals['copies_avoided']>0,'ON_copy_path_not_exercised')
            match=SUMMARY.fullmatch(body(lines[cursor]));cursor+=1
            require(match is not None,'missing_or_malformed_bench_terminal')
            actual_depth,actual_nodes,elapsed,nps=(uint(raw) for raw in match.groups())
            require((actual_depth,actual_nodes)==(depth,nodes),'bench_fixed_reference')
            require(nps==(nodes*1000//elapsed if elapsed else 0),'bench_source_nps_formula')
            result['benchmarks'].append({'depth':depth,'nodes':nodes,'stats':stats,'totals':totals})
        require(cursor==len(lines),'post_summary_bytes')
        result.update(status='PASS',raw_stdout_bytes=len(stdout),raw_stdout_sha256=hashlib.sha256(stdout).hexdigest(),
            raw_stderr_sha256=hashlib.sha256(stderr).hexdigest(),original_EOF_receipt_verified=True)
    except ContractError as error:result['errors'].append({'code':error.code})
    return result
