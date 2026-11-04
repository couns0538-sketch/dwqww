# wait_cpu01.ps1 - Item B (30-h job): wait until 14:10 PC clock, then until no process named forge-v2-bullet,
# fastchess or forge_ltopgo* has CPU 0 or 1 in its affinity mask. Polls every 60 s, never touches a process.
# Exit 0 = clear (the build may start), 1 = the cutoff was reached while still blocked. Log: wait_cpu01.log.
$start = Get-Date '2026-11-04 14:10:00'
$cutoff = Get-Date '2026-11-04 14:55:00'
$log = 'D:\o30\checks_itemB\wait_cpu01.log'
function Blockers {
    $out = @()
    foreach ($p in (Get-Process | Where-Object { $_.ProcessName -match '^(forge-v2-bullet|fastchess|forge_ltopgo)' })) {
        try { $m = [int64]$p.ProcessorAffinity } catch { $m = -1 }
        if ($m -eq -1 -or ($m -band 3) -ne 0) { $out += ('{0} pid {1} mask 0x{2:X}' -f $p.ProcessName, $p.Id, $m) }
    }
    return $out
}
"$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') waiter started (start gate $start, cutoff $cutoff)" | Add-Content $log
while ((Get-Date) -lt $start) { Start-Sleep -Seconds 30 }
"$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') 14:10 reached, polling CPU 0-1 users" | Add-Content $log
while ($true) {
    $b = @(Blockers)
    $stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    if ($b.Count -eq 0) {
        "$stamp CLEAR: no forge-v2-bullet / fastchess / forge_ltopgo* on CPU 0 or 1" | Add-Content $log
        Write-Output "CLEAR $stamp"
        exit 0
    }
    "$stamp waiting: $($b -join '; ')" | Add-Content $log
    if ((Get-Date) -ge $cutoff) {
        "$stamp CUTOFF reached, still blocked: $($b -join '; ')" | Add-Content $log
        Write-Output "CUTOFF $stamp blocked by $($b -join '; ')"
        exit 1
    }
    Start-Sleep -Seconds 60
}
