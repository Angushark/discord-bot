@echo off
echo ========================================
echo   Discord 音樂機器人 - GUI 監控界面
echo   (Tkinter 桌面版本)
echo ========================================
echo.
echo 正在啟動 GUI...
echo.

python dashboard_tkinter.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo [錯誤] 無法啟動 GUI
    echo ========================================
    echo.
    echo 請檢查：
    echo 1. Python 是否正確安裝
    echo 2. 是否已啟動機器人 (python main_onlymusic.py)
    echo 3. 是否存在 bot_status.json 文件
    echo.
    pause
)
