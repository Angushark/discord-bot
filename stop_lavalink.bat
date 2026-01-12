@echo off
echo ========================================
echo 停止 Lavalink 伺服器
echo ========================================
echo.

echo 正在查找 Lavalink 進程...
netstat -ano | findstr :2333 > nul

if errorlevel 1 (
    echo [提示] 沒有找到運行中的 Lavalink 進程
    echo 端口 2333 未被占用
    echo.
    pause
    exit /b 0
)

echo 找到占用端口 2333 的進程：
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :2333 ^| findstr LISTENING') do (
    set PID=%%a
    goto :found
)

:found
echo 進程 ID: %PID%

echo.
echo 正在停止進程...
taskkill /PID %PID% /F

if errorlevel 1 (
    echo [錯誤] 無法停止進程
    echo 請手動關閉或使用管理員權限運行此腳本
    pause
    exit /b 1
)

echo [✓] Lavalink 已停止
echo.

REM 驗證端口已釋放
timeout /t 2 > nul
netstat -ano | findstr :2333 > nul

if errorlevel 1 (
    echo [✓] 端口 2333 已釋放，可以重新啟動 Lavalink
) else (
    echo [警告] 端口仍被占用，請稍後再試
)

echo.
pause
