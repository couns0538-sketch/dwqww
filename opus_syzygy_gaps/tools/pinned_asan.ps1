# pinned_asan.ps1 -Tag <san tag> -Exe <exe> -ArgLine '<args>' [-Log <file>] [-OutFile <file> -ErrFile <file>] - as pinned.ps1, with the MSVC environment of out\san\<tag>\vcenv.txt,
# so that an ASan exe finds its runtime and a program started from here (a python driver) passes it on. ASAN_OPTIONS as in run_san.ps1. TB_HEAP=1 only with -Heap (tb_root: exact-size heap copies of the tables).
param(
    [Parameter(Mandatory = $true)][string]$Tag,
    [Parameter(Mandatory = $true)][string]$Exe,
    [string]$ArgLine = '',
    [string]$Log = '',
    [string]$OutFile = '',
    [string]$ErrFile = '',
    [switch]$Heap
)
. 'D:\forge_jobs_20261107\opus1\env.ps1'
$x = [Diagnostics.Process]::GetCurrentProcess()
if ([int64]$x.ProcessorAffinity -ne 0xF000 -or $x.PriorityClass -ne [Diagnostics.ProcessPriorityClass]::Idle) { Write-Output 'FAIL pin did not read back'; exit 90 }
$dir = Join-Path $JobOut "san\$Tag"
foreach ($l in Get-Content (Join-Path $dir 'vcenv.txt')) { $i = $l.IndexOf('='); if ($i -gt 0) { Set-Item -Path ('env:' + $l.Substring(0, $i)) -Value $l.Substring($i + 1) } }
$env:TEMP = $JobTmp; $env:TMP = $JobTmp
$env:ASAN_OPTIONS = 'halt_on_error=1:detect_leaks=0'
if ($Heap) { $env:TB_HEAP = '1' }
$psi = New-Object Diagnostics.ProcessStartInfo
$psi.FileName = 'cmd.exe'
$psi.UseShellExecute = $false
$psi.WorkingDirectory = (Get-Location).Path
if ($OutFile) {
    $errTarget = if ($ErrFile) { $ErrFile } else { 'NUL' }
    $psi.Arguments = '/d /c ""' + $Exe + '" ' + $ArgLine + ' > "' + $OutFile + '" 2> "' + $errTarget + '""'
} elseif ($Log) {
    $psi.Arguments = '/d /c ""' + $Exe + '" ' + $ArgLine + ' > "' + $Log + '" 2>&1"'
} else {
    $psi.Arguments = '/d /c ""' + $Exe + '" ' + $ArgLine + '"'
}
$p = [Diagnostics.Process]::Start($psi)
$p.WaitForExit()
exit $p.ExitCode
