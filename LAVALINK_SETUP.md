# Lavalink 設置指南

本音樂機器人使用 **Wavelink** 和 **Lavalink** 來播放音樂。Lavalink 是一個獨立的音頻伺服器，需要單獨運行。

## 📋 前置需求

1. **Java 17 或更高版本**
   - Windows: 下載 [Adoptium JDK](https://adoptium.net/)
   - Linux: `sudo apt install openjdk-17-jre`
   - macOS: `brew install openjdk@17`

2. **驗證 Java 安裝**
   ```bash
   java -version
   ```
   應該顯示 Java 17 或更高版本

## 🚀 快速設置

### 步驟 1: 下載 Lavalink

1. 訪問 [Lavalink Releases](https://github.com/lavalink-devs/Lavalink/releases)
2. 下載最新的 `Lavalink.jar` 文件
3. 在機器人目錄中創建 `lavalink` 資料夾
4. 將 `Lavalink.jar` 放入 `lavalink` 資料夾

### 步驟 2: 創建配置文件

在 `lavalink` 資料夾中創建 `application.yml` 文件，內容如下：

```yaml
server:
  port: 2333
  address: 0.0.0.0

lavalink:
  plugins:
    - dependency: "dev.lavalink.youtube:youtube-plugin:1.16.0"
      snapshot: false
  server:
    password: "youshallnotpass"
    sources:
      youtube: false  # 必須設為 false，使用插件而非內建源
      bandcamp: true
      soundcloud: true
      twitch: true
      vimeo: true
      http: true
      local: false
    filters:
      volume: true
      equalizer: true
      karaoke: true
      timescale: true
      tremolo: true
      vibrato: true
      distortion: true
      rotation: true
      channelMix: true
      lowPass: true
    bufferDurationMs: 400
    frameBufferDurationMs: 5000
    opusEncodingQuality: 10
    resamplingQuality: LOW
    trackStuckThresholdMs: 10000
    useSeekGhosting: true
    youtubePlaylistLoadLimit: 6
    playerUpdateInterval: 5
    youtubeSearchEnabled: true
    soundcloudSearchEnabled: true
    gc-warnings: true

plugins:
  youtube:
    enabled: true
    allowSearch: true
    allowDirectVideoIds: true
    allowDirectPlaylistIds: true
    clients:
      - ANDROID_MUSIC
      - MUSIC
      - WEB
      - TVHTML5EMBEDDED

metrics:
  prometheus:
    enabled: false
    endpoint: /metrics

sentry:
  dsn: ""
  environment: ""

logging:
  file:
    path: ./logs/

  level:
    root: INFO
    lavalink: INFO

  request:
    enabled: true
    includeClientInfo: true
    includeHeaders: false
    includeQueryString: true
    includePayload: true
    maxPayloadLength: 10000

  logback:
    rollingpolicy:
      max-file-size: 25MB
      max-history: 30
```

**重要配置說明：**
- `lavalink.plugins` - 宣告 YouTube 插件依賴（**必須**）
- `lavalink.server.sources.youtube: false` - **關鍵！** 必須設為 false 以禁用舊的內建 YouTube 源，強制使用新插件
- `plugins.youtube.enabled: true` - 啟用 YouTube 插件
- `plugins.youtube.clients` - 使用多個 YouTube 客戶端以提高成功率

**注意**: YouTube 插件 1.16.0 目前無法可靠播放 YouTube 影片（詳見下方「YouTube 播放限制」章節）

### 步驟 3: 啟動 Lavalink

在 `lavalink` 資料夾中打開終端/命令提示字元，執行：

```bash
java -jar Lavalink.jar
```

**成功啟動的訊息：**
```
INFO 12345 --- [           main] lavalink.server.Launcher                 : Started Launcher in X.XXX seconds
```

### 步驟 4: 保持 Lavalink 運行

Lavalink 必須在機器人運行期間保持運行。你可以：

1. **開發環境**: 在單獨的終端視窗中運行
2. **生產環境**: 使用 systemd (Linux) 或 PM2 自動管理

## 🔧 配置機器人連接

機器人已經配置為連接到本地 Lavalink：

```python
# 在 main_onlymusic.py 中
node: wavelink.Node = wavelink.Node(uri='http://localhost:2333', password='youshallnotpass')
```

如果你修改了 `application.yml` 中的端口或密碼，請相應修改 `main_onlymusic.py` 中的配置。

## ✅ 測試連接

1. 啟動 Lavalink 伺服器
2. 啟動機器人：`python main_onlymusic.py`
3. 查看日誌中是否出現：
   ```
   ✓ 已連接到 Lavalink 伺服器
   ```

如果看到錯誤訊息，請確認：
- Lavalink 正在運行
- 端口 2333 未被占用
- 密碼配置正確

## 🌐 遠端 Lavalink（可選）

如果你想使用遠端 Lavalink 伺服器，修改 `main_onlymusic.py`：

```python
node: wavelink.Node = wavelink.Node(
    uri='http://your-server-ip:2333',
    password='your-password'
)
```

## 📊 Lavalink 管理

### 查看日誌
日誌文件位於 `lavalink/logs/` 資料夾

### 停止 Lavalink
在運行 Lavalink 的終端中按 `Ctrl+C`

### 重啟 Lavalink
1. 停止 Lavalink (`Ctrl+C`)
2. 重新執行 `java -jar Lavalink.jar`

## ❓ 常見問題

**Q: Lavalink 無法啟動**
A: 確認 Java 版本是否為 17 或更高，執行 `java -version` 檢查

**Q: 機器人顯示 "無法連接到 Lavalink 伺服器"**
A: 確認 Lavalink 正在運行，並檢查端口 2333 是否開放

**Q: YouTube 影片無法播放（顯示 "Please sign in" 錯誤）**
A: 這是 YouTube 插件 1.16.0 的已知限制。請參考下方「YouTube 播放限制」章節

**Q: 需要同時運行機器人和 Lavalink 嗎？**
A: 是的，Lavalink 是獨立的音頻處理伺服器，必須與機器人同時運行

## ⚠️ YouTube 播放限制

### 當前狀況（2026-01 更新）

YouTube 插件 1.16.0 目前無法可靠播放 YouTube 影片，會出現以下錯誤：

```
com.sedmelluq.discord.lavaplayer.tools.FriendlyException: Please sign in
```

**錯誤表現**:
- 機器人可以成功加入語音頻道
- 可以載入影片的元數據（標題、作者等）
- 但播放時失敗，沒有聲音輸出
- 語音頭像不會亮起

### 原因分析

YouTube 在 2025-2026 年持續加強反爬蟲機制：
1. **簽名密鑰演算法更新**: YouTube 播放器腳本經常變化，插件無法解析
2. **需要認證**: YouTube 開始要求某些影片需要登入才能播放
3. **IP 速率限制**: 頻繁請求會被識別為機器人並封鎖

這是 **Lavalink 社群層級的已知問題**，不是配置錯誤。

### 已驗證可用的音樂來源

✅ **SoundCloud** - 完全正常運作（已測試）
✅ **Bandcamp** - 支援良好
✅ **Twitch** - 可播放直播和 VOD
✅ **Vimeo** - 支援
✅ **HTTP 直播串流** - 支援 .mp3, .m3u8 等格式

### 解決方案選項

#### 選項 1: 使用其他音樂平台（推薦）

**優點**: 立即可用，無需額外配置
**使用方式**:
```bash
# Discord 中使用
$play https://soundcloud.com/artist/track-name
$play https://artist.bandcamp.com/track/name
```

#### 選項 2: 等待社群更新

YouTube 插件開發者正在努力解決這個問題。定期檢查更新：
- [YouTube Plugin Releases](https://github.com/lavalink-devs/youtube-source/releases)
- 當新版本發布時，更新 `application.yml` 中的版本號並重啟 Lavalink

#### 選項 3: 配置 poToken（推薦嘗試）

**更新 (2026-01)**: poToken (Proof of Origin Token) 是目前繞過 YouTube 限制的有效方法。

**優點**:
- 無需 Google 帳號
- 不會有帳號被封風險
- 配置相對簡單

**缺點**:
- Token 有時效性，需定期更新（通常幾天到幾週）
- 只適用於 WEB 和 WEBEMBEDDED 客戶端

**設置步驟**:

1. **提取 poToken**（使用 YouTube Music）

   a. 開啟瀏覽器，訪問 [YouTube Music](https://music.youtube.com)

   b. 按 **F12** 打開開發者工具，切換到「**Network**」（網路）標籤

   c. 在過濾器中輸入 `v1/player`

   d. 播放任意一首歌曲

   e. 在 Network 標籤中找到 `player` 請求，點擊查看

   f. 查看「**Payload**」或「**Request**」內容

   g. 尋找並複製 `serviceIntegrityDimensions.poToken` 的值

   範例：
   ```json
   {
     "serviceIntegrityDimensions": {
       "poToken": "MgB...很長的字串...AwE"
     }
   }
   ```

2. **提取 visitorData**

   方法 1 - 使用控制台：
   - 在開發者工具切換到「**Console**」（控制台）標籤
   - 輸入以下命令並按 Enter：
     ```javascript
     ytcfg.get('VISITOR_DATA')
     ```
   - 複製輸出的值（通常是類似 `Cgt...` 開頭的字串）

   方法 2 - 查看 Cookie：
   - 在開發者工具切換到「**Application**」→「**Cookies**」
   - 找到 `VISITOR_INFO1_LIVE` cookie
   - 複製其值

3. **更新 application.yml**

   編輯 `lavalink/application.yml`，在 `plugins.youtube` 區塊中新增：

   ```yaml
   plugins:
     youtube:
       enabled: true
       # ... 其他設定 ...
       pot:
         token: "你提取的_poToken_值"
         visitorData: "你提取的_visitorData_值"
   ```

4. **重啟 Lavalink**

   ```bash
   # 停止 Lavalink (Ctrl+C)
   # 重新啟動
   java -jar Lavalink.jar
   ```

5. **測試播放**

   在 Discord 中測試：
   ```
   $play https://www.youtube.com/watch?v=VIDEO_ID
   ```

**Token 過期處理**:

當 token 過期（通常幾天後），YouTube 播放會再次失敗。此時只需：
1. 重複上述步驟獲取新的 poToken 和 visitorData
2. 更新 `application.yml`
3. 重啟 Lavalink

**自動化工具**（可選）:

如果你想自動化 token 更新，可以參考：
- [yt-dlp PO Token Guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide)
- 使用 bgutil-ytdlp-pot-provider 插件自動生成

#### 選項 4: OAuth2 認證（進階，不推薦）

**警告**: 這需要複雜的設置，且 YouTube 可能封鎖帳號

需要配置：
1. Google Cloud Console 建立 OAuth2 憑證
2. 獲取 refresh token
3. 在 `application.yml` 中配置認證資訊

由於成功率不高且有封號風險，**不推薦**此方案。

### 建議做法

**方案優先順序**:

1. **嘗試 poToken 配置**（選項 3）
   - 花費時間：5-10 分鐘
   - 成功率：中到高（取決於 YouTube 的當前限制）
   - 維護成本：需要定期更新 token（幾天到幾週）
   - **推薦給願意定期維護的用戶**

2. **使用 SoundCloud 等替代音源**（選項 1）
   - 花費時間：0（立即可用）
   - 成功率：100%
   - 維護成本：無
   - **推薦給想要穩定服務的用戶**

3. **等待插件更新**（選項 2）
   - 被動等待社群解決方案
   - 追蹤 [YouTube Plugin Releases](https://github.com/lavalink-devs/youtube-source/releases)

**實際部署建議**:

- **最佳策略**: 配置 poToken + 告知用戶 SoundCloud 作為備用
  - 當 YouTube 可用時享受其豐富內容
  - 當 token 過期時無縫切換到 SoundCloud
  - 定期（每週）檢查並更新 poToken

- **零維護策略**: 完全使用 SoundCloud
  - 告知 Discord 用戶優先使用 SoundCloud 連結
  - SoundCloud 有豐富的音樂資源且搜尋功能完善
  - Wavelink + Lavalink 架構本身運作正常

### 技術細節

如果你想查看詳細錯誤日誌：

```bash
# Lavalink 日誌位於
lavalink/logs/spring.log

# 典型錯誤訊息
ERROR [lava-daemon-pool-playback-1-thread-1] d.l.y.c.LocalSignatureCipherManager
: Problematic YouTube player script detected

WARN [lava-daemon-pool-playback-1-thread-1] c.s.d.l.t.p.LocalAudioTrackExecutor
: com.sedmelluq.discord.lavaplayer.tools.FriendlyException: Please sign in
```

這些錯誤表明插件無法解析 YouTube 的播放器腳本，這是插件層級的限制。

## 🔄 自動啟動（進階）

### Windows - 批次腳本

創建 `start_all.bat`：
```batch
@echo off
start "Lavalink Server" cmd /k "cd lavalink && java -jar Lavalink.jar"
timeout /t 10
python main_onlymusic.py
```

### Linux - systemd 服務

創建 `/etc/systemd/system/lavalink.service`：
```ini
[Unit]
Description=Lavalink Music Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/discordbot/lavalink
ExecStart=/usr/bin/java -jar Lavalink.jar
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

啟用並啟動：
```bash
sudo systemctl enable lavalink
sudo systemctl start lavalink
```

## 📚 更多資源

- [Lavalink GitHub](https://github.com/lavalink-devs/Lavalink)
- [Wavelink 文件](https://wavelink.dev/)
- [Discord.py 文件](https://discordpy.readthedocs.io/)

---

**注意**: Lavalink 需要穩定的網路連接來串流音樂。建議在伺服器環境中運行以獲得最佳性能。
