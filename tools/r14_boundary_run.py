"""Bounded native resolution and receipts for all boundary-window candidates."""
from __future__ import annotations

from collections import Counter
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import struct
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r14_boundary
from r14_boundary import Population, parse_endpoint, candidate_chunks, count_candidates, ACCOUNTING_FIELDS, read_window
from r14_segments import PairEvidence, SourceRecord, TransportFailure, validate_reply, Guard, validate_qualification
from r14_qualification.qualify import hashes, resource_guard, Native, DEFAULT_CANDIDATE
from r14_scan import load_pins
from run_policy import safe_path

QUERY_STRUCT = struct.Struct('<IIBBBI')


class ReceiptWriter:
    def __init__(self, directory, guard, chunk_bytes=10*1024**2):
        self.directory = Path(directory)
        guard()
        self.directory.mkdir(exist_ok=False)
        self.guard, self.chunk_bytes = guard, chunk_bytes
        self.opened, self.parts, self.artifacts = {}, Counter(), []

    def append(self, kind, payload):
        if kind not in ('queries','positives') or len(payload) > self.chunk_bytes:
            raise ValueError('invalid bounded receipt payload')
        current = self.opened.get(kind)
        if current is not None and current['bytes']+len(payload) > self.chunk_bytes:
            self.finish(kind)
            current = None
        if current is None:
            self.guard()
            self.parts[kind] += 1
            suffix = 'bin' if kind == 'queries' else 'jsonl'
            destination = self.directory/f'{kind}_{self.parts[kind]:04}.{suffix}'
            pending = destination.with_suffix(destination.suffix+'.part')
            current = dict(path=destination,pending=pending,stream=pending.open('xb'),bytes=0,records=0,
                           renamed=False,close_succeeded=False,seal_io_failed=False)
            self.opened[kind] = current
        if current['stream'].write(payload) != len(payload):
            raise OSError('partial receipt write')
        current['bytes'] += len(payload)
        current['records'] += 1

    def query(self,left,right,depth,attempt,evidence):
        self.append('queries',QUERY_STRUCT.pack(left.line,right.line,depth,attempt,evidence.code,evidence.nodes))

    def positive(self,left,right,depth,evidence):
        payload = dict(left_line=left.line,right_line=right.line,depth=depth,nodes=evidence.nodes,
                       witness=list(evidence.witness))
        self.append('positives',(json.dumps(payload,sort_keys=True)+'\n').encode('ascii'))

    def finish(self,kind):
        self.guard()
        current = self.opened[kind]
        if current['seal_io_failed']:
            raise OSError('prior receipt seal or close failed')
        if not current['close_succeeded']:
            if current['stream'].closed:
                current['seal_io_failed'] = True
                raise OSError('receipt handle closed without a successful close')
            try:
                current['stream'].flush()
                os.fsync(current['stream'].fileno())
                current['stream'].close()
            except Exception:
                current['seal_io_failed'] = True
                raise
            current['close_succeeded'] = True
        stored_path = current['path'] if current['renamed'] else current['pending']
        if stored_path.stat().st_size != current['bytes']:
            raise OSError('receipt size mismatch')
        self.guard()
        if not current['renamed']:
            os.rename(current['pending'],current['path'])
            current['renamed'] = True
        self.artifacts.append(dict(kind=kind,bytes=current['bytes'],records=current['records'],**hashes(current['path'])))
        del self.opened[kind]

    def close(self):
        for kind in list(self.opened):
            self.finish(kind)

    def abort(self):
        for current in self.opened.values():
            try:
                current['stream'].raw.close()
            except (OSError,ValueError):
                pass
            try:
                current['stream'].close()
            except (OSError,ValueError):
                pass
        self.opened.clear()


def _record(endpoint):
    return SourceRecord(endpoint.source_id,endpoint.line,endpoint.row(),True)


def search_candidates(left,right,first_pass,query_many,writer,report,guard=lambda: None):
    """Repeat enumeration, resolve bounded batches, and preserve every unknown."""
    if first_pass.get('complete') is not True:
        raise ValueError('complete first enumeration pass required')
    report.clear()
    report.update(complete=False,attempted_pairs=0,query_attempts=0,retried_pairs=0,
                  candidate_pairs=first_pass['survivors'],unqueried_pairs=first_pass['survivors'],
                  initial_counts={},retry_counts={},final_counts={},final_reasons={},
                  query_receipts_written=0,positive_receipts_written=0,receipt_errors=0,
                  unrecorded_query_attempts=0,unrecorded_positive_pairs=0,receipt_accounting_complete=False)
    initial, retries, final, reasons = Counter(),Counter(),Counter(),Counter()
    second, pending = {},[]
    pending_bytes, ordinal = 0,0

    def snapshot():
        report.update(initial_counts=dict(initial),retry_counts=dict(retries),final_counts=dict(final),
                      final_reasons=dict(reasons),second_pass=second,
                      unqueried_pairs=first_pass['survivors']-report['attempted_pairs'],
                      unrecorded_query_attempts=report['query_attempts']-report['query_receipts_written'],
                      unrecorded_positive_pairs=final['REACHABLE']-report['positive_receipts_written'])
        report['receipt_accounting_complete'] = bool(
            report['receipt_errors'] == 0 and report['unrecorded_query_attempts'] == 0 and
            report['unrecorded_positive_pairs'] == 0 and sum(final.values()) == report['attempted_pairs'])

    def request(items,cap,attempt,previous=None):
        guard()
        if attempt == 2 and (previous is None or len(previous) != len(items)):
            raise ValueError('retry requires its prior pair outcomes')
        lines = []
        for a,b,depth,ident in items:
            lines.append('\t'.join((ident,a.fen,a.result,b.fen,b.result,'8',str(cap))))
        report['query_attempts'] += len(items)
        if attempt == 1:
            report['attempted_pairs'] += len(items)
        else:
            report['retried_pairs'] += len(items)
        request_error = None
        try:
            replies = query_many(lines)
            if not isinstance(replies,list) or len(replies) != len(items):
                raise TransportFailure('boundary reply count mismatch')
            outcomes = [validate_reply(_record(a),_record(b),reply,ident,cap,8)
                        for (a,b,_,ident),reply in zip(items,replies)]
        except Exception as error:
            request_error = error
            outcomes = [PairEvidence(_record(a),_record(b),8) for a,b,_,_ in items]
        # Commit every validated classification before any receipt allocation.
        for index,event in enumerate(outcomes):
            if attempt == 1:
                initial[event.status] += 1
            else:
                retries[event.status] += 1
                final[previous[index].status] -= 1
                reasons[previous[index].reason] -= 1
            final[event.status] += 1
            reasons[event.reason] += 1
        snapshot()
        if request_error is not None:
            resource_guard(reserve_bytes=1024**2)
        try:
            for (a,b,depth,_),event in zip(items,outcomes):
                writer.query(a,b,depth,attempt,event)
                report['query_receipts_written'] += 1
                if event.code == 0:
                    writer.positive(a,b,depth,event)
                    report['positive_receipts_written'] += 1
        except Exception as error:
            report['receipt_errors'] += 1
            report['receipt_error'] = f'{type(error).__name__}: {error}'
            snapshot()
            raise
        snapshot()
        if request_error is not None:
            raise TransportFailure(f'boundary batch failed: {type(request_error).__name__}: {request_error}') from request_error
        return outcomes

    def flush():
        nonlocal pending,pending_bytes
        if not pending:
            return
        batch = pending
        pending,pending_bytes = [],0
        outcomes = request(batch,100000,1)
        for (a,b,depth,ident),event in zip(batch,outcomes):
            if event.code != 5:
                continue
            request([(a,b,depth,ident+'r')],1000000,2,[event])

    try:
        for chunk in candidate_chunks(left,right,second,guard):
            for index in chunk.right_indices:
                target = right.valid[int(index)]
                ordinal += 1
                ident = f'b{ordinal}'
                line = '\t'.join((ident,chunk.left.fen,chunk.left.result,target.fen,target.result,'8','100000'))
                size = len(line.encode('ascii'))+1
                if size > 2048:
                    raise ValueError('candidate request exceeds transport bound')
                if len(pending) == 8 or pending_bytes+size > 2048:
                    flush()
                pending.append((chunk.left,target,chunk.depth,ident))
                pending_bytes += size
        flush()
        if any(second.get(name) != first_pass.get(name) for name in (*ACCOUNTING_FIELDS,'total_pairs','complete')):
            raise RuntimeError('candidate enumeration passes disagree')
        if report['attempted_pairs'] != first_pass['survivors'] or sum(final.values()) != report['attempted_pairs']:
            raise RuntimeError('native pair accounting mismatch')
        snapshot()
        if not report['receipt_accounting_complete']:
            raise RuntimeError('native receipt accounting mismatch')
        report['complete'] = True
    finally:
        snapshot()


def no_link_verdict(first_pass,search):
    if search.get('final_counts',{}).get('REACHABLE',0):
        return 'FAIL'
    if (first_pass.get('complete') is True and first_pass.get('total_pairs',0) > 0 and
        first_pass.get('invalid_endpoint_pairs') == 0 and search.get('complete') is True and
        search.get('attempted_pairs') == first_pass.get('survivors') and search.get('unqueried_pairs') == 0 and
        search.get('final_counts',{}).get('UNKNOWN',0) == 0):
        return 'PASS'
    return 'UNVERIFIED'


def seam_verdict(first_pass,search,*,receipts_complete,native_session_success=False):
    if (receipts_complete is not True or native_session_success is not True or
        search.get('receipt_accounting_complete') is not True):
        return 'UNVERIFIED'
    return no_link_verdict(first_pass,search)


def close_native_session(child,seam):
    try:
        child.close()
    except Exception as error:
        seam['native_session_success'] = False
        seam['native_session_failed'] = True
        seam['complete'] = False
        seam.setdefault('native_session_errors',[]).append(f'{type(error).__name__}: {error}')
        raise
    if not seam.get('native_session_failed',False):
        seam['native_session_success'] = True


def _publish(path,report):
    payload = (json.dumps(report,sort_keys=True,indent=2)+'\n').encode('utf-8')
    resource_guard(reserve_bytes=len(payload)+4096)
    temporary = path.with_suffix(path.suffix+'.part')
    with temporary.open('xb') as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    resource_guard(reserve_bytes=4096)
    os.rename(temporary,path)


def validate_filter_qualification(report,core_identity):
    if (report.get('schema') != 1 or report.get('scope') != 'boundary_filter_qualification' or
        report.get('status') != 'PASS' or report.get('complete') is not True):
        raise ValueError('completed production filter qualification PASS required')
    requested,resolved = report.get('requested_random_pairs'),report.get('resolved_random_pairs')
    if type(requested) is not int or requested < 100000 or type(resolved) is not int or resolved < requested:
        raise ValueError('100000 resolved random legal filter pairs required')
    zero_fields = ('rejected_legal_pairs','special_failures','popcount_disagreements')
    if any(type(report.get(field)) is not int or report[field] != 0 for field in zero_fields):
        raise ValueError('filter qualification failures')
    if type(report.get('special_pairs')) is not int or report['special_pairs'] < 10:
        raise ValueError('filter qualification failures or missing special paths')
    if type(report.get('popcount_checks')) is not int or report['popcount_checks'] < requested:
        raise ValueError('filter qualification popcount coverage incomplete')
    if report.get('core') != core_identity:
        raise ValueError('filter qualification core identity mismatch')
    identities = report.get('tool_identities')
    if not isinstance(identities,list) or not identities:
        raise ValueError('filter qualification dependency identities missing')
    for identity in identities:
        if not isinstance(identity,dict) or hashes(safe_path(identity.get('path',''))) != identity:
            raise ValueError('filter qualification dependency identity mismatch')
    return report


def main(argv=None):
    root = Path('D:/a14')
    source = Path('D:/grok-pc-data/selfplay_out')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--pins',type=Path,default=root/'evidence/r14/input-pins-all.jsonl')
    parser.add_argument('--qualification',type=Path,required=True)
    parser.add_argument('--qualification-md5',required=True)
    parser.add_argument('--filter-qualification',type=Path,required=True)
    parser.add_argument('--filter-qualification-md5',required=True)
    parser.add_argument('--native',type=Path,default=DEFAULT_CANDIDATE)
    parser.add_argument('--cpu',type=int,default=3)
    parser.add_argument('--seconds',type=float,default=5400)
    args = parser.parse_args(argv)
    guard = Guard(args.seconds,args.cpu)
    native_identity = hashes(safe_path(args.native))
    qualification = hashes(safe_path(args.qualification))
    if qualification['md5'] != args.qualification_md5:
        raise ValueError('qualification pin mismatch')
    validate_qualification(json.loads(Path(qualification['path']).read_text()),native_identity)
    filter_qualification = hashes(safe_path(args.filter_qualification))
    if filter_qualification['md5'] != args.filter_qualification_md5:
        raise ValueError('filter qualification pin mismatch')
    core_identity = hashes(Path(r14_boundary.__file__))
    validate_filter_qualification(json.loads(Path(filter_qualification['path']).read_text()),core_identity)
    pin_identity = hashes(safe_path(args.pins))
    pins = load_pins(Path(pin_identity['path']))
    out = safe_path(args.out,write=True)
    resource_guard(reserve_bytes=32*1024**2)
    out.mkdir(parents=True,exist_ok=False)
    for name in ('TEMP','TMP'):
        os.environ[name] = str(out)
    identities = [hashes(path) for path in (
        Path(__file__),Path(r14_boundary.__file__),root/'tools/r14_segments.py',
        root/'tools/r14_qualification/qualify.py',root/'tools/r14_scan.py',root/'tools/run_policy.py',
        Path(sys.executable),Path(r14_boundary.chess.__file__),Path(r14_boundary.np.__file__))]
    report = dict(schema=1,scope='all_pairs_bounded_boundary_windows',status='UNVERIFIED',
                  authentic_game_separation='UNVERIFIED',bounded_no_link_status='UNVERIFIED',complete=False,
                  k=8,window_rows=50000,initial_nodes=100000,retry_nodes=1000000,
                  native=native_identity,qualification=qualification,pins=pin_identity,tool_identities=identities,
                  filter_qualification=filter_qualification,
                  start_vienna=datetime.now().strftime('%Y-%m-%d %H:%M:%S Vienna'),seams=[],reasons=[],
                  query_format=dict(format='<IIBBBI',bytes=15,
                                    fields=['left_line','right_line','depth','attempt','outcome_code','nodes']),
                  verdict_scope='Every physical endpoint pair in each selected window, within 1..8 legal plies; original game identities are not established.')
    began,last_progress = time.monotonic(),0.0
    active_seam = None
    child = writer = None

    def progress(value=None):
        nonlocal last_progress
        now = time.monotonic()
        if now-last_progress < 30:
            return
        resource_guard(reserve_bytes=1024**2)
        value = dict(value or {})
        value.update(elapsed_seconds=now-began,seam=active_seam.get('name') if active_seam else None,
                     stage=active_seam.get('stage') if active_seam else 'initializing')
        if active_seam:
            value['first_pass'] = active_seam.get('first_pass',{})
            search = active_seam.get('search',{})
            value['search_counts'] = {key:search.get(key) for key in ('attempted_pairs','query_attempts','final_counts','unqueried_pairs')}
        payload = json.dumps(value,sort_keys=True)
        print(payload,flush=True)
        with (out/'progress.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(payload+'\n')
        last_progress = now

    def check():
        guard()
        progress()

    try:
        for left_id,right_id in ((12,13),(14,15)):
            guard()
            active_seam = dict(name=f'{left_id:03}|{right_id:03}',left_source_id=left_id,right_source_id=right_id,
                               stage='source_windows',complete=False,bounded_no_link_status='UNVERIFIED',
                               first_pass={},search={},inputs=[],artifacts=[],receipt_seal_complete=False,
                               native_session_success=False,native_session_failed=False,native_session_errors=[])
            report['seams'].append(active_seam)
            directory = out/f'seam_{left_id:03}_{right_id:03}'
            resource_guard(reserve_bytes=1024**2)
            directory.mkdir()
            windows = []
            for source_id,side in ((left_id,'last'),(right_id,'first')):
                path = safe_path(source/f'forge_selfplay_{source_id:03}.txt')
                pin = pins.get(str(path).casefold())
                if pin is None:
                    raise ValueError('missing source pin: '+str(path))
                receipt = {}
                active_seam['inputs'].append(receipt)
                records,_ = read_window(path,pin,side,50000,source_id,check,progress,receipt)
                windows.append(Population(records))
            left,right = windows
            active_seam['stage'] = 'count_all_candidates'
            for _ in candidate_chunks(left,right,active_seam['first_pass'],check):
                pass
            active_seam['stage'] = 'resolve_candidates'
            writer = ReceiptWriter(directory/'parts',check)
            child = Native(args.native,'--pairs',directory/'native.stderr.log',guard.deadline)
            guard.child = child
            search_candidates(left,right,active_seam['first_pass'],child.query_many,writer,active_seam['search'],check)
            close_native_session(child,active_seam)
            child = None
            guard.child = None
            writer.close()
            active_seam['artifacts'] = writer.artifacts
            active_seam['receipt_seal_complete'] = True
            writer = None
            active_seam['bounded_no_link_status'] = seam_verdict(active_seam['first_pass'],active_seam['search'],
                                                               receipts_complete=active_seam['receipt_seal_complete'],
                                                               native_session_success=active_seam['native_session_success'])
            active_seam['complete'] = True
            active_seam['stage'] = 'complete'
            progress()
        report['complete'] = True
    except Exception as error:
        report['reasons'].append(f'{type(error).__name__}: {error}')
        if isinstance(error,r14_boundary.InputHashMismatch):
            report['stop_rule'] = 'input_md5_mismatch'
    finally:
        if child is not None:
            try:
                close_native_session(child,active_seam)
            except Exception as error:
                report['complete'] = False
                report['reasons'].append(f'native close: {error}')
        try:
            resource_guard(reserve_bytes=32*1024**2)
        except Exception as error:
            if writer is not None:
                writer.abort()
            print(json.dumps(dict(status='UNVERIFIED',complete=False,hard_stop=str(error),report=report)),flush=True)
            return 2
        if writer is not None:
            try:
                writer.guard = lambda: resource_guard(reserve_bytes=32*1024**2)
                writer.close()
                active_seam['receipt_seal_complete'] = True
            except Exception as error:
                writer.abort()
                active_seam['receipt_seal_complete'] = False
                report['reasons'].append(f'receipt seal: {error}')
            active_seam['artifacts'] = writer.artifacts
        if active_seam is not None and active_seam.get('first_pass',{}).get('complete'):
            active_seam['bounded_no_link_status'] = seam_verdict(active_seam['first_pass'],active_seam['search'],
                                                               receipts_complete=active_seam['receipt_seal_complete'],
                                                               native_session_success=active_seam['native_session_success'])
        stable = True
        for identity in [native_identity,qualification,filter_qualification,pin_identity,*identities]:
            try:
                unchanged = hashes(identity['path']) == identity
            except Exception:
                unchanged = False
            if not unchanged:
                stable = False
                report['complete'] = False
                report['reasons'].append('identity changed: '+identity['path'])
        verdicts = [seam['bounded_no_link_status'] for seam in report['seams']]
        if stable and 'FAIL' in verdicts:
            report['bounded_no_link_status'] = 'FAIL'
        elif stable and report['complete'] and len(verdicts) == 2 and all(value == 'PASS' for value in verdicts):
            report['bounded_no_link_status'] = 'PASS'
        report.update(elapsed_seconds=time.monotonic()-began,
                      end_vienna=datetime.now().strftime('%Y-%m-%d %H:%M:%S Vienna'))
        report['reasons'].append('Bounded reachability does not authenticate original game IDs or historical writer binding.')
        try:
            _publish(out/'REPORT.json',report)
        except Exception as error:
            print(json.dumps(dict(status='UNVERIFIED',complete=False,publication_error=str(error))),flush=True)
            return 2
        print(json.dumps(dict(status='UNVERIFIED',bounded_no_link_status=report['bounded_no_link_status'],
                              complete=report['complete'],report=str(out/'REPORT.json'))),flush=True)
    return 0 if report['complete'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
