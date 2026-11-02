$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]12
$env:TEMP='D:\a10\tmp';$env:TMP=$env:TEMP
$path=Join-Path $PSScriptRoot 'remote-heads.json'
if(Test-Path -LiteralPath $path){throw 'Preserve earlier receipt'}
$start=[DateTime]::UtcNow.ToString('o')
$lines=@(git -C D:\a10\wt ls-remote origin refs/heads/opus-r13-p4-v2nets refs/heads/opus-r13-p7-e3fit refs/heads/opus-r13-status)
$code=$LASTEXITCODE
@{capture_start_utc=$start;capture_finish_utc=[DateTime]::UtcNow.ToString('o');command='git -C D:\a10\wt ls-remote origin refs/heads/opus-r13-p4-v2nets refs/heads/opus-r13-p7-e3fit refs/heads/opus-r13-status';exit_code=$code;stdout=$lines;classification='UNPROVEN'} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $path -Encoding UTF8
if($code){throw 'Read-only remote-head query failed'}
$expected=@('df79fb6e33e0ec45e4bdf40cbbdfadb3b6fc27a6','cd9cb992fd6a6b05766d1117c1de441a430586a9','43af044a14a375b653f3d0bc633d9f476325ca81')
if($lines.Count -ne 3){throw 'Remote head count changed'}
foreach($sha in $expected){if(-not ($lines | Where-Object {$_.StartsWith($sha)})){throw 'Remote head advanced; reassess skip before packaging'}}
$lines
