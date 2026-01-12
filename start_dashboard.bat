@echo off
echo ========================================
echo Discord 音樂機器人 GUI 控制台
echo ========================================
echo.
echo 正在啟動控制台界面...
echo.
echo 快捷鍵：
echo   Q - 退出
echo   R - 手動刷新
echo   L - 清除日誌
echo   S - 保存日誌
echo.
echo ========================================
echo.

python dashboard.py

if errorlevel 1 (
    echo.
    echo [錯誤] 無法啟動控制台
    echo.
    echo 請檢查：
    echo 1. Python 是否正確安裝
    echo 2. 是否已安裝依賴：pip install -r requirements.txt
    echo 3. 機器人是否正在運行
    echo.
    pause
)
