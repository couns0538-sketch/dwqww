param([int]$Cpu=3,[Parameter(Mandatory=$true)][string]$Name)
$ErrorActionPreference='Stop'
if ($Name -notmatch '^[a-z0-9_-]+$') { throw 'Invalid name' }
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='Idle'
$out='D:\a14\evidence\r14\parser-'+$Name+'.log'
if (Test-Path -LiteralPath $out) { throw 'Existing evidence' }
& D:\a14\runtime\python\python.exe -I -B D:\a14\tools\r14_parser_probe.py --cpu $Cpu *> $out
$code=$LASTEXITCODE
Get-Content -LiteralPath $out
exit $code
