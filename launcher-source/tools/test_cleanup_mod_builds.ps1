# Exercise the real cleanup script against isolated disposable files only.
$ErrorActionPreference='Stop'
$workspace=Split-Path -Parent $PSScriptRoot
$fixture=Join-Path $workspace ('test-fixtures\cleanup-safety-'+[guid]::NewGuid().ToString('N'))
$script=Join-Path $PSScriptRoot 'cleanup_mod_builds.ps1'
function Put([string]$Relative,[string]$Contents='fixture') {
    $path=Join-Path $fixture $Relative
    New-Item -ItemType Directory -Path (Split-Path $path) -Force | Out-Null
    Set-Content -LiteralPath $path -Value $Contents
}
function Check([bool]$Condition,[string]$Message) { if(-not $Condition) { throw $Message } }
Put 'project\tools\launcher_ui\game_routes.py'
Put 'x\profiles\pokemon-x-base.research.json'
Put 'unova\builds\current\melonDS.exe'
Put 'project\builds\release-1.0.1\Unova-Together\builds\current\old.dll'
Put 'project\builds\release-1.0.1\Unova-Together\builds\current\user\keep.dll'
Put 'project\builds\release-1.0.1\Unova-Together\player.save' 'private save'
Put 'project\builds\release-1.0.4\Unova-Together\builds\current\rollback.dll'
Put 'project\builds\current\current.dll'
Put 'project\builds\azahar-x\bundle\azahar.exe'
Put 'project\builds\azahar-x\bin\Release\PokemonXResearch.exe'
Put 'project\builds\azahar-x\src\CMakeFiles\example.obj'
Put 'x\tools\__pycache__\example.pyc'
Put 'outside\sentinel.dll'
$arguments=@{Workspace=(Join-Path $fixture 'project');PokemonXRoot=(Join-Path $fixture 'x');UnovaRoot=(Join-Path $fixture 'unova')}
& $script @arguments | Out-Null
Check (Test-Path -LiteralPath (Join-Path $fixture 'project\builds\azahar-x\bundle\azahar.exe')) 'Preview deleted a file.'
& $script @arguments -Apply -WhatIf | Out-Null
Check (Test-Path -LiteralPath (Join-Path $fixture 'x\tools\__pycache__\example.pyc')) 'WhatIf deleted a file.'
& $script @arguments -Apply | Out-Null
Check (-not(Test-Path -LiteralPath (Join-Path $fixture 'project\builds\release-1.0.1\Unova-Together\builds\current\old.dll'))) 'Legacy binary was not cleaned.'
foreach($relative in @('project\builds\release-1.0.1\Unova-Together\builds\current\user\keep.dll','project\builds\release-1.0.1\Unova-Together\player.save','project\builds\release-1.0.4\Unova-Together\builds\current\rollback.dll','project\builds\current\current.dll','project\builds\azahar-x\bin\Release\PokemonXResearch.exe','project\builds\azahar-x\src\CMakeFiles\example.obj','unova\builds\current\melonDS.exe','outside\sentinel.dll')) {
    Check (Test-Path -LiteralPath (Join-Path $fixture $relative)) ('Protected file removed: '+$relative)
}
& $script @arguments -Apply -IncludeCompilerOutputs | Out-Null
Check (-not(Test-Path -LiteralPath (Join-Path $fixture 'project\builds\azahar-x\src\CMakeFiles\example.obj'))) 'Optional compiler cleanup failed.'
$link=Join-Path $fixture 'project\builds\release-1.0.2'
New-Item -ItemType Junction -Path $link -Target (Join-Path $fixture 'outside') | Out-Null
$rejected=$false
try { & $script @arguments -Apply | Out-Null } catch { $rejected=$_.Exception.Message -like '*Linked*' }
Check $rejected 'Cleanup did not reject a junction.'
Check (Test-Path -LiteralPath (Join-Path $fixture 'outside\sentinel.dll')) 'Junction escaped the project.'
Write-Host ('Cleanup safety checks passed. Disposable evidence: '+$fixture)
