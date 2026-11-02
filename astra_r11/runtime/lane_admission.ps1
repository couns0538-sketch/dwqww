# Read-only admission. Never modifies another process or reads queue files.
function Get-R11LaneConflicts([object[]]$Records,[int[]]$SkipIds,[long]$AllMask) {
    $hits=@()
    foreach($row in $Records){
        if([int]$row.pid -in $SkipIds){continue}
        if($row.command -match '(?i)run_tmfit|final200|run_parallel_smoke|tmfit_referee'){
            $hits+=[ordered]@{pid=$row.pid;name=$row.name;reason='timing lane command'};continue
        }
        if($null -ne $row.mask -and [long]$row.mask -ne 0 -and [long]$row.mask -ne $AllMask -and ([long]$row.mask -band 12) -ne 0){
            $hits+=[ordered]@{pid=$row.pid;name=$row.name;mask=$row.mask;reason='unrelated process pinned onto CPU2/3'}
        }
    }
    return $hits
}
function Get-R11LaneAdmission {
    $processors=[Environment]::ProcessorCount
    if($processors -lt 4 -or $processors -ge 63){throw 'Explicit one-group CPU topology required'}
    [long]$allMask=([long]1 -shl $processors)-1
    $cim=@(Get-CimInstance Win32_Process -ErrorAction Stop)
    $byPid=@{};foreach($row in $cim){$byPid[[int]$row.ProcessId]=$row}
    $skip=@();$ancestor=[Diagnostics.Process]::GetCurrentProcess().Id
    while($ancestor -gt 0 -and $ancestor -notin $skip){$skip+=$ancestor;if(-not $byPid.ContainsKey($ancestor)){break};$ancestor=[int]$byPid[$ancestor].ParentProcessId}
    $rows=@();$unreadable=0
    foreach($row in $cim){
        $mask=$null
        try{$proc=[Diagnostics.Process]::GetProcessById([int]$row.ProcessId);try{$mask=$proc.ProcessorAffinity.ToInt64()}finally{$proc.Dispose()}}catch{$unreadable++}
        $rows+=[pscustomobject]@{pid=[int]$row.ProcessId;name=$row.Name;command=[string]$row.CommandLine;mask=$mask}
    }
    $conflicts=@(Get-R11LaneConflicts $rows $skip $allMask)
    $load=@(Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor -ErrorAction Stop|Where-Object Name -in @('2','3'))
    $available=[long](Get-CimInstance Win32_OperatingSystem -ErrorAction Stop).FreePhysicalMemory*1024
    $busy=@($load|Where-Object PercentProcessorTime -ge 50)
    return [ordered]@{status=$(if($conflicts.Count -eq 0 -and $load.Count -eq 2 -and $busy.Count -eq 0 -and $available -ge 8GB){'ADMITTED'}else{'BLOCKED'});utc=[DateTime]::UtcNow.ToString('o');cpus=@(2,3);conflicts=$conflicts;unreadable_processes=$unreadable;free_ram_bytes=$available;cpu_load=@($load|ForEach-Object{[ordered]@{cpu=[int]$_.Name;percent=[int]$_.PercentProcessorTime}});scope='Read-only instantaneous admission; normal all-CPU processes are not affinity conflicts; no process or queue changed'}
}
