# run_san_chain.ps1 - C5 sanitizer chain on the audit lane (PowerShell 5.1, ASCII only): instrumented builds,
# full bench under each sanitizer, then the multi-thread fixed-node searches. Each step runs through pin.ps1.
# A step whose log already exists is skipped (nothing is overwritten or deleted).
param([string]$Mask = '0x404A', [string]$BenchMasksA = '0x2,0x8', [string]$BenchMasksB = '0x40,0x4000')
$ErrorActionPreference = 'Continue'
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.ProcessorAffinity = [IntPtr]([Convert]::ToInt64($Mask, 16))
$me.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::BelowNormal
$J = 'D:\forge_jobs_20261110\fable4cpu'
$T = "$J\repo\fable_cpu_speed\tools"
$LG = "$J\repo\fable_cpu_speed\evidence\logs"
$B = "$J\out\build"
$ps = "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe"
$steps = @(
    @{ log = 'san_build_asan.log';  a = "build --kind asan --tag san_asan --mask $Mask" },
    @{ log = 'san_build_ubsan.log'; a = "build --kind ubsan --tag san_ubsan --mask $Mask" },
    @{ log = 'san_bench_asan.log';  a = "bench --kind asan --exe $B\san_asan\forge_asan.exe --masks $BenchMasksA" },
    @{ log = 'san_bench_ubsan.log'; a = "bench --kind ubsan --exe $B\san_ubsan\forge_ubsan.exe --masks $BenchMasksB" },
    @{ log = 'mt_asan.log';         a = "mt --kind asan --exe $B\san_asan\forge_asan.exe --mask $Mask" },
    @{ log = 'mt_ubsan.log';        a = "mt --kind ubsan --exe $B\san_ubsan\forge_ubsan.exe --mask $Mask" },
    @{ log = 'mt_release_lock.log'; a = "mt --kind release --exe $J\out\base\combo29_lock.exe --mask $Mask" }
)
foreach ($s in $steps) {
    $lf = "$LG\$($s.log)"
    if (Test-Path -LiteralPath $lf) { [Console]::Out.WriteLine("skip (log exists): $($s.log)"); continue }
    $out = & $ps -NoProfile -ExecutionPolicy Bypass -File "$T\pin.ps1" -Mask $Mask -Exe 'C:\Python315\python.exe' -ArgLine "-I -B $T\san.py $($s.a) --log $lf"
    $v = @($out | Where-Object { $_ -match 'VERDICT|planned \d+ completed|refusing|NOT STARTED|Traceback|Error' }) -join ' || '
    [Console]::Out.WriteLine("$($s.log): exit $LASTEXITCODE :: $v")
}
[Console]::Out.WriteLine('sanitizer chain ended')
