param([switch]$IncludeDatasets)
$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='Idle'
$root='D:\a14'
$fixed=@(
@('D:\a13\FINAL_REPORT.md','78d231a89ca346bbe669f2242ae6329e'),
@('D:\a13\p5qc\statistics.json','062429777cecdb8e522449f0264618b4'),
@('D:\a13\p5qc\mate_rows.jsonl','aa78162b2280c51d72d12ccbb5eb3b16'),
@('D:\a13\pgnpack\SEARCH.json','413589c7fa584022ee504221871ebe18'),
@('D:\a13\tools\p5_qc.py','79c87d85d8dabdb8a9cd1d30ebcff1c0'),
@('D:\a13\tools\qc_core.py','47e96abf376a610b1b55e5416a27727d'),
@('D:\a13\tools\game_hash.py','628d771af7a4f523c66e8c5b03f63ccc'),
@('D:\a13\tools\run_policy.py','a0d117ccdb1eff2591161e072385b7aa'),
@('D:\a13\tools\Invoke-R13.ps1','1575521f9a04ac981cb781b1679ba1a3'),
@('D:\a13\.agents\skills\npt-data-holdout-check\SKILL.md','7dddc603349e81a7a0078f1b2827c569'),
@('D:\o14b\r2\proof\jobA\final\labels.tsv','2614e82d55bc5e9572c24d3900a8810a'),
@('D:\o14b\r2\proof\jobA\final\train.txt','6e9e4e5abbf9e1fa86dc33823aef7903'),
@('D:\o14b\r2\proof\jobA\final\val.txt','8e639f41c64dbe96581b1d6a3f4cf675'),
@('D:\o14b\r2\proof\jobA\rows.tsv','57a6742279339282763dff17e97670ce'),
@('D:\o14b\r2\proof\jobA\final\MANIFEST.json','94d2d7629382f69132d71df19426660a'),
@('D:\o14b\r2\proof\jobA\prepare.json','1d7fd43dcd2f0d5553d940012cdc8bd7')
)
$sourcePins=@{1='5c82679fd4c60862942b7ddd3620b265';2='1cb03e142338c33a9f58ad495f8ca0c4';12='c55e3732dd340d9818e5845f486d7847';13='f0739b12b4b32c41094aabf7cac26686';14='2900e7985e2cd588dfc02fac26c08ced';15='3666476d10d15e1cad48b24f61b251cc'}
$checks=[Collections.Generic.List[object]]::new()
foreach ($pair in $fixed) { $checks.Add(@{path=$pair[0];expected=$pair[1];pin_origin='user'}) }
if ($IncludeDatasets) {
 foreach ($number in 1..39) {
  $path='D:\grok-pc-data\selfplay_out\forge_selfplay_{0:000}.txt' -f $number
  $origin='user'
  if ($sourcePins.ContainsKey($number)) { $expected=$sourcePins[$number] }
  else {
   $origin=$path+'.md5'
   $text=[IO.File]::ReadAllText($origin).Trim()
   $leaf=[IO.Path]::GetFileName($path)
   if ($text -notmatch ('^([0-9a-fA-F]{32})\s+\*?'+[Regex]::Escape($leaf)+'$')) { throw "Malformed sidecar $origin" }
   $expected=$Matches[1].ToLowerInvariant()
  }
  $checks.Add(@{path=$path;expected=$expected;pin_origin=$origin})
 }
}
$tag=if ($IncludeDatasets) {'all'} else {'small'}
$out=Join-Path $root ('evidence\r14\input-pins-'+$tag+'.jsonl')
if (Test-Path -LiteralPath $out) { throw 'Receipt exists' }
$utf8=New-Object System.Text.UTF8Encoding($false)
foreach ($check in $checks) {
 if ((Get-PSDrive D).Free -lt (50GB+1MB) -or (Get-PSDrive C).Free -lt 30GB) { throw 'Disk floor' }
 $before=Get-Item -LiteralPath $check.path
 $size=$before.Length
 $mtime=$before.LastWriteTimeUtc.Ticks
 $actual=(Get-FileHash -Algorithm MD5 -LiteralPath $check.path).Hash.ToLowerInvariant()
 if ((Get-PSDrive D).Free -lt (50GB+1MB) -or (Get-PSDrive C).Free -lt 30GB) { throw 'Disk floor after hashing; no receipt allocation' }
 $after=Get-Item -LiteralPath $check.path
 $match=($actual -ceq $check.expected -and $after.Length -eq $size -and $after.LastWriteTimeUtc.Ticks -eq $mtime)
 $receipt=@{path=$check.path;expected_md5=$check.expected;actual_md5=$actual;bytes=$size;pin_origin=$check.pin_origin;match=$match;time_vienna=((Get-Date -Format 'yyyy-MM-dd HH:mm:ss')+' Vienna')}
 [IO.File]::AppendAllText($out,($receipt | ConvertTo-Json -Compress)+"`n",$utf8)
 $receipt | ConvertTo-Json -Compress
 if (-not $match) { throw ('STOP: INPUT HASH OR STABILITY MISMATCH '+$check.path) }
}
if ((Get-PSDrive D).Free -lt 50GB -or (Get-PSDrive C).Free -lt 30GB) { throw 'Disk floor at completion' }
