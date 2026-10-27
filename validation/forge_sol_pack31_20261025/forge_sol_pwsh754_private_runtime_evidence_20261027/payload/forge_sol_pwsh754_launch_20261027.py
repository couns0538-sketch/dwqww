#!/usr/bin/env python3
"""Launch the private, verified runtime with no profile or user-cache writes.
Pass only -Command/-File and their arguments; NoProfile/NonInteractive are forced.
HOME and PATH are inherited unchanged. No global installation is performed.
"""
from pathlib import Path
import hashlib,os,sys
root=Path(__file__).resolve().parent
program=root/'runtime/pwsh'
expected='e0c6c82153c6655a842602be4ea7607d4e3a137b1956668ef44d1b1b7bf939b8'
if hashlib.sha256(program.read_bytes()).hexdigest()!=expected:raise SystemExit('Portable pwsh identity changed')
work=root/'launch_work'
for p in (work,work/'tmp',work/'cache',work/'data',work/'config'):
    if p.is_symlink():raise SystemExit('Refusing symlinked private work path')
    p.mkdir(mode=0o700,exist_ok=True)
env=os.environ.copy()
env.update({'POWERSHELL_TELEMETRY_OPTOUT':'1','POWERSHELL_UPDATECHECK':'Off','PSModuleAnalysisCachePath':str(work/'cache/ModuleAnalysisCache'),'DOTNET_EnableDiagnostics':'0','DOTNET_CLI_TELEMETRY_OPTOUT':'1','TMPDIR':str(work/'tmp'),'XDG_CACHE_HOME':str(work/'cache'),'XDG_DATA_HOME':str(work/'data'),'XDG_CONFIG_HOME':str(work/'config')})
assert env.get('HOME')==os.environ.get('HOME') and env.get('PATH')==os.environ.get('PATH')
os.execve(program,[str(program),'-NoLogo','-NoProfile','-NonInteractive',*sys.argv[1:]],env)
