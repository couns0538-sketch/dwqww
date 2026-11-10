# Dot-source at the start of every shell call of this job:
#   . D:\forge_jobs_20261109\fable2\repo\fable_speed_lane\tools\env.ps1
# Keeps TEMP/TMP and caches on D:, stops git/gh from prompting, never touches global settings. ASCII only (PS 5.1).
$global:J    = 'D:\forge_jobs_20261109\fable2'
$global:REPO = Join-Path $J 'repo'
$global:OUT  = Join-Path $J 'out'
$global:PACK = Join-Path $REPO 'fable_speed_lane'
$global:T    = Join-Path $PACK 'tools'
$global:PY   = 'C:\Python315\python.exe'          # read and execute only
$global:LM   = 'C:\opus_5h\oss_scout\dl\llvm-mingw-20261104\x\llvm-mingw-20261104-ucrt-x86_64\bin'   # read and execute only
$global:PIN  = Join-Path $T 'pin.ps1'
$env:TEMP = Join-Path $OUT 'tmp'
$env:TMP  = $env:TEMP
$env:GIT_TERMINAL_PROMPT = '0'
$env:GCM_INTERACTIVE = 'never'
$env:GH_PROMPT_DISABLED = '1'
$env:GH_NO_UPDATE_NOTIFIER = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPYCACHEPREFIX = Join-Path $OUT 'pycache'
function global:DFree { [math]::Round((Get-PSDrive D).Free / 1GB, 2) }
function global:NowVienna {
    [TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTime]::UtcNow, 'W. Europe Standard Time').ToString('yyyy-MM-dd HH:mm:ss') + ' Vienna'
}
# Pinned run of one program (mask 0x78 or a subset, Idle). Returns the child's exit code.
function global:Pinned([string]$Exe, [string]$ArgLine = '', [string]$OutFile = '', [string]$InFile = '', [string]$WorkDir = '', [long]$Mask = 0x78) {
    $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $PIN, '-Exe', $Exe, '-Mask', $Mask)
    if ($ArgLine -ne '') { $a += @('-ArgLine', $ArgLine) }
    if ($OutFile -ne '') { $a += @('-OutFile', $OutFile) }
    if ($InFile -ne '') { $a += @('-InFile', $InFile) }
    if ($WorkDir -ne '') { $a += @('-WorkDir', $WorkDir) }
    & powershell.exe @a
    return $LASTEXITCODE
}
