# Lavalink Plugins

這個目錄用於存放 Lavalink 插件。

## 需要的插件

### LavaSrc Plugin (必須)

**用途**：提供 YouTube、Spotify、SoundCloud 等平台支援

**下載地址**：
```
https://github.com/topi314/LavaSrc/releases
```

**建議版本**：v4.8.1 或更新版本

**安裝方法**：
1. 下載 `lavasrc-plugin-4.8.1.jar`
2. 放到這個目錄（`lavalink/plugins/`）
3. 重啟 Lavalink 伺服器

## 已安裝的插件

啟動 Lavalink 後，你會在日誌中看到：

```
INFO 12345 --- [main] lavalink.server.Launcher: Lavalink v4.1.2
INFO 12345 --- [main] c.s.l.p.PluginManager: Loading plugin: lavasrc-plugin-4.8.1
```

## 其他可選插件

你可以在這裡找到更多 Lavalink 插件：
- https://lavalink.dev/plugins

常見插件：
- **LavaSearch** - 搜索功能增強
- **LavaLyrics** - 歌詞顯示
- **LavaLink-Filter-Plugin** - 音效過濾器

## 注意事項

- 插件必須與你的 Lavalink 版本兼容
- 修改插件後需要重啟 Lavalink 伺服器
- 某些插件可能需要額外的配置（在 `application.yml` 中）
