# Lavalink 設置說明

這個目錄用於存放 Lavalink 伺服器文件。

## 需要下載的文件

### 1. Lavalink.jar (必須)

從官方 GitHub 下載最新版本：
```
https://github.com/lavalink-devs/Lavalink/releases
```

建議版本：**v4.1.2** 或更新版本

下載後將 `Lavalink.jar` 放到這個目錄。

### 2. LavaSrc Plugin (必須 - 用於 YouTube 支援)

從 GitHub 下載：
```
https://github.com/topi314/LavaSrc/releases
```

建議版本：**v4.8.1** 或更新版本

下載後將 `lavasrc-plugin-4.8.1.jar` 放到 `plugins/` 子目錄。

## 配置文件

`application.yml` - Lavalink 伺服器配置（已包含，無需下載）

## 目錄結構

完成後應該是這樣：

```
lavalink/
├── README.md              (本文件)
├── application.yml        (已包含)
├── Lavalink.jar          (需要下載)
├── logs/                 (自動生成)
└── plugins/
    └── lavasrc-plugin-4.8.1.jar  (需要下載)
```

## 啟動 Lavalink

```bash
cd lavalink
java -jar Lavalink.jar
```

**注意**：需要 Java 17 或更新版本。

## 詳細設置指南

請參考根目錄的 [LAVALINK_SETUP.md](../LAVALINK_SETUP.md) 獲取完整的安裝和配置說明。
