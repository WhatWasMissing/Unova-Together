<#
Preview: .\tools\cleanup_mod_builds.ps1
Clean obsolete binaries: .\tools\cleanup_mod_builds.ps1 -Apply
Also discard rebuildable X compiler objects: add -IncludeCompilerOutputs.
Only named build roots are eligible. Source, user data and recovery backups stay.
#>
[CmdletBinding(SupportsShouldProcess=$true)]
param(
    [switch]$Apply,
    [switch]$IncludeCompilerOutputs,
    [string]$Workspace='',
    [string]$PokemonXRoot='F:\pokemon-x-coop',
    [string]$UnovaRoot='F:\unova-together'
)
$ErrorActionPreference='Stop'
if(-not $Workspace) { $Workspace=Split-Path -Parent $PSScriptRoot }
$workspacePath=[IO.Path]::GetFullPath($Workspace).TrimEnd('\')
$xPath=[IO.Path]::GetFullPath($PokemonXRoot).TrimEnd('\')
$unovaPath=[IO.Path]::GetFullPath($UnovaRoot).TrimEnd('\')
if(-not(Test-Path -LiteralPath (Join-Path $workspacePath 'tools\launcher_ui\game_routes.py'))) { throw 'This is not the multiplayer project.' }
if(-not(Test-Path -LiteralPath (Join-Path $xPath 'profiles\pokemon-x-base.research.json'))) { throw 'Pokemon X profile is missing.' }
if(-not(Test-Path -LiteralPath (Join-Path $unovaPath 'builds\current\melonDS.exe'))) { throw 'Move the current Unova package to F: first; no cleanup performed.' }

function Assert-Contained([string]$Path,[string]$Base) {
    $full=[IO.Path]::GetFullPath($Path)
    if(-not $full.StartsWith($Base+'\',[StringComparison]::OrdinalIgnoreCase)) { throw ('Outside allowed root: '+$full) }
    $cursor=$full
    while($true) {
        if(Test-Path -LiteralPath $cursor) {
            if((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw ('Linked path rejected: '+$cursor) }
        }
        if($cursor -eq $Base) { break }
        $cursor=Split-Path -Parent $cursor
        if(-not $cursor) { throw 'Invalid cleanup ancestor.' }
    }
    return $full
}

# Never traverse links or private directories, even inside an archived build.
function Get-SafeFiles([string]$Root,[string]$Base) {
    $null=Assert-Contained $Root $Base
    $pending=New-Object 'System.Collections.Generic.Stack[string]'
    $pending.Push($Root)
    while($pending.Count) {
        $directory=$pending.Pop()
        $null=Assert-Contained $directory $Base
        foreach($item in Get-ChildItem -LiteralPath $directory -Force) {
            if($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw ('Linked build entry rejected: '+$item.FullName) }
            if($item.PSIsContainer) {
                if($item.Name -notmatch '^(user|saves?|states|rom|game-files|play-profiles|backups|trade-state|\.git)$') { $pending.Push($item.FullName) }
            } else { $item }
        }
    }
}
function Get-RunningPaths {
    foreach($process in Get-CimInstance Win32_Process) {
        if($process.ExecutablePath) { $process.ExecutablePath }
    }
}
$running=@(Get-RunningPaths)
$roots=New-Object 'System.Collections.Generic.List[object]'
$buildDirectory=Join-Path $workspacePath 'builds'
foreach($folder in Get-ChildItem -LiteralPath $buildDirectory -Directory) {
    # Keep the current dev runtime, latest rollback package, hub and all unclassified candidates.
    if($folder.Name -match '^(archive|release-(0\..*|1\.0\.[0-3])|unova-together-0\..*|beta-.*|launcher-dist|launcher-styled-dist|launcher-gen5-tools-20261011)$') {
        $roots.Add([pscustomobject]@{Path=$folder.FullName;Base=$workspacePath;Type='Legacy binaries';Extensions=@('.exe','.dll','.pyd')})
    }
}
$bundle=Join-Path $workspacePath 'builds\azahar-x\bundle'
if(Test-Path -LiteralPath $bundle) { $roots.Add([pscustomobject]@{Path=$bundle;Base=$workspacePath;Type='Duplicate X bundle';Extensions=@('.exe','.dll')}) }
$cache=Join-Path $xPath 'tools\__pycache__'
if(Test-Path -LiteralPath $cache) { $roots.Add([pscustomobject]@{Path=$cache;Base=$xPath;Type='Python cache';Extensions=@('.pyc')}) }
if($IncludeCompilerOutputs) {
    foreach($relative in @('builds\azahar-x\src','builds\azahar-x\CMakeFiles','builds\azahar-x\externals')) {
        $path=Join-Path $workspacePath $relative
        if(Test-Path -LiteralPath $path) { $roots.Add([pscustomobject]@{Path=$path;Base=$workspacePath;Type='Rebuildable compiler output';Extensions=@('.obj','.pch')}) }
    }
}
$plan=New-Object 'System.Collections.Generic.List[object]'
$summaries=New-Object 'System.Collections.Generic.List[object]'
foreach($root in $roots) {
    $null=Assert-Contained $root.Path $root.Base
    if(@($running | Where-Object { $_.StartsWith($root.Path+'\',[StringComparison]::OrdinalIgnoreCase) }).Count) { Write-Host ('Skipped running build: '+$root.Path);continue }
    $files=@(Get-SafeFiles $root.Path $root.Base | Where-Object { $_.Extension.ToLowerInvariant() -in $root.Extensions })
    foreach($file in $files) { $plan.Add([pscustomobject]@{Path=$file.FullName;Base=$root.Base;Build=$root.Path;Bytes=$file.Length;Modified=$file.LastWriteTimeUtc.Ticks}) }
    if($files.Count) {
        $total=($files | Measure-Object Length -Sum).Sum
        $summaries.Add([pscustomobject]@{Build=$root.Path;Kind=$root.Type;Files=$files.Count;GiB=[math]::Round($total/1GB,3)})
    }
}
$summaries | Format-Table -AutoSize
$bytes=($plan | Measure-Object Bytes -Sum).Sum
Write-Host ($plan.Count.ToString()+' files; '+[math]::Round($bytes/1GB,2)+' GiB logical size. Hard-linked copies may reclaim less disk space.')
Write-Host 'Protected: F: Unova installation, source, current dev runtime, hub, release 1.0.4 rollback, ROMs, saves, states, user folders and backups.'
if(-not $Apply) { Write-Host 'Preview only. Run with -Apply to remove exactly these obsolete binary/cache files.';return }
if(-not $plan.Count) { return }
if(-not $PSCmdlet.ShouldProcess('Obsolete multiplayer build files','Delete '+$plan.Count+' binary/cache files; preserve user data')) { return }
# Validate every target before the first removal. Fail closed on changed paths/files/processes.
$running=@(Get-RunningPaths)
foreach($entry in $plan) {
    $null=Assert-Contained $entry.Path $entry.Base
    if($entry.Path.StartsWith($unovaPath+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Active F: installation is protected.' }
    $file=Get-Item -LiteralPath $entry.Path -Force
    if($file.Length -ne $entry.Bytes -or $file.LastWriteTimeUtc.Ticks -ne $entry.Modified) { throw ('File changed; rerun preview: '+$entry.Path) }
    if(@($running | Where-Object { $_.StartsWith($entry.Build+'\',[StringComparison]::OrdinalIgnoreCase) }).Count) { throw 'An old build started running; cleanup stopped.' }
}
$reportDirectory=Join-Path $workspacePath 'docs\cleanup-reports'
$null=Assert-Contained $reportDirectory $workspacePath
New-Item -ItemType Directory -Path $reportDirectory -Force | Out-Null
$report=Join-Path $reportDirectory ((Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N')+'.json')
$removed=New-Object 'System.Collections.Generic.List[string]'
try {
    @{planned=@($plan.ToArray());removed=@();started=(Get-Date).ToString('o')} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $report -Encoding UTF8
    foreach($entry in $plan) {
        $null=Assert-Contained $entry.Path $entry.Base
        $file=Get-Item -LiteralPath $entry.Path -Force
        if($file.Length -ne $entry.Bytes -or $file.LastWriteTimeUtc.Ticks -ne $entry.Modified) { throw ('File changed during cleanup: '+$entry.Path) }
        Remove-Item -LiteralPath $entry.Path -Force
        $removed.Add($entry.Path)
    }
} finally {
    @{planned=@($plan.ToArray());removed=@($removed.ToArray());finished=(Get-Date).ToString('o')} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $report -Encoding UTF8
}
Write-Host ('Removed '+$removed.Count+' files. Report: '+$report)
