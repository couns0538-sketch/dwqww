"""Small AST/provenance audit only; no compiler or engine invocation."""
from pathlib import Path
import ast
import hashlib
import json

ROOT=Path(__file__).resolve().parent


def parts(path):
    text=path.read_text();lines=text.splitlines(keepends=True)
    return {node.name:''.join(lines[node.lineno-1:node.end_lineno]) for node in ast.parse(text).body
            if isinstance(node,(ast.FunctionDef,ast.ClassDef))}


def main():
    out={'schema':'forge.S12.source_only_audit.v1','native_compiler_engine_invocations':0,
         'python_asts':{},'frozen_input_bytes':{},'unchanged_transport_function_bytes':{}}
    for path in sorted(ROOT.rglob('*.py')):
        ast.parse(path.read_text(),filename=str(path));out['python_asts'][path.relative_to(ROOT).as_posix()]='PASS'
    checks={
        'inputs/forge_sol_S12_lazyacc_native_regression_20261026.cpp':
            '/tmp/forge_sol_S12_delivery_prepared_20261026/forge_sol_S12_lazyacc_native_regression_20261026.cpp',
        'inputs/forge_sol_S12_benchcounter_helper_20261026.cpp':
            '/tmp/forge_sol_S12_benchcounter_prep_20261026/generated_final/forge_sol_S12_benchcounter_helper_20261026.cpp',
        'inputs/forge_sol_S12_benchcounter_source_binding_20261026.json':
            '/tmp/forge_sol_S12_benchcounter_prep_20261026/generated_final/forge_sol_S12_benchcounter_source_binding_20261026.json',
        'inputs/forge_sol_S12_benchcounter_records_20261026.py':
            '/tmp/forge_sol_S12_benchcounter_prep_20261026/forge_sol_S12_benchcounter_records_20261026.py'}
    for relative,old in checks.items():
        a,b=(ROOT/relative).read_bytes(),Path(old).read_bytes()
        if a!=b:raise ValueError('frozen original helper/parser changed: '+relative)
        out['frozen_input_bytes'][relative]={'PASS_IDENTICAL':True,'original':old,'sha256':hashlib.sha256(a).hexdigest()}
    old=Path('/tmp/forge_sol_S11_native_prep_20261026/forge_sol_S11_scalar_parity_20261026.py')
    new=ROOT/'forge_sol_S12_alias_transport_20261027.py'
    a,b=parts(old),parts(new)
    for name in ('sha','verify_sealed_input','load_owned_module'):
        if a[name]!=b[name]:raise ValueError('unchanged transport function changed: '+name)
        out['unchanged_transport_function_bytes'][name]=hashlib.sha256(a[name].encode()).hexdigest()
    constants={node.targets[0].id:ast.literal_eval(node.value) for node in ast.parse(new.read_text()).body
               if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)
               and node.targets[0].id=='ORACLE_SHA'}
    if constants['ORACLE_SHA']!=hashlib.sha256((ROOT/'forge_sol_S12_alias_oracle_20261027.cpp').read_bytes()).hexdigest():
        raise ValueError('alias producer hash/transport binding differs')
    output=ROOT/'forge_sol_S12_source_only_audit_20261027.json'
    output.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'AST_files':len(out['python_asts']),'frozen_CPP_or_parser_inputs':len(checks),
                      'unchanged_transport_functions':len(out['unchanged_transport_function_bytes']),'native_runs':0}))


if __name__=='__main__':main()
