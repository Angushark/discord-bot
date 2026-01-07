# 🎵 Discord 音樂機器人

一個功能完整的 Discord 音樂機器人，支援 YouTube 音樂播放、歌單循環、單曲重複等功能。

## ✨ 主要功能

- 🎵 播放音樂（支援 SoundCloud、Bandcamp、Twitch、Vimeo 等）
- ⚠️ YouTube 播放（目前受限於 YouTube 反爬蟲機制，建議使用其他音源）
- 🔁 歌單循環模式
- 🔂 單曲重複模式
- ⏸️ 暫停/繼續播放
- ⏭️ 跳過歌曲
- 📜 播放佇列管理
- 🎮 互動式控制面板
- 📝 完整的日誌記錄
- 🔄 自動錯誤重試
- 🔒 環境變數安全管理

## 🚀 快速開始

### 前置需求

1. **Python 3.8+**
2. **Java 17+** - Lavalink 伺服器需要
   - Windows: [下載 Adoptium JDK](https://adoptium.net/)
   - Linux: `sudo apt-get install openjdk-17-jre`
   - macOS: `brew install openjdk@17`
3. **Lavalink 伺服器** - 音頻處理伺服器（詳見下方設置步驟）
4. **Discord Bot Token** - 從 [Discord Developer Portal](https://discord.com/developers/applications) 獲取

### 安裝步驟

1. **克隆或下載此專案**

2. **安裝 Python 依賴**
```bash
pip install -r requirements.txt
```

3. **設置 Lavalink 伺服器**
```bash
# 創建 Lavalink 資料夾
mkdir lavalink
cd lavalink

# 下載 Lavalink.jar
# 請訪問 https://github.com/lavalink-devs/Lavalink/releases
# 下載最新版本的 Lavalink.jar 並放入 lavalink 資料夾

# 創建配置文件（詳見 LAVALINK_SETUP.md）
```
**詳細的 Lavalink 設置說明請參考 [LAVALINK_SETUP.md](LAVALINK_SETUP.md)**

4. **設定環境變數**
```bash
# 複製環境變數模板
cp .env.example .env

# 編輯 .env 文件，填入你的 Bot Token
# DISCORD_BOT_TOKEN=your_actual_token_here
```

5. **啟動 Lavalink 伺服器**
```bash
# 在 lavalink 資料夾中
cd lavalink
java -jar Lavalink.jar
```

6. **啟動機器人**（在新的終端視窗）
```bash
python main_onlymusic.py
```

## 📝 指令列表

| 指令 | 說明 |
|------|------|
| `$play [URL]` | 播放音樂（支援 YouTube, SoundCloud, Bandcamp 等） |
| `$skip` | 跳過當前歌曲 |
| `$repeat` | 切換重複模式（單曲重複 ↔ 歌單循環） |
| `$queue` | 顯示播放佇列 |
| `$nowplaying` | 顯示當前播放歌曲 |
| `$control` | 顯示音樂控制面板 |
| `$pause` | 暫停播放 |
| `$resume` | 繼續播放 |
| `$volume [0-100]` | 設定播放音量（不填顯示當前音量） |
| `$stop` | 停止播放並清除佇列 |
| `$remove [數字]` | 移除佇列中指定位置的歌曲 |
| `$clear` | 清除播放佇列 |
| `$join` | 加入你所在的語音頻道 |
| `$leave` | 退出語音頻道 |
| `$help` | 顯示幫助訊息 |

## 🎮 使用方式

1. **加入語音頻道**
   - 在 Discord 中加入一個語音頻道
   - 使用 `$join` 讓機器人加入，或直接使用 `$play [URL]` 自動加入

2. **播放音樂**
   ```
   # SoundCloud (推薦 - 穩定可用)
   $play https://soundcloud.com/artist/track-name

   # YouTube (可能受限)
   $play https://www.youtube.com/watch?v=VIDEO_ID

   # Bandcamp
   $play https://artist.bandcamp.com/track/track-name
   ```

3. **切換播放模式**
   - 使用 `$repeat` 在歌單循環（🔁）和單曲重複（🔂）之間切換

4. **使用控制面板**
   - 使用 `$control` 顯示互動式控制面板
   - 點擊按鈕進行操作（暫停、跳過、切換模式等）

## 🔧 配置

### Discord 機器人權限

機器人需要以下權限：
- ✅ 連接語音頻道
- ✅ 在語音頻道中說話
- ✅ 發送消息
- ✅ 嵌入連結
- ✅ 讀取消息歷史

### 環境變數

在 `.env` 文件中配置：
```env
DISCORD_BOT_TOKEN=your_bot_token_here
```

## 📊 日誌

日誌文件位於 `logs/music_bot.log`

**特性：**
- 自動輪轉（每個文件最大 5MB）
- 保留最近 5 個日誌文件
- 記錄所有操作和錯誤

**查看日誌：**
```bash
# Windows
type logs\music_bot.log

# Linux/macOS
cat logs/music_bot.log
tail -f logs/music_bot.log  # 實時查看
```

## ❓ 常見問題

**Q: 機器人無法啟動**
A: 確認 `.env` 文件中的 `DISCORD_BOT_TOKEN` 是否正確設定

**Q: 顯示 "無法連接到 Lavalink 伺服器"**
A:
   1. 確認 Lavalink 正在運行（在單獨的終端視窗中執行 `java -jar Lavalink.jar`）
   2. 確認 Java 版本為 17 或更高（執行 `java -version` 檢查）
   3. 確認端口 2333 未被其他程序占用
   4. 查看 [LAVALINK_SETUP.md](LAVALINK_SETUP.md) 獲取詳細設置指南

**Q: 無法播放音樂或聽不到聲音**
A:
   1. 確認 Lavalink 伺服器正在運行
   2. 檢查機器人日誌中是否顯示 "✓ 已連接到 Lavalink 伺服器"
   3. 查看 Lavalink 日誌（在 `lavalink/logs/` 資料夾）是否有錯誤

**Q: Java 相關錯誤**
A: 確保安裝了 Java 17 或更高版本，執行 `java -version` 檢查

**Q: 播放中途斷開**
A:
   1. 檢查網路連接
   2. 確認 Lavalink 伺服器未崩潰
   3. 查看日誌文件中的錯誤訊息

**Q: YouTube 影片無法播放（顯示 "Please sign in" 錯誤）**
A: 這是 YouTube 插件 1.16.0 的已知限制（2026-01 更新）
   - **原因**: YouTube 加強了反爬蟲機制，需要更複雜的認證
   - **建議方案**:
     1. 優先使用 **SoundCloud**（已驗證可正常運作）
     2. 使用 Bandcamp、Twitch、Vimeo 等其他平台
     3. 等待 YouTube 插件社群更新
   - 查看 [LAVALINK_SETUP.md](LAVALINK_SETUP.md) 中的「YouTube 播放限制」章節了解詳情

**Q: SoundCloud 或其他平台可以播放嗎？**
A: 可以！SoundCloud、Bandcamp、Twitch、Vimeo 等平台都能正常播放。機器人的 Wavelink + Lavalink 架構運作正常，只有 YouTube 目前受限

## 🔄 更新日誌

詳見 [claude.md](claude.md) 文件

**最新版本 v2.0.0 (2026-01-06)**
- 🎉 **重大更新：完全重寫為 Wavelink + Lavalink 架構**
- ✅ 移除 yt-dlp + FFmpeg，改用 Lavalink 音頻伺服器
- ✅ 完美解決 HLS 串流播放問題
- ✅ 更穩定的音頻播放體驗
- ✅ 更好的性能和資源管理
- ✅ 保持所有原有用戶端功能不變
- ✅ 支援 YouTube、SoundCloud、Twitch 等多個平台
- 📚 新增完整的 Lavalink 設置指南

## 📜 授權

本項目僅供學習和個人使用。使用本機器人時請遵守：
- Discord 服務條款
- YouTube 使用政策
- 相關版權法規

## 🤝 貢獻

歡迎提交問題報告和功能建議！請查看 [claude.md](claude.md) 了解更多詳情。

---

**注意：** 本機器人需要穩定的網路連接才能正常運作。建議在伺服器或穩定的環境中運行。
