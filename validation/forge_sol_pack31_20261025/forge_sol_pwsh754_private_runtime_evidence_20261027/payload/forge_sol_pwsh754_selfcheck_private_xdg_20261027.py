from pathlib import Path
import os,subprocess,json,hashlib,time,shutil
r=Path('/tmp/forge_sol_pwsh754_preflight_20261027');runtime=r/'runtime'
work=r/'selfcheck_private_xdg_work';work.mkdir(mode=0o700,exist_ok=False)
for name in ('tmp','cache','data','config'):(work/name).mkdir(mode=0o700)
script=r'''$ErrorActionPreference='Stop'
if ($PSVersionTable.PSVersion.ToString() -ne '7.5.4') { throw 'Unexpected portable runtime version' }
[ordered]@{
 PSVersionTable=$PSVersionTable
 Framework=[System.Runtime.InteropServices.RuntimeInformation]::FrameworkDescription
 Architecture=[System.Runtime.InteropServices.RuntimeInformation]::ProcessArchitecture.ToString()
 Culture=[System.Globalization.CultureInfo]::GetCultureInfo('en-US').DisplayName
 SHA256=[System.Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData([System.Text.Encoding]::UTF8.GetBytes('forge-portable-runtime')))
 LanguageMode=$ExecutionContext.SessionState.LanguageMode.ToString()
} | ConvertTo-Json -Depth 6 -Compress
'''
(r/'forge_sol_pwsh754_selfcheck_private_xdg_command_20261027.ps1').write_text(script)
changes={'POWERSHELL_TELEMETRY_OPTOUT':'1','POWERSHELL_UPDATECHECK':'Off','PSModuleAnalysisCachePath':str(work/'cache/ModuleAnalysisCache'),'DOTNET_EnableDiagnostics':'0','DOTNET_CLI_TELEMETRY_OPTOUT':'1','TMPDIR':str(work/'tmp'),'XDG_CACHE_HOME':str(work/'cache'),'XDG_DATA_HOME':str(work/'data'),'XDG_CONFIG_HOME':str(work/'config')}
env=os.environ.copy();env.update(changes);assert env.get('HOME')==os.environ.get('HOME')
targets=[Path.home()/x for x in ('.cache/powershell','.config/powershell','.local/share/powershell','.dotnet')]
def snapshot():
 rows=[]
 for p in targets:
  present=p.exists();row={'path':str(p),'exists':present}
  if present:
   s=p.stat();row.update(mode=s.st_mode,size=s.st_size,mtime_ns=s.st_mtime_ns)
  rows.append(row)
 return rows
before=snapshot();trace=r/'forge_sol_pwsh754_selfcheck_private_xdg_file_trace_20261027.log'
argv=[shutil.which('strace'),'-f','-qq','-yy','-e','trace=file','-o',str(trace),str(runtime/'pwsh'),'-NoLogo','-NoProfile','-NonInteractive','-Command',script]
s=time.monotonic();p=subprocess.run(argv,cwd=work,env=env,capture_output=True,timeout=30)
(r/'forge_sol_pwsh754_selfcheck_private_xdg_20261027.stdout').write_bytes(p.stdout);(r/'forge_sol_pwsh754_selfcheck_private_xdg_20261027.stderr').write_bytes(p.stderr)
record={'argv':argv,'cwd':str(work),'returncode':p.returncode,'elapsed_seconds':time.monotonic()-s,'environment_overrides_only':changes,'HOME_unchanged':env.get('HOME')==os.environ.get('HOME'),'user_config_before':before,'user_config_after':snapshot(),'pwsh_sha256':hashlib.sha256((runtime/'pwsh').read_bytes()).hexdigest(),'strace_sha256':hashlib.sha256(Path(shutil.which('strace')).read_bytes()).hexdigest(),'trace':str(trace),'stdout':str(r/'forge_sol_pwsh754_selfcheck_private_xdg_20261027.stdout'),'stderr':str(r/'forge_sol_pwsh754_selfcheck_private_xdg_20261027.stderr'),'project_scripts_run':0}
if p.returncode==0:
 value=json.loads(p.stdout);assert value['Architecture']=='X64' and value['SHA256']==hashlib.sha256(b'forge-portable-runtime').hexdigest().upper();record['actual_selfcheck']=value
record['user_config_metadata_unchanged']=record['user_config_before']==record['user_config_after']
(r/'forge_sol_pwsh754_selfcheck_private_xdg_receipt_20261027.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'returncode':p.returncode,'elapsed_seconds':record['elapsed_seconds'],'HOME_unchanged':record['HOME_unchanged'],'user_config_metadata_unchanged':record['user_config_metadata_unchanged'],'stdout':p.stdout.decode(errors='replace'),'stderr':p.stderr.decode(errors='replace')}));assert p.returncode==0
