# run_determinism.ps1 - C5 determinism runs on the lock exe copy (PowerShell 5.1, ASCII only).
# Starts one pinned Python per run, side by side, each on its own CPU of the audit lane, and waits for all.
# Planned per net mode: cold x3 (2,000 positions each), warm x2 (2,000 each), reset x1 (500 positions, twice).
param(
    [string[]]$Cpus = @('1', '3', '6', '14', '4', '5'),
    [string]$Limit = 'depth 13'
)
$ErrorActionPreference = 'Stop'
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.ProcessorAffinity = [IntPtr]0x707F
$me.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::BelowNormal
$Cpus = @($Cpus | ForEach-Object { $_ -split ',' } | Where-Object { $_ -ne '' })
$J = 'D:\forge_jobs_20261110\fable4cpu'
$T = "$J\repo\fable_cpu_speed\tools"
$O = "$J\out\rows"
if (-not (Test-Path -LiteralPath $O)) { [void](New-Item -ItemType Directory -Path $O) }
$ps = "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe"
$lock = "$J\out\base\combo29_lock.exe"
$plan = @()
foreach ($net in 'on', 'off') {
    foreach ($k in 1, 2, 3) { $plan += @{ name = "det_cold_${net}_$k"; args = "--policy cold --net $net --count 2000" } }
    foreach ($k in 1, 2) { $plan += @{ name = "det_warm_${net}_$k"; args = "--policy warm --net $net --count 2000" } }
    $plan += @{ name = "det_reset_${net}"; args = "--policy reset --net $net --count 500" }
}
$queue = New-Object System.Collections.Queue
foreach ($x in $plan) { $queue.Enqueue($x) }
$running = New-Object System.Collections.ArrayList
$freeCpus = New-Object System.Collections.Queue
foreach ($c in $Cpus) { $freeCpus.Enqueue([int]$c) }
while ($queue.Count -gt 0 -or $running.Count -gt 0) {
    while ($queue.Count -gt 0 -and $freeCpus.Count -gt 0) {
        $x = $queue.Dequeue(); $cpu = $freeCpus.Dequeue()
        $mask = '0x{0:X}' -f (1 -shl $cpu)
        $outFile = "$O\$($x.name).tsv"
        if (Test-Path -LiteralPath $outFile) { [Console]::Out.WriteLine("skip (exists): $outFile"); $freeCpus.Enqueue($cpu); continue }
        $al = "-I -B $T\rows.py run --exe $lock --out $outFile --mask $mask --limit `"$Limit`" --label $($x.name) $($x.args)"
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $ps
        $psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -File $T\pin.ps1 -Mask $mask -Exe C:\Python315\python.exe -ArgLine `"$($al.Replace('"', '\"'))`" -OutFile $O\$($x.name).console.txt"
        $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true
        $p = [System.Diagnostics.Process]::Start($psi)
        [void]$running.Add(@{ p = $p; cpu = $cpu; name = $x.name })
        [Console]::Out.WriteLine("started $($x.name) on CPU $cpu ($mask)")
    }
    Start-Sleep -Seconds 2
    foreach ($e in @($running)) {
        if ($e.p.HasExited) {
            $e.p.WaitForExit()
            [Console]::Out.WriteLine("ended $($e.name) exit $($e.p.ExitCode)")
            $freeCpus.Enqueue($e.cpu); $running.Remove($e)
        }
    }
}
[Console]::Out.WriteLine('all determinism runs ended')
