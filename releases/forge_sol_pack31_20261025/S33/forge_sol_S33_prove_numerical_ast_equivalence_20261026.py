"""Prove the post-validation edit changed only CLI and dependency lookup metadata."""
import ast
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
OLD = BASE / 'forge_sol_S33_sprt_planner_prefreeze_cli_v2_20261026.py'
NEW = BASE / 'forge_sol_S33_sprt_planner_20261026.py'
OLD_SHA256 = 'b04af9f74b0ffc7cb9b9e58a04ac4cf02efff43e4d801991dfc11324a2e2f194'
METADATA_ASSIGNMENTS = {'S06_DEPENDENCY','_S06_FILENAME','_S06_ADJACENT','S06_DEPENDENCY_SHA256'}


def strip_allowed(source):
    tree = ast.parse(source)
    kept,removed = [],[]
    for node in tree.body:
        reason = None
        if isinstance(node,ast.FunctionDef) and node.name=='main':
            reason = 'CLI main() only'
        elif isinstance(node,ast.If) and ast.unparse(node.test)=="__name__ == '__main__'":
            reason = 'CLI entrypoint only'
        elif isinstance(node,ast.Assign) and all(isinstance(x,ast.Name) and x.id in METADATA_ASSIGNMENTS for x in node.targets):
            reason = 'S06 dependency selector/hash metadata only'
        elif isinstance(node,ast.Import) and len(node.names)==1 and node.names[0].name=='hashlib':
            reason = 'S06 dependency metadata hashing import only'
        elif (isinstance(node,ast.If) and ast.unparse(node.test)==
              'S06_DEPENDENCY.is_file() and hashlib.sha256(S06_DEPENDENCY.read_bytes()).hexdigest() != S06_DEPENDENCY_SHA256'):
            reason = 'S06 dependency metadata hash verification only'
        if reason:
            removed.append({'reason':reason,'node':ast.unparse(node)})
        else:
            kept.append(node)
    tree.body = kept
    canonical = ast.dump(tree,annotate_fields=True,include_attributes=False)
    return tree,canonical,removed


def main():
    old_bytes,new_bytes = OLD.read_bytes(),NEW.read_bytes()
    assert hashlib.sha256(old_bytes).hexdigest()==OLD_SHA256
    old,old_ast,old_removed = strip_allowed(old_bytes.decode())
    new,new_ast,new_removed = strip_allowed(new_bytes.decode())
    assert old_ast==new_ast, 'non-CLI/non-dependency AST changed'
    old_funcs = {x.name:ast.dump(x,include_attributes=False) for x in old.body if isinstance(x,ast.FunctionDef)}
    new_funcs = {x.name:ast.dump(x,include_attributes=False) for x in new.body if isinstance(x,ast.FunctionDef)}
    assert old_funcs==new_funcs
    result = {'status':'PASS','old_source_sha256':OLD_SHA256,
              'new_source_sha256':hashlib.sha256(new_bytes).hexdigest(),
              'canonical_retained_AST_sha256':hashlib.sha256(old_ast.encode()).hexdigest(),
              'retained_function_names':sorted(old_funcs),'retained_function_count':len(old_funcs),
              'retained_AST_identical':True,'numerical_functions_constants_RNG_unchanged':True,
              'old_removed_nodes':old_removed,'new_removed_nodes':new_removed,
              'scope':'Remove only main(), __name__ entrypoint and explicit S06 dependency selector/hash metadata; compare every remaining AST node exactly.',
              'validation_reuse':'The six 20000-run receipts remain bound to old_source_sha256; this proof binds their identical numerical model to new_source_sha256 without rerunning MC.'}
    output = BASE / 'forge_sol_S33_numerical_ast_equivalence_20261026.json'
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','old_source_sha256','new_source_sha256','canonical_retained_AST_sha256','retained_function_count')}))


if __name__=='__main__':
    main()
