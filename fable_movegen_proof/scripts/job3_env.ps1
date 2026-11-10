# job3_env.ps1 - dot-source at the start of every job-3 script (PowerShell 5.1, ASCII only).
#   . D:\forge_jobs_20261109\fable2\repo\fable_movegen_proof\scripts\job3_env.ps1
# Paths of the job, TEMP/TMP on D:, git guards, self-pinning, disk guard, hashing without Get-FileHash.
# It changes nothing outside this process.
$global:J3_REPO  = 'D:\forge_jobs_20261109\fable2\repo'
$global:J3_PACK  = Join-Path $J3_REPO 'fable_movegen_proof'
$global:J3_OUT   = 'D:\forge_jobs_20261109\fable2\out\job3'
$global:J3_JOB2  = 'D:\forge_jobs_20261109\fable2\out'
$global:J3_QA    = 'D:\forge_qa\fable2_cands_20261109'
$global:J3_PY    = 'C:\Python315\python.exe'                                                            # read and execute only
$global:J3_LM    = 'C:\opus_5h\oss_scout\dl\llvm-mingw-20261104\x\llvm-mingw-20261104-ucrt-x86_64\bin'   # read and execute only
$global:J3_LANE  = 0x78
$global:J3_FLOOR = 30.3
$env:TEMP = Join-Path $J3_OUT 'tmp'
$env:TMP  = $env:TEMP
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:GIT_NO_LAZY_FETCH = '1'
$env:GIT_TERMINAL_PROMPT = '0'
$env:GCM_INTERACTIVE = 'never'
$env:GH_PROMPT_DISABLED = '1'

# Pin this process to the lane (or a subset) at Idle priority and read both back. Children inherit both.
function global:J3-Pin([long]$Mask = 0x78) {
    if ($Mask -le 0 -or ($Mask -band (-bnot $J3_LANE)) -ne 0) { throw ('J3-Pin: mask 0x{0:X} is not inside 0x78' -f $Mask) }
    $me = [System.Diagnostics.Process]::GetCurrentProcess()
    $me.ProcessorAffinity = [IntPtr]$Mask
    $me.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::Idle
    $me.Refresh()
    if (([int64]$me.ProcessorAffinity) -ne $Mask) { throw 'J3-Pin: affinity was not applied' }
    if ($me.PriorityClass -ne [System.Diagnostics.ProcessPriorityClass]::Idle) { throw 'J3-Pin: Idle priority was not applied' }
    return ('pinned: affinity 0x{0:X}, priority Idle' -f $Mask)
}
function global:J3-Free { return [math]::Round((Get-PSDrive D).Free / 1GB, 2) }
function global:J3-Guard {
    $f = (Get-PSDrive D).Free / 1GB
    if ($f -lt $J3_FLOOR) { throw ('J3-Guard: NOT STARTED (disk guard): D: has {0:N2} GiB free, under {1:N1}' -f $f, $J3_FLOOR) }
}
function global:J3-Now {
    return [TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTime]::UtcNow, 'W. Europe Standard Time').ToString('yyyy-MM-dd HH:mm:ss') + ' Vienna'
}
# MD5 or SHA256 of a file as lower-case hex, through System.Security.Cryptography.
function global:J3-Hash([string]$Path, [string]$Alg = 'SHA256') {
    if ($Alg -eq 'MD5') { $h = [System.Security.Cryptography.MD5]::Create() } else { $h = [System.Security.Cryptography.SHA256]::Create() }
    # FileShare ReadWrite: a log that a running process still writes can be read (its hash is then a snapshot)
    $s = New-Object System.IO.FileStream($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
    try { $b = $h.ComputeHash($s) } finally { $s.Dispose(); $h.Dispose() }
    return ([System.BitConverter]::ToString($b) -replace '-', '').ToLower()
}
