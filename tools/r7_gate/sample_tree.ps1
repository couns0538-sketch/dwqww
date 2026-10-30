# R8: CPU and RAM of a process tree over time (read only). usage: sample_tree.ps1 -RootPid N [-Seconds 30] [-Out file.csv]
# Every $Seconds: total CPU seconds of the root and all descendants (cumulative), their working sets and private bytes,
# system free RAM and total CPU busy fraction (from processor time counters). Ends when the root process exits.
param([int]$RootPid, [int]$Seconds = 30, [string]$Out = "")
function Tree([int]$root) {
    $all = Get-CimInstance Win32_Process | Select-Object ProcessId, ParentProcessId
    $ids = New-Object System.Collections.Generic.HashSet[int]; [void]$ids.Add($root)
    $grow = $true
    while ($grow) { $grow = $false; foreach ($p in $all) { if ($ids.Contains([int]$p.ParentProcessId) -and -not $ids.Contains([int]$p.ProcessId)) { [void]$ids.Add([int]$p.ProcessId); $grow = $true } } }
    return $ids
}
$header = "time,elapsed_s,tree_procs,tree_cpu_s,tree_ws_mb,tree_private_mb,free_ram_gb,system_busy_pct"
if ($Out) { $header | Out-File -FilePath $Out -Encoding ascii } else { $header }
$t0 = Get-Date
while (Get-Process -Id $RootPid -ErrorAction SilentlyContinue) {
    $ids = Tree $RootPid
    $cpu = 0.0; $ws = 0.0; $pv = 0.0; $n = 0
    foreach ($i in $ids) { $p = Get-Process -Id $i -ErrorAction SilentlyContinue; if ($p) { $n++; $cpu += $p.TotalProcessorTime.TotalSeconds; $ws += $p.WorkingSet64; $pv += $p.PrivateMemorySize64 } }
    $os = Get-CimInstance Win32_OperatingSystem
    $busy = (Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor -Filter "Name='_Total'").PercentProcessorTime
    $line = "{0},{1:N0},{2},{3:N2},{4:N1},{5:N1},{6:N2},{7}" -f (Get-Date -Format "HH:mm:ss"), ((Get-Date) - $t0).TotalSeconds, $n, $cpu, ($ws / 1MB), ($pv / 1MB), ($os.FreePhysicalMemory / 1MB), $busy
    if ($Out) { $line | Out-File -FilePath $Out -Append -Encoding ascii } else { $line }
    Start-Sleep -Seconds $Seconds
}
