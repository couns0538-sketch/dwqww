$ErrorActionPreference='Stop'
$path='D:\a14\tools\Invoke-R13.ps1'
$source=[IO.File]::ReadAllText($path)
if ($source.StartsWith('#Requires -Version 7')) { throw 'Already adapted' }
$source='#Requires -Version 7'+"`n"+$source
$source=$source.Replace("'D:\a13'","'D:\a14'").Replace("'D:\a11\runtime\python\python.exe'","'D:\a14\runtime\python\python.exe'")
$source=$source.Replace("if (`$RequiredBytes -lt 0 -or (Get-PSDrive D).Free -lt (50GB + `$RequiredBytes))", "if (`$RequiredBytes -lt 0 -or (Get-PSDrive D).Free -lt (50GB + `$RequiredBytes) -or (Get-PSDrive C).Free -lt 30GB)")
$source=$source.Replace("'evidence\runs\'", "'evidence\test_logs\r14\launchers\'")
$start=$source.IndexOf('if ($WithDatafilterRuntime) {')
$end=$source.IndexOf('$process=[Diagnostics.Process]::GetCurrentProcess()', $start)
if ($start -lt 0 -or $end -lt 0) { throw 'Runtime block not found' }
$source=$source.Substring(0,$start)+"if (`$WithDatafilterRuntime) { throw 'Protected runtime access is forbidden' }`n`$env:PYTHONPATH='D:\a14\tools'`n"+$source.Substring($end)
$source=$source.Replace("`$env:PYTHONDONTWRITEBYTECODE='1'", "`$childEnvironment=@{}`n`$env:PYTHONDONTWRITEBYTECODE='1'")
$source=[Regex]::Replace($source,'\$env:([A-Z][A-Z0-9_]*)', {param($m) '$childEnvironment['''+$m.Groups[1].Value+''']'})
$needle='$child.StartInfo.UseShellExecute=$false'
$source=$source.Replace($needle,$needle+"`nforeach (`$key in `$childEnvironment.Keys) { `$child.StartInfo.Environment[`$key]=[string]`$childEnvironment[`$key] }")
$source=$source.Replace("if ((Get-PSDrive D).Free -lt 50GB)","if ((Get-PSDrive D).Free -lt 50GB -or (Get-PSDrive C).Free -lt 30GB)")
$source=$source.Replace("if ((Get-PSDrive D).Free -lt (50GB+1MB))", "if ((Get-PSDrive D).Free -lt (50GB+1MB) -or (Get-PSDrive C).Free -lt 30GB)")
$source=$source.Replace("[DateTime]::UtcNow.ToString('o')", "((Get-Date -Format 'yyyy-MM-dd HH:mm:ss')+' Vienna')")
[IO.File]::WriteAllText($path,$source,(New-Object System.Text.UTF8Encoding($false)))
