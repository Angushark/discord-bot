@echo off
echo ========================================
echo Lavalink 診斷工具
echo ========================================
echo.

echo [1/5] 檢查 Java 版本...
java -version 2>&1 | findstr "version"
if errorlevel 1 (
    echo [錯誤] Java 未安裝或未加入 PATH
    echo 請安裝 Java 17+: https://adoptium.net/
    pause
    exit /b 1
)
echo [✓] Java 已安裝
echo.

echo [2/5] 檢查 Lavalink.jar 文件...
if not exist "lavalink\Lavalink.jar" (
    echo [錯誤] 找不到 Lavalink.jar
    echo 請下載: https://github.com/lavalink-devs/Lavalink/releases
    pause
    exit /b 1
)
echo [✓] Lavalink.jar 存在
echo.

echo [3/5] 檢查 application.yml 配置...
if not exist "lavalink\application.yml" (
    echo [錯誤] 找不到 application.yml
    echo 請參考 LAVALINK_SETUP.md 創建配置文件
    pause
    exit /b 1
)
echo [✓] application.yml 存在
echo.

echo [4/5] 檢查端口 2333 是否被占用...
netstat -ano | findstr ":2333" > nul
if not errorlevel 1 (
    echo [警告] 端口 2333 已被占用
    echo 占用端口的進程：
    netstat -ano | findstr ":2333"
    echo.
    echo 解決方案：
    echo 1. 關閉占用端口的程序
    echo 2. 或修改 lavalink\application.yml 中的端口號
    echo.
) else (
    echo [✓] 端口 2333 可用
)
echo.

echo [5/5] 嘗試啟動 Lavalink...
echo 輸出將保存到 lavalink\startup_log.txt
echo 按 Ctrl+C 停止
echo.
cd lavalink
java -jar Lavalink.jar 2>&1 | tee startup_log.txt

pause
