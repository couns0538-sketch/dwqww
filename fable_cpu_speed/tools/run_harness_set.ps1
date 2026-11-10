# run_harness_set.ps1 - build and run the evaluation harness for a list of source trees, side by side, then
# compare every transcript with the control's (PowerShell 5.1, ASCII only). Nothing is overwritten: a tag whose
# folder exists is not rebuilt, a comparison whose log exists is not redone.
#   -Set "tag|source tree|switches|expected verdict" separated by ';'   (expected: PASS, or FAIL for a planted fault)
param(
    [Parameter(Mandatory = $true)][string]$Set,
    [string]$Control = 'ctl',
    [string]$Mask = '0x7032',
    [int]$Count = 12000
)
$ErrorActionPreference = 'Continue'
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.ProcessorAffinity = [IntPtr]([Convert]::ToInt64($Mask, 16))
$me.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::BelowNormal
$J = 'D:\forge_jobs_20261110\fable4cpu'
$T = "$J\repo\fable_cpu_speed\tools"
$LG = "$J\repo\fable_cpu_speed\evidence\logs"
$H = "$J\out\harness"
$ps = "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe"
$py = 'C:\Python315\python.exe'
function Start-Pinned([string]$al, [string]$console) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $ps
    $psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -File $T\pin.ps1 -Mask $Mask -Exe $py -ArgLine `"$al`" -OutFile $console"
    $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true
    return [System.Diagnostics.Process]::Start($psi)
}
$items = @()
foreach ($e in ($Set -split ';')) { if ($e.Trim()) { $f = $e.Split('|'); $items += @{ tag = $f[0].Trim(); src = $f[1].Trim(); defs = $f[2].Trim(); want = $f[3].Trim() } } }
if (-not (Test-Path -LiteralPath "$J\out\logs")) { [void](New-Item -ItemType Directory -Path "$J\out\logs") }
# 1) builds, side by side
$procs = @()
foreach ($it in $items) {
    if (Test-Path -LiteralPath "$H\$($it.tag)") { [Console]::Out.WriteLine("build skipped (exists): $($it.tag)"); continue }
    $d = ''; if ($it.defs) { $d = " --defs $($it.defs)" }
    $procs += Start-Pinned "-I -B $T\harness.py build --src $($it.src) --tag $($it.tag)$d --mask $Mask" "$J\out\logs\harness_build_$($it.tag).console.txt"
}
foreach ($p in $procs) { $p.WaitForExit() }
# 2) runs, side by side
$procs = @()
foreach ($it in $items) {
    if (Test-Path -LiteralPath "$H\$($it.tag)\eval_on.tsv") { [Console]::Out.WriteLine("run skipped (exists): $($it.tag)"); continue }
    if (-not (Test-Path -LiteralPath "$H\$($it.tag)\evaldump.exe")) { [Console]::Out.WriteLine("NO HARNESS EXE: $($it.tag) (see $H\$($it.tag)\build.log)"); continue }
    $procs += Start-Pinned "-I -B $T\harness.py run --tag $($it.tag) --mask $Mask --count $Count" "$J\out\logs\harness_run_$($it.tag).console.txt"
}
foreach ($p in $procs) { $p.WaitForExit() }
# 3) comparisons with the control
foreach ($it in $items) {
    if ($it.tag -eq $Control) { continue }
    foreach ($net in 'on', 'off') {
        $name = "harness_$($it.tag)_vs_$($Control)_net$net"
        $lf = "$LG\cmp_$name.log"
        if (Test-Path -LiteralPath $lf) { [Console]::Out.WriteLine("comparison skipped (log exists): $name"); continue }
        $out = & $ps -NoProfile -ExecutionPolicy Bypass -File "$T\pin.ps1" -Mask $Mask -Exe $py -ArgLine "-I -B $T\rows.py cmp --a $H\$Control\eval_$net.tsv --b $H\$($it.tag)\eval_$net.tsv --planned $Count --label $name --log $lf"
        $code = $LASTEXITCODE
        $got = @{ 0 = 'PASS'; 1 = 'FAIL'; 2 = 'INCOMPLETE' }[$code]
        $line = @($out | Where-Object { $_ -match 'planned \d+ completed' }) -join ' '
        [Console]::Out.WriteLine(("{0,-52} {1,-10} expected {2,-5} {3} | {4}" -f $name, $got, $it.want, $(if ($got -eq $it.want) { 'AS EXPECTED' } else { 'UNEXPECTED' }), $line))
    }
}
[Console]::Out.WriteLine('harness set ended')
