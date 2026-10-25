#!/usr/bin/env python3
"""Check NNUE rounding and 256-bit output, including outlined evaluation helpers."""
from __future__ import annotations
import argparse,json,re,subprocess,sys
HEADER=re.compile(r'^\s*[0-9a-fA-F]+ <(.+)>:\s*$')
FUSED=re.compile(r'^vf(?:n)?m(?:add|sub)[a-z0-9]*\b',re.I)
CMP=re.compile(r'^vcmp([a-z_]*)ps\s+(?:\$(0x[0-9a-f]+|\d+),)?%ymm(\d+),%ymm(\d+),%k([0-7])$')
ZERO=re.compile(r'^(?:vxorps|vpxor|vpxord|vpxorq)\s+%[xy]mm(\d+),%[xy]mm\1,%[xy]mm\1$')

def instruction(line):
    m=re.match(r'^\s*[0-9a-fA-F]+:\s+(.+)$',line)
    if not m:return None
    value=re.sub(r'^(?:[0-9a-fA-F]{2}\s+)+','',m.group(1))
    return re.sub(r'^\{evex\}\s*','',value.split('#',1)[0].strip())

def symbols(assembly):
    result=[];current=None
    for line in assembly.splitlines():
        header=HEADER.match(line)
        if header:
            current={'name':header.group(1),'instructions':[]};result.append(current)
        elif current is not None:
            ins=instruction(line)
            if ins:current['instructions'].append(ins)
    return result

def vector_destination(ins):
    fields=ins.split(None,1)
    if len(fields)!=2:return None
    m=re.fullmatch(r'%[xyz]mm(\d+)(?:\{.*)?',fields[1].rsplit(',',1)[-1])
    return m.group(1) if m else None

def update_zeroes(known,ins):
    dest=vector_destination(ins)
    if dest is not None:
        if ZERO.fullmatch(ins):known.add(dest)
        else:known.discard(dest)

def mask_clamp(insns):
    zeroes=set()
    for index,ins in enumerate(insns):
        if re.match(r'^(?:callq?|retq?|j[a-z]+)\b',ins):zeroes.clear()
        match=CMP.fullmatch(ins)
        if match:
            pred,imm,zero,value,mask=match.groups()
            valid_predicate=(pred in {'gt','gt_os','gt_oq','nle','nle_us','nle_uq'} and imm is None) if pred else (imm is not None and int(imm,0) in {6,14,22,30})
            if valid_predicate and mask!='0' and zero in zeroes and value not in zeroes:
                live_zeroes=set(zeroes)
                for after in insns[index+1:]:
                    if re.search(r',%k'+mask+r'$',after):break
                    source=after.rsplit(',',1)[0]
                    uses_value=bool(re.search(r'%ymm'+value+r'(?!\d)',source))
                    if uses_value and '{%k'+mask+'}{z}' in after:return 'mask-zero'
                    blend=re.fullmatch(r'vblendmps\s+%ymm(\d+),%ymm(\d+),%ymm\d+\{%k'+mask+r'\}',after)
                    if blend and blend.group(1)==value and blend.group(2) in live_zeroes:return 'mask-blend'
                    if vector_destination(after) in (value,zero):break
                    if re.match(r'^(?:callq?|retq?|j[a-z]+)\b',after):break
                    update_zeroes(live_zeroes,after)
        update_zeroes(zeroes,ins)
    return None

def output_contract(insns):
    for op in ('vminps','vmulps','vaddps'):
        if not any(re.match(r'^'+op+r'\b',ins) and '%ymm' in ins for ins in insns):return None
    if any(re.match(r'^vmaxps\b',ins) and '%ymm' in ins for ins in insns):return 'vmaxps'
    return mask_clamp(insns)

def check_assembly(assembly):
    rows=[row for row in symbols(assembly) if row['name'].startswith('forge::nnue::')]
    public=[row for row in rows if row['name'].startswith('forge::nnue::evaluate(')]
    if not public:raise ValueError('public NNUE evaluate symbol not found')
    fused=[{'symbol':row['name'],'instruction':ins} for row in rows for ins in row['instructions'] if FUSED.match(ins)]
    if fused:raise ValueError('fused arithmetic in scoped NNUE code: '+json.dumps(fused))
    output=[row for row in rows if re.match(r'^forge::nnue::(?:\(anonymous namespace\)::)?evaluate(?:_values)?\(',row['name'])]
    qualified=[{'symbol':row['name'],'clamp':clamp} for row in output if (clamp:=output_contract(row['instructions']))]
    if not qualified:raise ValueError('NNUE output lacks 256-bit clamp/min/multiply/add in public or outlined evaluate body')
    return {'status':'PASS','checker_version':3,'fma_count':0,'scanned_symbols':[row['name'] for row in rows],
            'qualified_output':qualified,'scope':'All demangled forge::nnue:: symbol bodies, including anonymous helpers and compiler clones'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('object',help='NNUE object or unstripped executable');args=p.parse_args()
    result=subprocess.run(['objdump','-d','-C','--no-show-raw-insn',args.object],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    if result.returncode:raise ValueError('objdump failed with exit '+str(result.returncode)+': '+result.stderr.decode('utf-8','replace'))
    print(json.dumps(check_assembly(result.stdout.decode('utf-8','strict')),sort_keys=True))
    return 0
if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,OSError) as exc:
        print('FAIL: '+str(exc),file=sys.stderr);sys.exit(1)
