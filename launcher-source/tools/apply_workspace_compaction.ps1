[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$Manifest)
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot)).TrimEnd('\')
$record=Get-Content -LiteralPath $Manifest -Raw | ConvertFrom-Json
if($record.workspace -ne $workspace) { throw 'Manifest belongs to a different workspace.' }
function Check-Path([string]$Path) {
    $full=[IO.Path]::GetFullPath($Path)
    if(-not $full.StartsWith($workspace+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Cleanup target is outside the workspace.' }
    $relative=$full.Substring($workspace.Length+1)
    if($relative -notmatch '^(test-fixtures|backups|builds\\(?!current\\|mod-hub\\|azahar-x\\)[^\\]+|designs\\backups|downloads\\releases|builds\\azahar-x\\(src|CMakeFiles|externals)|melonDS-source-1\.1\\build)\\') { throw ('Target is not an allowed historical output: '+$relative) }
    if($relative -match '^builds\\azahar-x\\externals\\qt\\') { throw 'Qt dependencies are protected.' }
    $cursor=$full
    while($true) {
        if([IO.File]::GetAttributes($cursor) -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked cleanup path.' }
        if($cursor -eq $workspace) { break }
        $cursor=[IO.Path]::GetDirectoryName($cursor)
    }
}
foreach($entry in $record.files) {
    Check-Path $entry.path
    $file=[IO.FileInfo]::new($entry.path)
    # Python stat reports nanoseconds since Unix epoch; compare within filesystem precision.
    $ticksSinceEpoch=$file.LastWriteTimeUtc.Ticks-621355968000000000L
    if($file.Length -ne $entry.bytes -or [math]::Abs(($ticksSinceEpoch*100.0)-[double]$entry.mtime)>2000) { throw ('Source changed; cleanup cancelled: '+$entry.path) }
    if($entry.action -eq 'archive') {
        if(-not $entry.archive.StartsWith('F:\pokemon-workspace-archive\',[StringComparison]::OrdinalIgnoreCase) -or -not[IO.File]::Exists($entry.archive)) { throw 'Verified archive object is missing.' }
        if(-not $entry.entry -and [IO.FileInfo]::new($entry.archive).Length -ne $entry.bytes) { throw 'Archive object changed.' }
    } elseif($entry.action -ne 'discard') { throw 'Unknown cleanup action.' }
}
foreach($entry in $record.files) {
    Check-Path $entry.path
    $file=[IO.FileInfo]::new($entry.path)
    $ticksSinceEpoch=$file.LastWriteTimeUtc.Ticks-621355968000000000L
    if($file.Length -ne $entry.bytes -or [math]::Abs(($ticksSinceEpoch*100.0)-[double]$entry.mtime)>2000) { throw 'Source changed during cleanup.' }
    Remove-Item -LiteralPath $entry.path -Force
}
@{removedFiles=$record.files.Count;completed=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath ($Manifest+'.completed.json') -Encoding UTF8
Write-Host ('Removed '+$record.files.Count+' confirmed historical/generated files from C:.')
