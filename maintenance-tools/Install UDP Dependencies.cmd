@echo off
cd /d "%~dp0"
call tools\run-python.cmd -m pip install -r tools\requirements-online-udp.txt
if errorlevel 1 (
    echo Installation failed. Check Python and your internet connection.
) else (
    echo UDP dependencies installed. Run Online Co-op.cmd.
)
pause
