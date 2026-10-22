"""Safely stop an outdated local relay owned by this installation."""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import subprocess
import sys


class RelayProcessError(RuntimeError):
    """Raised when Windows cannot safely identify or stop a managed relay."""


def _stop_script(home: Path, port: int) -> str:
    encoded_root = base64.b64encode(str(home.resolve()).encode('utf-16le')).decode('ascii')
    return f"""
$ErrorActionPreference = 'Stop'
$managedRoot = [Text.Encoding]::Unicode.GetString([Convert]::FromBase64String('{encoded_root}')).TrimEnd('\\')
$prefix = $managedRoot + '\\'
$port = {port}
$portPattern = '(?:^|\\s)--presence-relay\\s+' + [regex]::Escape([string]$port) + '(?:\\s|$)'
$legacyScript = Join-Path (Join-Path $managedRoot 'tools') 'presence_server.py'
$legacyScriptPattern = '(?:^|\\s)"?' + [regex]::Escape($legacyScript) + '"?(?=\\s|$)'
$legacyArgsPattern = '(?:^|\\s)--host\\s+0\\.0\\.0\\.0\\s+--port\\s+' + [regex]::Escape([string]$port) + '(?:\\s|$)'
$legacyLauncher = Join-Path (Join-Path $managedRoot 'tools') 'unova_launcher.py'
$legacyLauncherPattern = '(?:^|\\s)"?' + [regex]::Escape($legacyLauncher) + '"?(?=\\s|$)'
$owners = @(Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique)
$results = @()
foreach ($ownerId in $owners) {{
    if ($ownerId -eq $PID) {{ continue }}
    $process = Get-CimInstance -ClassName Win32_Process -Filter (\"ProcessId = {{0}}\" -f $ownerId) -ErrorAction SilentlyContinue
    if ($null -eq $process -or !$process.ExecutablePath -or !$process.CommandLine) {{ continue }}
    try {{ $fullPath = [IO.Path]::GetFullPath($process.ExecutablePath) }} catch {{ continue }}
    $launcherRelay = $false
    if ($fullPath.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {{
        $parts = $fullPath.Substring($prefix.Length).Split([IO.Path]::DirectorySeparatorChar)
        $layoutMatches = ($parts.Length -eq 2 -and $parts[0] -ieq 'launcher') -or
            ($parts.Length -eq 6 -and $parts[0] -ieq '.updates' -and $parts[1] -ieq 'versions' -and
             $parts[3] -ieq 'Unova-Together' -and $parts[4] -ieq 'launcher')
        $fileName = [IO.Path]::GetFileName($fullPath)
        $nameMatches = $fileName -ieq 'Pokemon Together.exe' -or $fileName -ieq 'Unova Together.exe'
        $launcherRelay = $layoutMatches -and $nameMatches -and $process.CommandLine -match $portPattern
    }}
    # Older game builds launched presence_server.py with Python. Its interpreter
    # is outside the install, so identify it by the exact installed script and
    # argument sequence before treating it as owned.
    $pythonName = [IO.Path]::GetFileName($fullPath)
    $legacyPythonServer = $process.CommandLine -match $legacyScriptPattern -and
        $process.CommandLine -match $legacyArgsPattern
    $legacyPythonLauncher = $process.CommandLine -match $legacyLauncherPattern -and
        $process.CommandLine -match $portPattern
    $legacyPythonRelay = ($pythonName -ieq 'python.exe' -or $pythonName -ieq 'pythonw.exe') -and
        ($legacyPythonServer -or $legacyPythonLauncher)
    if (!$launcherRelay -and !$legacyPythonRelay) {{
        $results += [pscustomobject]@{{owned=$false;stopped=$false}}
        continue
    }}
    $stopped = $false
    try {{
        $result = Invoke-CimMethod -InputObject $process -MethodName Terminate -Arguments @{{Reason=[uint32]0}}
        $stopped = ($result.ReturnValue -eq 0)
    }} catch {{ $stopped = $false }}
    $results += [pscustomobject]@{{owned=$true;stopped=$stopped}}
}}
ConvertTo-Json -InputObject @($results) -Compress
"""


def stop_owned_listener(home: str | Path, port: int) -> bool:
    """Stop only a relay process started from this installation.

    Current builds run the packaged launcher with ``--presence-relay``. Older
    game builds ran Python against this install's exact ``tools/presence_server.py``
    with fixed host/port arguments; source launchers used ``tools/unova_launcher.py``
    with ``--presence-relay``. The listener PID and process identity are checked
    together, then termination is invoked on that queried process.
    """
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError('Relay port must be between 1 and 65535.')
    if sys.platform != 'win32':
        raise RelayProcessError('Automatic relay replacement is available only on Windows.')
    try:
        root = Path(home).resolve(strict=True)
    except (OSError, TypeError, ValueError) as exc:
        raise RelayProcessError('Cannot verify this launcher installation folder.') from exc
    if not root.is_dir():
        raise RelayProcessError('Cannot verify this launcher installation folder.')
    command = [
        'powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
        '-Command', _stop_script(root, port),
    ]
    try:
        completed = subprocess.run(command, capture_output=True, text=True,
                                   timeout=12, check=False, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except (OSError, subprocess.SubprocessError) as exc:
        raise RelayProcessError('Windows could not inspect the local relay process safely.') from exc
    if completed.returncode:
        raise RelayProcessError('Windows could not inspect the local relay process safely.')
    try:
        result = json.loads(completed.stdout.strip() or '[]')
    except (TypeError, json.JSONDecodeError) as exc:
        raise RelayProcessError('Windows returned an invalid local relay status.') from exc
    entries = result if isinstance(result, list) else [result]
    if not entries:
        return False
    if any(not isinstance(entry, dict) for entry in entries):
        raise RelayProcessError('Windows returned an invalid local relay status.')
    if any(entry.get('owned') is not True for entry in entries):
        raise RelayProcessError('A relay is listening on this port, but it was not started by this installation.')
    if any(entry.get('stopped') is not True for entry in entries):
        raise RelayProcessError('The outdated relay belongs to this installation but Windows could not stop it.')
    return True
