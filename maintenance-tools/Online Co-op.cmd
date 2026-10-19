@echo off
cd /d "%~dp0"
call tools\run-python.cmd tools\online_udp_bridge.py --wizard
if errorlevel 1 (
    echo If cryptography is missing, run Install UDP Dependencies.cmd first.
    pause
)
