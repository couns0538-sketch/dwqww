#!/usr/bin/env python3
"""Count, normalize and preserve compiler sanitizer diagnostics from raw stderr."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re


HEAD = re.compile(r'^\s*(?:==\d+==\s*)?(ERROR|FATAL|WARNING):\s*'
                  r'(AddressSanitizer|LeakSanitizer|ThreadSanitizer):\s*(.*?)\s*$')
UB = re.compile(r'^\s*(.+?):(\d+)(?::\d+)?: runtime error:\s*(.*)$')
ASAN_FATAL = re.compile(r'^\s*(?:==\d+==\s*)?(?:AddressSanitizer: (?:CHECK failed|FATAL)|'
                        r'ASan runtime does not come first|Shadow memory range interleaves).*$', re.I)
DEADLY = re.compile(r'^\s*(?:==\d+==\s*)?AddressSanitizer:\s*DEADLYSIGNAL\s*$')
TSAN_FATAL = re.compile(r'^\s*(?:==\d+==\s*)?ThreadSanitizer(?:\s+CHECK failed|:\s*FATAL).*$', re.I)
FRAME = re.compile(r'^\s*#\d+\s+(.*)$')
LOC = re.compile(r'(?P<file>(?:[A-Za-z]:)?[^\s():]+):(?P<line>\d+)(?::\d+)?(?=\s|\)|$)')
HEX = re.compile(r'0x[\da-fA-F]+')
MODULE = re.compile(r'\(([^\s()]+?)(?:\+0x[\da-fA-F]+)?\)\s*$')
SEPARATOR = re.compile(r'^={10,}\s*$')
ABORTING = re.compile(r'^\s*(?:==\d+==\s*)?ABORTING\s*$')
TAG = re.compile(r'^[A-Za-z0-9._/-]+$')


def clean_message(message):
    message = HEX.sub('<address>', message)
    message = re.sub(r'\(pid=\d+\)|==\d+==|\bthread T\d+\b', '', message, flags=re.I)
    message = re.sub(r"(?<!\w)-?\d+\b", '<n>', message)
    return ' '.join(message.split())


def normalized_path(name):
    parts = [p for p in name.replace('\\', '/').split('/') if p not in ('', '.', '..')]
    components = [i for i,p in enumerate(parts) if p in ('src','include')]
    if components:
        return '/'.join(parts[components[-1]:])
    if 'libsanitizer' in parts:
        return '/'.join(parts[parts.index('libsanitizer'):])
    return parts[-1] if parts else name


def ub_kind(message):
    low = message.lower()
    for prefix in ('signed integer overflow','unsigned integer overflow','division by zero',
                   'left shift of negative value','negation of','shift exponent','load of misaligned address',
                   'store to misaligned address','pointer index expression','member access within null pointer',
                   'load of null pointer','store to null pointer','reference binding to null pointer',
                   'execution reached an unreachable program point','applying non-zero offset to null pointer'):
        if low.startswith(prefix):
            return prefix
    if low.startswith('index ') and ' out of bounds for type ' in low:
        return 'index out of bounds'
    if low.startswith(('load of address ', 'store to address ')) and 'insufficient space' in low:
        return 'insufficient object space'
    return clean_message(low)


def identify(line):
    found = HEAD.fullmatch(line)
    if found:
        level, tool, text = found.groups()
        name = {'AddressSanitizer':'ASan','LeakSanitizer':'LSan','ThreadSanitizer':'TSan'}[tool]
        if name == 'TSan':
            kind = clean_message(text.lower())
        elif name == 'LSan':
            kind = 'memory leak' if 'memory leak' in text.lower() else clean_message(text.lower())
        else:
            prefix = re.match(r'(?:attempting\s+)?([A-Za-z]+(?:-[A-Za-z]+)+|SEGV|BUS|FPE|ILL)\b', text)
            kind = prefix[1].lower() if prefix else clean_message(text.split(' on ',1)[0].lower())
        return {'sanitizer':name,'severity':level.lower(),'kind':kind,
                'runtime_failure':level=='FATAL'}, None
    match = UB.fullmatch(line)
    if match:
        return {'sanitizer':'UBSan','severity':'error','kind':ub_kind(match[3]),'runtime_failure':False}, {
            'file':normalized_path(match[1]),'line':int(match[2]),
        }
    if DEADLY.fullmatch(line):
        return {'sanitizer':'ASan','severity':'fatal','kind':'deadlysignal','runtime_failure':True}, None
    if ASAN_FATAL.fullmatch(line) or TSAN_FATAL.fullmatch(line):
        name = 'TSan' if TSAN_FATAL.fullmatch(line) else 'ASan'
        return {'sanitizer':name,'severity':'fatal','kind':clean_message(line.lower()),'runtime_failure':True}, None
    return None


def span_blocks(lines):
    active = None
    consumed = 0
    for index, line in enumerate(lines):
        hit = identify(line)
        if hit is None:
            if active is None:
                continue
            first, header, location = active
            tool = header['sanitizer']
            if ((tool == 'TSan' and not header['runtime_failure'] and SEPARATOR.fullmatch(line))
                    or (tool in ('ASan', 'LSan') and ABORTING.fullmatch(line))):
                consumed = index + 1
                yield first, consumed, header, location
                active = None
            continue
        header, location = hit
        start = index - 1 if index > consumed and SEPARATOR.fullmatch(lines[index - 1]) else index
        if active is not None:
            first, previous, previous_location = active
            if (previous['kind']=='deadlysignal' and header['sanitizer']=='ASan' and
                    not any(re.search(r'ABORTING|Sanitizer: stack-overflow', content) for content in lines[first:index])):
                active = (first,header,location)
                continue
            yield first,start,previous,previous_location
        active = (start,header,location)
    if active is not None:
        first,header,location = active
        yield first,len(lines),header,location


def source_info(text):
    hits = [match for match in LOC.finditer(text) if re.search(r'[/\\.]',match['file'])]
    if not hits:
        return None
    match = hits[-1]
    return match, {'file':normalized_path(match['file']),'line':int(match['line'])}


def normalize_frame(payload):
    body = re.sub(r'^0x[\da-fA-F]+\s*','',payload)
    body = body.removeprefix('in ').strip()
    loc = source_info(body)
    if loc is not None:
        match, source = loc
        function = body[:match.start()].strip()
    else:
        module = MODULE.search(body)
        function = body[:module.start()].strip() if module else body
        source = {'file':normalized_path(module[1]),'line':None} if module else {'file':None,'line':None}
    function = ' '.join(HEX.sub('<address>',function).split())
    return {'function':function or '<unresolved>',**source}


def context(line):
    if m := re.match(r'\s*(?:previous )?((?:atomic )?(?:read|write)) of size ',line,re.I):
        return m[1].lower()
    low = line.lower()
    if 'created by' in low or re.search(r'^\s*thread t\d+ .*created ',low):
        return 'thread creation'
    if 'allocated by' in low:
        return 'allocation'
    if 'freed by' in low:
        return 'deallocation'
    if low.lstrip().startswith('mutex ') and 'created' in low:
        return 'mutex creation'
    return None


def stacks_and_summary(block):
    groups=[]
    current=[]
    role='trace'
    site=None
    for text in block:
        if match:=FRAME.fullmatch(text):
            current.append(normalize_frame(match[1]))
            continue
        if current:
            groups.append({'role':role,'frames':current})
            current=[]
            role='trace'
        if label:=context(text):
            role=label
        if text.startswith('SUMMARY: ') and (loc:=source_info(text)) is not None:
            match,source=loc
            tail=text[match.end():].strip().removeprefix('in ').strip()
            site={**source,'function':tail or None}
    if current:
        groups.append({'role':role,'frames':current})
    return groups,site


def fingerprint(header, location, groups, summary_site):
    if header['sanitizer']=='TSan' and header['kind']=='data race':
        # Race partners may swap which is described as the earlier access.
        if any(g['role'] in {'read','write','atomic read','atomic write'} for g in groups):
            summary_site=None
        groups=sorted(groups,key=lambda group:json.dumps(group,sort_keys=True))
    signature={'sanitizer':header['sanitizer'],'kind':header['kind'],'severity':header['severity'],
               'origin':location,'stacks':groups,'summary_site':summary_site}
    digest=hashlib.sha256(json.dumps(signature,sort_keys=True).encode()).hexdigest()
    return digest,signature


def matches_expected(expected, report, block):
    target, _, symbol = expected.partition(':')
    if target=='asan-heap':
        return (report['sanitizer'],report['kind'],report['runtime_failure']) == ('ASan','heap-buffer-overflow',False)
    if target=='ubsan-signed-overflow':
        return (report['sanitizer'],report['kind']) == ('UBSan','signed integer overflow')
    if target=='tsan-race':
        ident=re.compile(r'(?<![\w])'+re.escape(symbol)+r'(?![\w])')
        return (report['sanitizer'],report['kind'],report['runtime_failure']) == ('TSan','data race',False) and any(
            ident.search(line) for line in block)
    raise ValueError(f'unknown expectation {expected!r}')


def parse_run(tag, path, expected=()):
    data=path.read_bytes()
    lines=data.decode('utf-8',errors='backslashreplace').splitlines()
    unique={}
    total=Counter()
    runtime=0
    expectation_hits={name:[] for name in expected}
    for index,(start,end,header,location) in enumerate(span_blocks(lines),1):
        block=lines[start:end]
        groups,site=stacks_and_summary(block)
        digest,canonical=fingerprint(header,location,groups,site)
        total[header['sanitizer']]+=1
        runtime+=header['runtime_failure']
        if digest not in unique:
            unique[digest]={**header,'signature_sha256':digest,'signature':canonical,
                            'stack_groups':groups,'summary_site':site,'first_30_lines':block[:30], 'occurrences':[]}
        unique[digest]['occurrences'].append({'block':index,'first_line':start+1,'last_line':end})
        for expect in expected:
            if matches_expected(expect,header,block):
                expectation_hits[expect].append(index)
    return {'run':tag,'stderr':str(path),'stderr_bytes':len(data),'stderr_lines':len(lines),
            'stderr_sha256':hashlib.sha256(data).hexdigest(),'total_blocks':sum(total.values()),
            'distinct_reports':len(unique),'runtime_failure_blocks':runtime,'total_by_sanitizer':dict(total),
            'expectations':{name:{'matched':bool(blocks),'blocks':blocks} for name,blocks in expectation_hits.items()},
            'reports':list(unique.values())}


def read_mapping(items):
    grouped={}
    for item in items:
        key, equal, value = item.partition('=')
        if not equal or not TAG.fullmatch(key) or not value:
            raise ValueError(f'expected NAME=VALUE, got {item!r}')
        grouped.setdefault(key,[]).append(value)
    return grouped


def write_excerpts(destination, results):
    with destination.open('x',encoding='utf-8') as output:
        for result in results:
            for found in result['reports']:
                occurrence=found['occurrences'][0]
                output.write(f'[{result["run"]}] {found["sanitizer"]} {found["kind"]}, raw stderr '
                             f'lines {occurrence["first_line"]}–{occurrence["last_line"]}\n')
                output.write(''.join(f'{line}\n' for line in found['first_30_lines']))
                output.write('\n')


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--run',action='append',required=True,metavar='NAME=STDERR.txt')
    cli.add_argument('--expect',action='append',default=[],metavar='NAME=CONTROL[:SYMBOL]')
    cli.add_argument('--excerpts',type=Path,help='create a raw first-30-lines text excerpt file')
    args=cli.parse_args()
    try:
        names=read_mapping(args.run)
        wants=read_mapping(args.expect)
        if set(wants)-set(names) or any(len(paths)!=1 for paths in names.values()):
            raise ValueError('each run name must be unique, and every expected control must name an input')
        for expectations in wants.values():
            if len(set(expectations))!=len(expectations):
                raise ValueError('duplicate expectation')
            for entry in expectations:
                if entry not in {'asan-heap','ubsan-signed-overflow'} and not re.fullmatch(r'tsan-race:[A-Za-z_][\w:]*',entry):
                    raise ValueError(f'invalid control expectation {entry!r}')
        all_runs=[parse_run(tag,Path(paths[0]),wants.get(tag,[])) for tag,paths in names.items()]
        if args.excerpts is not None:
            write_excerpts(args.excerpts,all_runs)
        pass_=all(expect['matched'] for run in all_runs for expect in run['expectations'].values())
        different={rep['signature_sha256'] for run in all_runs for rep in run['reports']}
        print(json.dumps({'total_report_blocks':sum(run['total_blocks'] for run in all_runs),
                          'distinct_reports_across_runs':len(different),'controls_match':pass_,
                          'runs':all_runs},indent=2))
        return 0 if pass_ else 1
    except (OSError,ValueError) as error:
        cli.exit(2,f'Sanitizer readback failed: {error}\n')


if __name__=='__main__':
    raise SystemExit(main())
