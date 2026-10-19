@echo off
where py >nul 2>nul
if not errorlevel 1 (
    py -3 %*
    exit /b
)
if exist "%LocalAppData%\Programs\Python\Launcher\py.exe" (
    "%LocalAppData%\Programs\Python\Launcher\py.exe" -3 %*
    exit /b
)
where python >nul 2>nul
if not errorlevel 1 (
    python %*
    exit /b
)
echo Python was not found. Install Python 3, then try again.
exit /b 1
