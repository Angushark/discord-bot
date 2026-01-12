@echo off
echo ========================================
echo 啟動 Lavalink 音頻伺服器
echo ========================================
echo.

REM 檢查 Java 版本
java -version 2>&1 | findstr "version" > nul
if errorlevel 1 (
    echo [錯誤] 未找到 Java
    echo 請安裝 Java 17+: https://adoptium.net/
    echo.
    pause
    exit /b 1
)

REM 檢查 Lavalink.jar
if not exist "lavalink\Lavalink.jar" (
    echo [錯誤] 找不到 lavalink\Lavalink.jar
    echo 請下載: https://github.com/lavalink-devs/Lavalink/releases
    echo.
    pause
    exit /b 1
)

REM 進入 lavalink 目錄並啟動
cd lavalink
echo [提示] 啟動 Lavalink 伺服器...
echo [提示] 看到 "Lavalink is ready" 表示啟動成功
echo [提示] 按 Ctrl+C 停止伺服器
echo.
java -jar Lavalink.jar

REM 如果啟動失敗
if errorlevel 1 (
    echo.
    echo ========================================
    echo [錯誤] Lavalink 啟動失敗
    echo ========================================
    echo.
    echo 常見問題：
    echo 1. 端口 2333 被占用 - 執行 diagnose_lavalink.bat 診斷
    echo 2. 插件下載失敗 - 檢查網路連接
    echo 3. 配置文件錯誤 - 檢查 application.yml 語法
    echo.
    echo 查看詳細日誌：logs\*.log
    echo.
    pause
)
