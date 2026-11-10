# cand_ladder.ps1 - the identity steps of one candidate, in order (PowerShell 5.1, ASCII only):
# patch file, apply proof, lock-recipe builds with the flag at 0 and at -On, 13 pins on each, byte comparison of the
# flag-0 build with my lock rebuild, evaluation harness for both against the control. The timing is a separate step.
# Stops at the first failed step. Nothing is overwritten: an existing build or log makes its step refuse.
param(
    [Parameter(Mandatory = $true)][string]$Name,     # candidate name = patch name = work folder
    [Parameter(Mandatory = $true)][string]$Short,    # short tag for build folders
    [Parameter(Mandatory = $true)][string]$Flag,     # e.g. FORGE_SPD_NNUE_FUSE_EVAL
    [string]$On = '1',
    [string]$Mask = '0x7032'
)
$ErrorActionPreference = 'Continue'
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.ProcessorAffinity = [IntPtr]([Convert]::ToInt64($Mask, 16))
$me.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::BelowNormal
$J = 'D:\forge_jobs_20261110\fable4cpu'
$T = "$J\repo\fable_cpu_speed\tools"
$LG = "$J\repo\fable_cpu_speed\evidence\logs"
$B = "$J\out\build"
$W = "$J\out\work\$Name"
$ps = "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe"
$py = 'C:\Python315\python.exe'
function Say([string]$s) { [Console]::Out.WriteLine($s) }
function Py([string]$al) { & $ps -NoProfile -ExecutionPolicy Bypass -File "$T\pin.ps1" -Mask $Mask -Exe $py -ArgLine $al }
$o = Py "-I -B $T\cand.py patch $Name"; Say (@($o) -join ' | ')
$o = Py "-I -B $T\cand.py verify $Name"; $code = $LASTEXITCODE
Say ((@($o | Where-Object { $_ -match 'DIFF|VERDICT|numstat|^patch ' }) -join ' | '))
if ($code -ne 0) { Say 'STOP: patch proof failed'; exit 1 }
foreach ($v in @(@("${Short}_off", ''), @("${Short}_on", "$Flag=$On"))) {
    $args2 = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "$T\build.ps1", '-Tag', $v[0], '-Src', "$W\p", '-Mask', $Mask, '-Jobs', '6')
    if ($v[1]) { $args2 += @('-ExtraDefs', $v[1]) }
    $o = & $ps @args2 2>&1 | ForEach-Object { "$_" }
    Say ("build $($v[0]): " + (@($o | Where-Object { $_ -match '^RESULT|^end |: error|refusing|NOT STARTED|failed:' }) -join ' | '))
    if (-not (Test-Path -LiteralPath "$B\$($v[0])\m2use\forge_m2use.exe")) { Say "STOP: build $($v[0]) gave no exe"; exit 1 }
    Copy-Item -LiteralPath "$B\$($v[0])\build.log" -Destination "$LG\build_$($v[0]).log"
}
$procs = @()
foreach ($v in @(@("${Short}_off", "$Flag=0 (patch applied, flag at 0)", '0x10,0x2,0x1000'), @("${Short}_on", "$Flag=$On", '0x20,0x4000,0x2000'))) {
    $al = "-I -B $T\pins.py --exe $B\$($v[0])\m2use\forge_m2use.exe --log $LG\pins_$($v[0]).log --label $($v[0]) --masks $($v[2]) --flags \`"$($v[1])\`""
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $ps
    $psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -File $T\pin.ps1 -Mask $Mask -Exe $py -ArgLine `"$al`" -OutFile $J\out\logs\pins_$($v[0]).console.txt"
    $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true
    $procs += [System.Diagnostics.Process]::Start($psi)
}
foreach ($p in $procs) { $p.WaitForExit() }
$pinsOk = $true
foreach ($tagName in "${Short}_off", "${Short}_on") {      # not $t: names are case-insensitive and $T is the tools folder
    $v = @(Get-Content "$LG\pins_$tagName.log" -ErrorAction SilentlyContinue | Where-Object { $_ -match 'DIFF|ERROR|planned \d+ completed|VERDICT' }) -join ' | '
    Say "pins ${tagName}: $v"
    if ($v -notmatch 'VERDICT PINS PASS') { $pinsOk = $false }
}
$o = Py "-I -B $T\bytecmp.py --a $B\c29ctl\m2use\forge_m2use.exe --b $B\${Short}_off\m2use\forge_m2use.exe --label c29ctl_vs_${Name}_flag0 --log $LG\bytecmp_c29ctl_vs_${Short}_off.log"
Say ("bytecmp flag 0 vs lock rebuild: " + (@($o | Where-Object { $_ -match 'VERDICT|differing ranges' }) -join ' | '))
if (-not $pinsOk) { Say 'STOP: pins not all equal'; exit 1 }
& $ps -NoProfile -ExecutionPolicy Bypass -File "$T\run_harness_set.ps1" -Mask $Mask -Set "ctl|$J\repo\forge-combo29||PASS;${Short}_off|$W\p||PASS;${Short}_on|$W\p|$Flag=$On|PASS" | ForEach-Object { Say "$_" }
Say 'ladder ended'
