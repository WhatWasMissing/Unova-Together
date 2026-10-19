@echo off
cd /d "%~dp0"
echo Starting the Pokeplay LAN presence relay on TCP port 8765.
echo Leave this window open while playing. Press Ctrl+C to stop.
call tools\run-python.cmd -c "import socket,sys; s=socket.socket(); sys.exit(0 if s.connect_ex(('127.0.0.1',8765)) == 0 else 1)"
if not errorlevel 1 (
    echo Port 8765 is already accepting connections. If the relay is running, connect to 127.0.0.1:8765.
    pause
    exit /b
)
call tools\run-python.cmd tools\presence_server.py --host 0.0.0.0 --port 8765
pause
