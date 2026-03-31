@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM hq_job server 管理脚本
REM 用法: start.bat [start|stop|restart|status]

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "PID_FILE=%SCRIPT_DIR%\hq_job.pid"
set "LOG_FILE=%SCRIPT_DIR%\hq_job.log"

REM 环境变量配置
set "AUTODL_TOKEN=eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjY3MzAyNCwidXVpZCI6IjUxNWEyNzg5ZDgwMzdlZmEiLCJpc19hZG1pbiI6ZmFsc2UsImJhY2tzdGFnZV9yb2xlIjoiIiwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJzdWJfbmFtZSI6IiIsInRlbmFudCI6ImF1dG9kbCIsInVwayI6IiJ9.Z7ehfhzgIStE3_7RTiinhlkYxGA2i1yoPZbWce9DFiQt4iTuenJWJP4V0iT45VGCWTcS43Lw4iZKwYD7APxfzw"
set "API_TOKEN=foresee_hq_job"
set "HQJOB_COS_PREFIX=cos://autodl"

if "%1"=="" goto usage
if "%1"=="start" goto start
if "%1"=="stop" goto stop
if "%1"=="restart" goto restart
if "%1"=="status" goto status
goto usage

:start
if not exist "%PID_FILE%" goto do_start

set /p OLD_PID=<"%PID_FILE%"
tasklist /FI "PID eq %OLD_PID%" 2>nul | find /I "%OLD_PID%" >nul
if %errorlevel%==0 (
    echo hq_job server 已经在运行中 ^(PID: %OLD_PID%^)
    exit /b 1
) else (
    del /f "%PID_FILE%" 2>nul
)

:do_start
cd /d "%SCRIPT_DIR%"
echo 正在启动 hq_job server...

REM 创建启动脚本
set "LAUNCHER=%SCRIPT_DIR%\hq_job_launcher.bat"
echo @echo off > "%LAUNCHER%"
echo cd /d "%%~dp0" >> "%LAUNCHER%"
echo python -m hq_job.server ^>^> "%%~dp0hq_job.log" 2^>^&1 >> "%LAUNCHER%"

REM 使用 start /b 在后台运行，通过 wmic 获取 PID
start /b "" cmd /c "%LAUNCHER%"

timeout /t 2 /nobreak >nul

REM 查找 python 进程的 PID
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| find "PID:"') do set PID=%%i

if defined PID (
    echo %PID%> "%PID_FILE%"
    echo hq_job server 启动成功 ^(PID: %PID%^)
    echo 日志文件: %LOG_FILE%
) else (
    echo hq_job server 启动失败，请查看日志: %LOG_FILE%
    exit /b 1
)
goto end

:stop
if not exist "%PID_FILE%" (
    echo PID 文件不存在，服务可能未运行
    goto end
)

set /p PID=<"%PID_FILE%"
tasklist /FI "PID eq %PID%" 2>nul | find /I "%PID%" >nul
if %errorlevel% neq 0 (
    echo 进程 %PID% 不存在，清理 PID 文件
    del /f "%PID_FILE%" 2>nul
    goto end
)

echo 正在停止 hq_job server ^(PID: %PID%^)...
taskkill /PID %PID% /F >nul 2>&1

del /f "%PID_FILE%" 2>nul
echo hq_job server 已停止
goto end

:restart
call :stop
timeout /t 1 /nobreak >nul
call :start
goto end

:status
if exist "%PID_FILE%" (
    set /p PID=<"%PID_FILE%"
    tasklist /FI "PID eq !PID!" 2>nul | find /I "!PID!" >nul
    if !errorlevel!==0 (
        echo hq_job server 正在运行 ^(PID: !PID!^)
    ) else (
        echo hq_job server 未运行 ^(PID 文件存在但进程不存在^)
    )
) else (
    echo hq_job server 未运行
)
goto end

:usage
echo 用法: %~nx0 {start^|stop^|restart^|status}
exit /b 1

:end
endlocal
