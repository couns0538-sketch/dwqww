# Download and unpack official immutable archives only. Never runs Python/pip.
[CmdletBinding()]
param([switch]$BootstrapOnly)
$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess()
$self.PriorityClass='Idle'
$root='D:\a11\runtime'
$repo='D:\a11\wt'
$env:TEMP='D:\a11\tmp'; $env:TMP=$env:TEMP
$allowed=@('api.nuget.org','globalcdn.nuget.org','www.nuget.org','files.pythonhosted.org','pypi.org','download.pytorch.org','download-r2.pytorch.org')
function Safe-RuntimePath([string]$Path) {
    . "$repo\skills\grok-pc-safe-run\scripts\Invoke-GrokPcSafeRun.ps1"
    return (Assert-R10WritePath $Path @('D:\a10','F:\'))
}
function Guard([long]$Reservation=0) {
    if([IO.DriveInfo]::new('C:\').AvailableFreeSpace -lt 30GB){throw 'C floor 30GiB'}
    if([IO.DriveInfo]::new('D:\').AvailableFreeSpace -lt (50GB+$Reservation)){throw 'D floor 50GiB plus reservation'}
    foreach($p in @('D:\a11',$root)) {$null=Safe-RuntimePath $p}
}
function Write-NewJson([string]$Path,[object]$Value) {
    $Path=Safe-RuntimePath $Path
    $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($Value|ConvertTo-Json -Depth 12)+"`n")
    $s=[IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
    try{$s.Write($bytes,0,$bytes.Length);$s.Flush($true)}finally{$s.Dispose()}
}
function Download([string]$Url,[string]$Name,[string]$Sha,[long]$Expected) {
    if($Name -match '[\\/:]' -or $Name -in @('.','..') -or $Sha -notmatch '^[0-9a-f]{64}$' -or $Expected -le 0){throw 'Invalid archive identity'}
    Guard ($Expected+10MB)
    $path=Safe-RuntimePath (Join-Path "$root\downloads" $Name)
    if(Test-Path -LiteralPath $path){
        if((Get-Item -LiteralPath $path).Length -ne $Expected -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ine $Sha){throw "Existing download differs; retained: $path"}
        return $path
    }
    $handler=[Net.Http.HttpClientHandler]::new();$handler.AllowAutoRedirect=$false
    $client=[Net.Http.HttpClient]::new($handler);$client.Timeout=[TimeSpan]::FromMinutes(10)
    $urlNow=$Url; $response=$null; $input=$null; $output=$null
    try {
        for($redirect=0;$redirect -le 5;$redirect++) {
            $uri=[Uri]$urlNow
            if($uri.Scheme -ne 'https' -or $uri.Host -notin $allowed -or $uri.UserInfo){throw 'Nonofficial archive URL refused'}
            $response=$client.GetAsync($uri,[Net.Http.HttpCompletionOption]::ResponseHeadersRead).GetAwaiter().GetResult()
            if([int]$response.StatusCode -ge 300 -and [int]$response.StatusCode -lt 400){$urlNow=[Uri]::new($uri,$response.Headers.Location).AbsoluteUri;$response.Dispose();$response=$null;continue}
            $response.EnsureSuccessStatusCode()|Out-Null;break
        }
        if($null -eq $response){throw 'Too many redirects'}
        if($response.Content.Headers.ContentLength -and $response.Content.Headers.ContentLength -ne $Expected){throw 'Declared archive length mismatch'}
        $input=$response.Content.ReadAsStreamAsync().GetAwaiter().GetResult()
        $output=[IO.File]::Open($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
        $buffer=[byte[]]::new(1MB);[long]$total=0
        while(($n=$input.Read($buffer,0,$buffer.Length)) -gt 0){$total+=$n;if($total -gt $Expected){throw 'Archive size bound exceeded'};Guard;$output.Write($buffer,0,$n)}
        $output.Flush($true);$output.Dispose();$output=$null
        if($total -ne $Expected -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ine $Sha){throw "Official archive identity mismatch; retained: $path"}
        Write-NewJson ($path+'.receipt.json') ([ordered]@{url=$Url;final_url=$urlNow;path=$path;bytes=$total;sha256=$Sha;status='VERIFIED_DOWNLOAD'})
        return $path
    } finally {if($output){$output.Dispose()};if($input){$input.Dispose()};if($response){$response.Dispose()};$client.Dispose();$handler.Dispose()}
}
function Extract-Zip([string]$Archive,[string]$Destination,[switch]$Nuget) {
    $Archive=Safe-RuntimePath $Archive;$Destination=Safe-RuntimePath $Destination
    if(Test-Path -LiteralPath $Destination){throw "Fresh extraction required: $Destination"}
    $zip=[IO.Compression.ZipFile]::OpenRead($Archive)
    try {
        [long]$expanded=0;$names=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
        foreach($entry in $zip.Entries){
            $name=$entry.FullName.Replace('\','/');$parts=$name.TrimEnd('/').Split('/')
            if($name.StartsWith('/') -or $name.Contains(':') -or $parts.Contains('..') -or $parts.Contains('.') -or $parts.Contains('') -or -not $names.Add($name)){throw 'Unsafe/duplicate archive member'}
            if((($entry.ExternalAttributes -shr 16) -band 61440) -eq 40960){throw 'Archive symlink refused'}
            if($Nuget -and -not $name.StartsWith('tools/',[StringComparison]::OrdinalIgnoreCase)){continue}
            $expanded+=$entry.Length
            if($expanded -gt 256MB){throw 'Expanded bootstrap bound exceeded'}
        }
        Guard ($expanded+10MB)
        [IO.Directory]::CreateDirectory($Destination)|Out-Null
        foreach($entry in $zip.Entries){
            $name=$entry.FullName.Replace('\','/')
            if($Nuget){if(-not $name.StartsWith('tools/',[StringComparison]::OrdinalIgnoreCase)){continue};$name=$name.Substring(6)}
            if(-not $name){continue}
            $target=Safe-RuntimePath (Join-Path $Destination $name)
            if($name.EndsWith('/')){[IO.Directory]::CreateDirectory($target)|Out-Null;continue}
            [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target))|Out-Null
            $src=$entry.Open();$dst=[IO.File]::Open($target,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
            try{$src.CopyTo($dst);$dst.Flush($true)}finally{$src.Dispose();$dst.Dispose()}
        }
    }finally{$zip.Dispose()}
}
Guard 2500MB
[IO.Directory]::CreateDirectory("$root\downloads")|Out-Null
foreach($sub in @('tmp','cache','logs')){[IO.Directory]::CreateDirectory("$root\$sub")|Out-Null}
$bootstrap=Get-Content -Raw -LiteralPath "$repo\astra_r10\job3\runtime312\BOOTSTRAP.json"|ConvertFrom-Json
$pythonRow=$bootstrap.downloads|Where-Object path -like '*.nupkg'
$pipRow=$bootstrap.downloads|Where-Object path -like '*.whl'
$python=Download $pythonRow.url 'python.3.12.10.nupkg' $pythonRow.sha256 $pythonRow.bytes
$pip=Download $pipRow.url 'pip-25.3-py3-none-any.whl' $pipRow.sha256 $pipRow.bytes
if(-not(Test-Path -LiteralPath "$root\python")){Extract-Zip $python "$root\python" -Nuget}
if(-not(Test-Path -LiteralPath "$root\bootstrap_packages")){Extract-Zip $pip "$root\bootstrap_packages"}
if((Get-FileHash -LiteralPath "$root\python\python.exe" -Algorithm SHA256).Hash -ine $bootstrap.interpreter_sha256){throw 'Python interpreter identity mismatch'}
if(-not(Test-Path -LiteralPath "$root\BOOTSTRAP.json")){
    Write-NewJson "$root\BOOTSTRAP.json" ([ordered]@{schema=1;status='ARCHIVES_EXTRACTED_INTERPRETER_UNRUN';python='3.12.10';root=$root;python_sha256=$bootstrap.interpreter_sha256;source_bootstrap_sha256=(Get-FileHash -LiteralPath "$repo\astra_r10\job3\runtime312\BOOTSTRAP.json" -Algorithm SHA256).Hash.ToLowerInvariant();scope='Official pinned NuGet and PyPI archives; no interpreter execution'})
}
Write-Output 'CPython3.12.10 and pip archives verified/extracted; interpreter unrun'
if($BootstrapOnly){return}
$lock=Get-Content -Raw -LiteralPath "$repo\astra_r10\job3\runtime312np254\WHEEL_LOCK.json"|ConvertFrom-Json
$rows=@()
foreach($wheel in $lock.wheels){
    $path=Download $wheel.official.url $wheel.filename $wheel.sha256 $wheel.bytes
    $rows+=[ordered]@{name=$wheel.name;version=$wheel.version;path=$path;filename=$wheel.filename;bytes=$wheel.bytes;sha256=$wheel.sha256;expanded_bytes=$wheel.expanded_bytes;url=$wheel.official.url}
}
if(-not(Test-Path -LiteralPath "$root\WHEEL_LOCK.json")){
    Write-NewJson "$root\WHEEL_LOCK.json" ([ordered]@{schema=1;status='VERIFIED_OFFICIAL_DOWNLOADS';source_lock_sha256=(Get-FileHash -LiteralPath "$repo\astra_r10\job3\runtime312np254\WHEEL_LOCK.json" -Algorithm SHA256).Hash.ToLowerInvariant();wheels=$rows})
}
Write-Output ("Verified "+$rows.Count+' immutable official wheel downloads; none installed')
$chessMetadata=Invoke-RestMethod -Uri 'https://pypi.org/pypi/chess/1.11.2/json' -MaximumRedirection 0
$chessRows=@($chessMetadata.urls|Where-Object filename -eq 'chess-1.11.2.tar.gz')
if($chessRows.Count -ne 1){throw 'Exact official chess1.11.2 source archive missing'}
$chess=$chessRows[0]
$chessPath=Download $chess.url $chess.filename $chess.digests.sha256 $chess.size
if(-not(Test-Path -LiteralPath "$root\CHESS_SOURCE.json")){
    Write-NewJson "$root\CHESS_SOURCE.json" ([ordered]@{name='chess';version='1.11.2';url=$chess.url;path=$chessPath;sha256=$chess.digests.sha256;bytes=$chess.size;license='GPL-3.0-or-later';scope='External test runtime only; no GPL code in Forge source'})
}
