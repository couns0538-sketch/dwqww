# run_parallel.ps1 - start several pinned Python steps side by side and wait for all (PowerShell 5.1, ASCII only).
#   -Plan "name|mask|python arguments" separated by ';'   (arguments must not contain ';' or '|')
# Each step runs through pin.ps1 on its own mask; its console output goes to out\logs\<name>.console.txt.
param([Parameter(Mandatory = $true)][string]$Plan)
$ErrorActionPreference = 'Continue'
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.ProcessorAffinity = [IntPtr]0x707F
$me.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::BelowNormal
$J = 'D:\forge_jobs_20261110\fable4cpu'
$Tools = "$J\repo\fable_cpu_speed\tools"
$ps = "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe"
if (-not (Test-Path -LiteralPath "$J\out\logs")) { [void](New-Item -ItemType Directory -Path "$J\out\logs") }
$running = @()
foreach ($e in ($Plan -split ';')) {
    if (-not $e.Trim()) { continue }
    $f = $e.Split('|')
    $name = $f[0].Trim(); $mask = $f[1].Trim(); $al = $f[2].Trim().Replace('"', '\"')
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $ps
    $psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -File $Tools\pin.ps1 -Mask $mask -Exe C:\Python315\python.exe -ArgLine `"-I -B $al`" -OutFile $J\out\logs\$name.console.txt"
    $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true
    $running += @{ p = [System.Diagnostics.Process]::Start($psi); name = $name; mask = $mask }
    [Console]::Out.WriteLine("started $name on mask $mask")
}
foreach ($r in $running) {
    $r.p.WaitForExit()
    $last = ''
    try { $last = @(Get-Content "$J\out\logs\$($r.name).console.txt" -Tail 1) -join '' } catch { }
    [Console]::Out.WriteLine("ended $($r.name) exit $($r.p.ExitCode) :: $last")
}
[Console]::Out.WriteLine('all steps ended')
