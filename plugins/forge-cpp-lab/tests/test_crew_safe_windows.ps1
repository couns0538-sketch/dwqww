#requires -Version 5.1
# Runtime regression; authored on Linux, Windows execution UNVERIFIED.
[CmdletBinding()]
param([string]$Python, [int]$SpareCpu=-1, [string]$EvidenceDirectory)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if ($env:OS -ne 'Windows_NT') { throw 'Windows test required' }
$launcher=Join-Path $PSScriptRoot '..\skills\grok-pc-safe-run\scripts\Invoke-GrokPcSafeRun.ps1'
. $launcher
function Expect-Refused([scriptblock]$Action, [string]$Pattern) {
    $refused=$false; try {& $Action | Out-Null} catch {if ($Pattern -and $_.Exception.Message -notmatch $Pattern) {throw}; $refused=$true}
    if (-not $refused) {throw 'Expected refusal'}
}
foreach($path in @('C:\work\x','D:relative','\\server\share\x','D:\npt\x','D:\nnue-pytorch\x','D:\gates\x','D:\work\queue.txt','D:\work\queue_state.json','D:\work\STOP.txt','D:\work\PAUSE','D:\work\x:stream','D:\work\..\x')) {
    Expect-Refused {Assert-DPath $path @('D:\production-data')}
}
Expect-Refused {Assert-DPath 'D:\production-data\x' @('D:\production-data')}
Expect-Refused {Assert-DPath 'D:\shared' @('D:\shared\production')} 'ancestor'
Expect-Refused {Assert-SafeDisk 20000 0}
Expect-Refused {Invoke-GrokPcSafeJob 'D:\unused\job.json' @()}
if (-not $Python -or -not $EvidenceDirectory -or $SpareCpu -lt 0) {throw 'Provide D: Python, new D: evidence directory and explicitly spare CPU for native tests'}
$null=Assert-DPath $Python @('D:\npt','D:\gates')
$null=Assert-DPath $EvidenceDirectory @('D:\npt','D:\gates')
if (Test-Path -LiteralPath $EvidenceDirectory) {throw 'Evidence must be new'}
Assert-SafeDisk 32768 1048576
$null=New-Item -ItemType Directory -Path $EvidenceDirectory
$probe=Join-Path $EvidenceDirectory 'owned_probe.py'
@'
import argparse,ctypes,json,os,sys
p=argparse.ArgumentParser();p.add_argument('--threads',type=int,required=True);p.add_argument('--exit-code',type=int,default=0);a=p.parse_args()
k=ctypes.windll.kernel32;k.GetCurrentProcess.restype=ctypes.c_void_p
process=k.GetCurrentProcess();k.GetPriorityClass.argtypes=[ctypes.c_void_p]
mask=ctypes.c_size_t();system=ctypes.c_size_t()
k.GetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_size_t),ctypes.POINTER(ctypes.c_size_t)]
if not k.GetProcessAffinityMask(process,ctypes.byref(mask),ctypes.byref(system)):raise ctypes.WinError()
print(json.dumps({'priority':k.GetPriorityClass(process),'mask':mask.value,'threads':a.threads,'TEMP':os.environ['TEMP']}))
print('benign native stderr',file=sys.stderr)
raise SystemExit(a.exit_code)
'@ | Set-Content -LiteralPath $probe -Encoding UTF8
$self=[Diagnostics.Process]::GetCurrentProcess();$beforeMask=$self.ProcessorAffinity;$beforePriority=$self.PriorityClass
foreach($exitCode in @(0,7)) {
    $out=Join-Path $EvidenceDirectory "run_$exitCode"
    $job=[ordered]@{schema=1;executable=$Python;executable_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $Python).Hash;arguments=@($probe,'--threads','1','--exit-code',[string]$exitCode);working_directory=$EvidenceDirectory;output_directory=$out;read_paths=@($Python,$probe);write_paths=@($out);logical_cpus=@($SpareCpu);worker_threads=1;minimum_free_mib=32768;required_bytes=1048576}
    $manifest=Join-Path $EvidenceDirectory "manifest_$exitCode.json"
    $job | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifest -Encoding UTF8
    $observed=Invoke-GrokPcSafeJob $manifest @('D:\npt','D:\gates')
    if ($observed -ne $exitCode) {throw "Wrong native exit: $observed"}
    $receipt=Get-Content -LiteralPath (Join-Path $out 'result.json') -Raw | ConvertFrom-Json
    if($receipt.native_exit_code -ne $exitCode -or $receipt.capture_errors.Count -ne 0) {throw 'Exit receipt mismatch'}
    $data=Get-Content -LiteralPath (Join-Path $out 'stdout.log') -Raw | ConvertFrom-Json
    if($data.priority -ne 64 -or $data.mask -ne ([int64]1 -shl $SpareCpu) -or $data.threads -ne 1 -or $data.TEMP -notlike 'D:\*') {throw 'Child scheduling/temp mismatch'}
    if ((Get-Content -LiteralPath (Join-Path $out 'stderr.log') -Raw) -notmatch 'benign native stderr') {throw 'Stderr missing'}
    Expect-Refused {Invoke-GrokPcSafeJob $manifest @('D:\npt','D:\gates')}
    $bad=$job | ConvertTo-Json -Depth 5 | ConvertFrom-Json
    $bad.output_directory=Join-Path $EvidenceDirectory ('rejected_'+$exitCode);$bad.write_paths=@($bad.output_directory)
    $bad.worker_threads=4;$bad.arguments=@($probe,'--threads','4');Expect-Refused {Test-SafeJob $bad @('D:\npt','D:\gates')} 'worker_threads'
    $bad.worker_threads=1;$bad.arguments=@($probe,'--threads','4');Expect-Refused {Test-SafeJob $bad @('D:\npt','D:\gates')} 'Thread argument'
    $bad.arguments=@('..\custom-production\evil.py','--threads','1');Expect-Refused {Test-SafeJob $bad @('D:\npt','D:\gates')} 'Relative path-like'
    $bad.arguments=@('--input=D:\undeclared\x.txt','--threads','1');Expect-Refused {Test-SafeJob $bad @('D:\npt','D:\gates')} 'not within declared'
    $bad.arguments=@('@relative.rsp','--threads','1');Expect-Refused {Test-SafeJob $bad @('D:\npt','D:\gates')} 'Absolute D:'
}
$self.Refresh();if($self.ProcessorAffinity -ne $beforeMask -or $self.PriorityClass -ne $beforePriority) {throw 'Launcher scheduling not restored'}
'PASS: refusal, native stderr/exit, D temp, Idle/affinity and restoration; originals retained.'
