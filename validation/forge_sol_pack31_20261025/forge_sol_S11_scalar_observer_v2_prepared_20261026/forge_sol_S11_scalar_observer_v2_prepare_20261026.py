#!/usr/bin/env python3
"""One-off SOURCE-ONLY successor creation; never launches compiler or engine."""
from pathlib import Path
import ast
import hashlib
import json

HERE = Path(__file__).resolve().parent
ORIGINAL = Path('/tmp/forge_sol_S11_native_prep_20261026/forge_sol_S11_scalar_parity_20261026.py')
ORIGINAL_SHA = '31f475c01580d376e3f5a28debe3f37651fff7c426ca1a12d20c77832b263ae5'

FUNCTION = '''def verify_disassembly(text,mode):
    if mode not in {'scalar','avx2'}:raise ValueError('unknown required ISA mode')
    symbol=None;scoped=[];evaluate=[]
    for line in text.splitlines():
        match=re.match(r'^\\s*[0-9a-fA-F]+\\s+<(.+)>:\\s*$',line)
        if match:symbol=match[1];continue
        match=re.match(r'^\\s*[0-9a-fA-F]+:\\s+([a-zA-Z][a-zA-Z0-9_.]*)\\s*(.*?)\\s*$',line)
        if match and symbol and symbol.startswith('forge::nnue::'):
            row=(symbol,match[1].lower(),match[2]);scoped.append(row)
            if symbol.startswith('forge::nnue::evaluate('):evaluate.append(row)
    if not scoped or not evaluate:raise ValueError('no actual demangled NNUE/evaluate disassembly')
    if any(re.fullmatch(r'vf(?:n)?m(?:add|sub)[a-z0-9]*',op) for _,op,_ in scoped):raise ValueError('NNUE contains FMA')
    if any(re.search(r'%?zmm\\d+',args) for _,_,args in scoped):raise ValueError('unsupported AVX512 width')
    allowed_stores=0;allowed_selections=0
    if mode=='scalar':
        for _,op,args in evaluate:
            # Numerical scalar inference may contain bit-preserving compiler
            # initialization stores. This enumerates ONLY the observed opcode
            # and YMM-to-RSP forms; unknown wide operations still fail closed.
            wide=bool(re.search(r'%?(?:ymm|zmm)\\d+',args))
            if wide:
                if (op!='vmovdqa' or not re.fullmatch(r'%ymm\\d+\\s*,\\s*(?:0x[0-9a-fA-F]+)?\\(%rsp\\)',args)):
                    raise ValueError('scalar inference uses unsupported packed width or transfer operands')
                allowed_stores+=1
            registers=re.findall(r'%xmm(\\d+)',args)
            zero=(op in {'xorps','xorpd','vxorps','vxorpd'} and len(registers)>=2 and len(set(registers))==1)
            # VBLENDVPS selects existing bits, performing no floating arithmetic.
            # Permit only its reviewed four-XMM-register form, never YMM/memory.
            selection=(op=='vblendvps' and not wide and bool(re.fullmatch(
                r'%xmm\\d+\\s*,\\s*%xmm\\d+\\s*,\\s*%xmm\\d+\\s*,\\s*%xmm\\d+',args)))
            if selection:allowed_selections+=1
            packed=(op.endswith(('ps','pd','ph')) and not (op.startswith(('mov','vmov')) or zero or selection))
            if (packed or re.fullmatch(r'v?(?:add|sub|mul|div|min|max|sqrt|rcp|rsqrt)sd',op)
                or re.search(r'%st(?:\\(|\\b)',args) or re.match(r'f(?:ld|st|add|mul|sub|div|com|ucom|xch|sqrt)',op)):
                raise ValueError('scalar inference contains packed SSE fallback, non-float32 or x87 arithmetic')
        if not any(re.fullmatch(r'v?mulss',op) for _,op,_ in evaluate) or not any(re.fullmatch(r'v?addss',op) for _,op,_ in evaluate):raise ValueError('scalar float32 arithmetic not demonstrated')
    else:
        if not any(op in {'vmulps','vaddps'} and re.search(r'%?ymm\\d+',args) for _,op,args in evaluate):raise ValueError('actual AVX2 packed inference not demonstrated')
    return {'mode':mode,'NNUE_instructions':len(scoped),'evaluate_instructions':len(evaluate),'FMA_count':0,'ISA_proven':True,
        'ISA_observer_version':2,'ISA_scope':'scalar float32 numerical arithmetic with enumerated bit-preserving transfers/selections' if mode=='scalar' else 'AVX2 packed float32 inference',
        'allowed_YMM_stack_store_count':allowed_stores,'allowed_XMM_selection_count':allowed_selections,
        'scalar_FP32_mul_count':sum(bool(re.fullmatch(r'v?mulss',op)) for _,op,_ in evaluate),
        'scalar_FP32_add_count':sum(bool(re.fullmatch(r'v?addss',op)) for _,op,_ in evaluate)}
'''


def main():
    assert hashlib.sha256(ORIGINAL.read_bytes()).hexdigest() == ORIGINAL_SHA
    original = ORIGINAL.read_text()
    tree = ast.parse(original)
    target = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == 'verify_disassembly')
    lines = original.splitlines(True)
    modified = ''.join(lines[:target.lineno-1]) + FUNCTION + ''.join(lines[target.end_lineno:])
    out = HERE / 'forge_sol_S11_scalar_parity_observer_v2_20261026.py'
    if out.exists():raise FileExistsError('sealed/new named output required')
    out.write_text(modified)
    before = {node.name: ast.dump(node, include_attributes=False) for node in tree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
    after = {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(modified).body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
    assert set(before) == set(after)
    changed = [name for name in before if before[name] != after[name]]
    assert changed == ['verify_disassembly'], changed
    receipt = {'scope':'SOURCE_ONLY_NO_NATIVE','original':str(ORIGINAL),'original_sha256':ORIGINAL_SHA,
               'successor':out.name,'successor_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
               'only_changed_definition_AST':changed,'unchanged_definition_count':len(before)-1,
               'engine_code_changes':0,'compiler_flag_changes':0,'native_retries':0}
    (HERE/'forge_sol_S11_scalar_observer_v2_source_receipt_20261026.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__ == '__main__':main()
