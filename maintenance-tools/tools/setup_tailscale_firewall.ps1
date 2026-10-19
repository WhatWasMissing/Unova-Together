# Run as Administrator. Permit only the two PokePlay ports from Tailscale IPv4.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$statusPath = Join-Path $projectRoot 'transfer/tailscale-firewall-status.json'
New-Item -ItemType Directory -Force (Split-Path -Parent $statusPath) | Out-Null
try {
    $emulatorPath = Join-Path $projectRoot 'builds/current/melonDS.exe'
    if (-not (Test-Path -LiteralPath $emulatorPath)) { throw 'Current emulator is missing.' }
    $nativeRule = 'PokePlay-Tailscale-Native'
    $presenceRule = 'PokePlay-Tailscale-Presence'
    if (-not (Get-NetFirewallRule -Name $nativeRule -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule -Name $nativeRule -DisplayName 'PokePlay native wireless over Tailscale' `
            -Direction Inbound -Action Allow -Enabled True -Profile Any -Protocol UDP `
            -LocalPort 7064 -RemoteAddress '100.64.0.0/10' -Program $emulatorPath | Out-Null
    } else {
        Get-NetFirewallRule -Name $nativeRule | Get-NetFirewallApplicationFilter |
            Set-NetFirewallApplicationFilter -Program $emulatorPath | Out-Null
    }
    if (-not (Get-NetFirewallRule -Name $presenceRule -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule -Name $presenceRule -DisplayName 'PokePlay presence over Tailscale' `
            -Direction Inbound -Action Allow -Enabled True -Profile Any -Protocol TCP `
            -LocalPort 8765 -RemoteAddress '100.64.0.0/10' | Out-Null
    }
    @{ok=$true; nativePort=7064; presencePort=8765} | ConvertTo-Json | Set-Content -LiteralPath $statusPath
} catch {
    @{ok=$false; error=$_.Exception.Message} | ConvertTo-Json | Set-Content -LiteralPath $statusPath
    exit 1
}
