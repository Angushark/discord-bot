"""
Discord 音樂機器人 - Tkinter GUI 監控界面
使用 Tkinter 創建桌面 GUI 用於實時監控機器人狀態
"""

import tkinter as tk
from tkinter import ttk
import json
import threading
import queue
from pathlib import Path
from datetime import datetime
import time


# ==================== UI 組件類 ====================

class BotStatusFrame(ttk.LabelFrame):
    """機器人狀態顯示框架"""

    def __init__(self, parent):
        super().__init__(parent, text="🤖 機器人狀態", padding=10)

        # 使用 StringVar 實現數據綁定
        self.bot_status_var = tk.StringVar(value="❌ 離線")
        self.lavalink_status_var = tk.StringVar(value="❌ 未連接")
        self.guild_count_var = tk.StringVar(value="0")
        self.voice_conn_var = tk.StringVar(value="0")

        # 創建標籤並綁定變數
        tk.Label(self, text="狀態:", font=("Arial", 10, "bold"), bg="#f0f0f0", anchor="w").grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=(0, 10)
        )
        tk.Label(self, textvariable=self.bot_status_var, font=("Arial", 10), bg="#f0f0f0", anchor="w").grid(
            row=0, column=1, sticky=tk.W, pady=5
        )

        tk.Label(self, text="Lavalink:", font=("Arial", 10, "bold"), bg="#f0f0f0", anchor="w").grid(
            row=1, column=0, sticky=tk.W, pady=5, padx=(0, 10)
        )
        tk.Label(self, textvariable=self.lavalink_status_var, font=("Arial", 10), bg="#f0f0f0", anchor="w").grid(
            row=1, column=1, sticky=tk.W, pady=5
        )

        tk.Label(self, text="伺服器數:", font=("Arial", 10, "bold"), bg="#f0f0f0", anchor="w").grid(
            row=2, column=0, sticky=tk.W, pady=5, padx=(0, 10)
        )
        tk.Label(self, textvariable=self.guild_count_var, font=("Arial", 10), bg="#f0f0f0", anchor="w").grid(
            row=2, column=1, sticky=tk.W, pady=5
        )

        tk.Label(self, text="語音連接:", font=("Arial", 10, "bold"), bg="#f0f0f0", anchor="w").grid(
            row=3, column=0, sticky=tk.W, pady=5, padx=(0, 10)
        )
        tk.Label(self, textvariable=self.voice_conn_var, font=("Arial", 10), bg="#f0f0f0", anchor="w").grid(
            row=3, column=1, sticky=tk.W, pady=5
        )

        self.configure(style="Custom.TLabelframe")

    def update_data(self, data):
        """更新顯示數據（從主線程調用）"""
        bot_online = data.get('bot_online', False)
        lavalink_online = data.get('lavalink_online', False)

        self.bot_status_var.set("✅ 在線" if bot_online else "❌ 離線")
        self.lavalink_status_var.set("✅ 已連接 (localhost:2333)" if lavalink_online else "❌ 未連接")
        self.guild_count_var.set(str(data.get('guild_count', 0)))
        self.voice_conn_var.set(str(data.get('voice_connections', 0)))


class NowPlayingFrame(ttk.LabelFrame):
    """當前播放資訊框架"""

    def __init__(self, parent):
        super().__init__(parent, text="🎵 當前播放", padding=10)

        # 使用 StringVar 實現數據綁定
        self.title_var = tk.StringVar(value="無")
        self.requester_var = tk.StringVar(value="無")
        self.mode_var = tk.StringVar(value="🔁 歌單循環")
        self.volume_var = tk.StringVar(value="100%")
        self.status_var = tk.StringVar(value="⏹️ 已停止")

        # 創建標籤
        tk.Label(self, text="歌曲:", font=("Arial", 10, "bold"), bg="#f0f0f0", anchor="w").grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=(0, 10)
        )
        title_label = tk.Label(self, textvariable=self.title_var, font=("Arial", 10), bg="#f0f0f0", anchor="w", wraplength=200)
        title_label.grid(row=0, column=1, sticky=tk.W, pady=5)

        tk.Label(self, text="請求者:", font=("Arial", 10, "bold"), bg="#f0f0f0", anchor="w").grid(
            row=1, column=0, sticky=tk.W, pady=5, padx=(0, 10)
        )
        tk.Label(self, textvariable=self.requester_var, font=("Arial", 10), bg="#f0f0f0", anchor="w").grid(
            row=1, column=1, sticky=tk.W, pady=5
        )

        tk.Label(self, text="模式:", font=("Arial", 10, "bold"), bg="#f0f0f0", anchor="w").grid(
            row=2, column=0, sticky=tk.W, pady=5, padx=(0, 10)
        )
        tk.Label(self, textvariable=self.mode_var, font=("Arial", 10), bg="#f0f0f0", anchor="w").grid(
            row=2, column=1, sticky=tk.W, pady=5
        )

        tk.Label(self, text="音量:", font=("Arial", 10, "bold"), bg="#f0f0f0", anchor="w").grid(
            row=3, column=0, sticky=tk.W, pady=5, padx=(0, 10)
        )
        tk.Label(self, textvariable=self.volume_var, font=("Arial", 10), bg="#f0f0f0", anchor="w").grid(
            row=3, column=1, sticky=tk.W, pady=5
        )

        tk.Label(self, text="狀態:", font=("Arial", 10, "bold"), bg="#f0f0f0", anchor="w").grid(
            row=4, column=0, sticky=tk.W, pady=5, padx=(0, 10)
        )
        tk.Label(self, textvariable=self.status_var, font=("Arial", 10), bg="#f0f0f0", anchor="w").grid(
            row=4, column=1, sticky=tk.W, pady=5
        )

    def update_data(self, data):
        """更新當前播放資訊"""
        self.title_var.set(data.get('title', '無'))
        self.requester_var.set(data.get('requester', '無'))
        self.mode_var.set(data.get('mode', '🔁 歌單循環'))
        self.volume_var.set(f"{data.get('volume', 100)}%")
        self.status_var.set(data.get('status', '⏹️ 已停止'))


class QueueFrame(ttk.LabelFrame):
    """播放佇列框架"""

    def __init__(self, parent):
        super().__init__(parent, text="📜 播放佇列", padding=10)

        # 創建可滾動的 Listbox
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL)
        self.listbox = tk.Listbox(
            self,
            font=("Consolas", 10),
            bg="#2d2d30",
            fg="#d4d4d4",
            selectbackground="#094771",
            selectforeground="#ffffff",
            yscrollcommand=scrollbar.set,
            height=20
        )
        scrollbar.config(command=self.listbox.yview)

        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 初始化顯示
        self.listbox.insert(tk.END, "佇列為空")
        self.listbox.config(fg="#808080")  # 灰色提示

    def update_data(self, queue_items):
        """更新佇列顯示"""
        self.listbox.delete(0, tk.END)

        if not queue_items:
            self.listbox.insert(tk.END, "佇列為空")
            self.listbox.config(fg="#808080")
        else:
            self.listbox.config(fg="#d4d4d4")
            for i, item in enumerate(queue_items[:10], 1):
                self.listbox.insert(tk.END, f"{i}. {item}")

            if len(queue_items) > 10:
                self.listbox.insert(tk.END, "")
                self.listbox.insert(tk.END, f"...還有 {len(queue_items) - 10} 首歌曲")


class LogFrame(ttk.LabelFrame):
    """實時日誌框架（支持顏色標記）"""

    def __init__(self, parent):
        super().__init__(parent, text="📋 實時日誌", padding=10)

        # 創建可滾動的 Text 小部件
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL)
        self.text_widget = tk.Text(
            self,
            wrap=tk.WORD,
            height=15,
            bg="#1e1e1e",
            fg="#d4d4d4",
            font=("Consolas", 9),
            state=tk.DISABLED,
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.text_widget.yview)

        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 配置顏色標籤
        self.text_widget.tag_configure("INFO", foreground="#4ec9b0")      # 綠色
        self.text_widget.tag_configure("WARNING", foreground="#dcdcaa")   # 黃色
        self.text_widget.tag_configure("ERROR", foreground="#f48771")     # 紅色
        self.text_widget.tag_configure("NORMAL", foreground="#d4d4d4")    # 灰色
        self.text_widget.tag_configure("SYSTEM", foreground="#569cd6")    # 藍色（系統訊息）

        # 初始訊息
        self.append_log(f"[{datetime.now().strftime('%H:%M:%S')}] GUI 已啟動，等待數據...", level="SYSTEM")

    def append_log(self, line, level="NORMAL"):
        """添加日誌行（線程安全）"""
        self.text_widget.configure(state=tk.NORMAL)

        # 檢測日誌級別（如果未指定）
        if level == "NORMAL":
            if "ERROR" in line:
                level = "ERROR"
            elif "WARNING" in line:
                level = "WARNING"
            elif "INFO" in line:
                level = "INFO"

        # 插入文本並應用顏色標籤
        self.text_widget.insert(tk.END, line + "\n", level)

        # 自動滾動到最新行
        self.text_widget.see(tk.END)

        # 限制日誌行數（避免記憶體溢出）
        lines = int(self.text_widget.index('end-1c').split('.')[0])
        if lines > 1000:
            self.text_widget.delete('1.0', '100.0')  # 刪除前 100 行

        self.text_widget.configure(state=tk.DISABLED)


# ==================== 背景線程類 ====================

class JSONUpdateThread(threading.Thread):
    """JSON 數據更新線程"""

    def __init__(self, data_queue, status_file="bot_status.json"):
        super().__init__(daemon=True)
        self.data_queue = data_queue
        self.status_file = Path(status_file)
        self.running = True

    def run(self):
        """線程主循環"""
        while self.running:
            try:
                if self.status_file.exists():
                    with open(self.status_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    # 發送到主線程
                    self.data_queue.put(("DATA", data))
                else:
                    # 文件不存在時發送警告（但不重複發送）
                    if not hasattr(self, '_warning_sent'):
                        self.data_queue.put(("WARNING", "bot_status.json 文件不存在，請確認機器人正在運行"))
                        self._warning_sent = True
            except Exception as e:
                self.data_queue.put(("ERROR", f"讀取數據錯誤: {e}"))

            time.sleep(2)  # 每 2 秒更新一次

    def stop(self):
        """停止線程"""
        self.running = False


class LogTailThread(threading.Thread):
    """日誌追蹤線程（只讀取新日誌）"""

    def __init__(self, log_queue, log_file="logs/music_bot.log"):
        super().__init__(daemon=True)
        self.log_queue = log_queue
        self.log_file = Path(log_file)
        self.running = True

    def run(self):
        """線程主循環"""
        # 等待日誌文件創建（最多等待 30 秒）
        wait_count = 0
        while not self.log_file.exists() and self.running and wait_count < 60:
            time.sleep(0.5)
            wait_count += 1

        if not self.running:
            return

        if not self.log_file.exists():
            self.log_queue.put(("WARNING", f"[{datetime.now().strftime('%H:%M:%S')}] 日誌文件不存在，無法監控日誌"))
            return

        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                # ✨ 關鍵：直接移動到文件末尾（不讀取歷史日誌）
                f.seek(0, 2)  # SEEK_END

                self.log_queue.put(("SYSTEM", f"[{datetime.now().strftime('%H:%M:%S')}] 開始監控日誌（只顯示新日誌）"))

                # 持續追蹤新行
                while self.running:
                    line = f.readline()
                    if line:
                        # 發送新日誌行到主線程
                        self.log_queue.put(("LOG", line.strip()))
                    else:
                        # 沒有新行，短暫休眠
                        time.sleep(0.5)

        except Exception as e:
            self.log_queue.put(("ERROR", f"[{datetime.now().strftime('%H:%M:%S')}] 讀取日誌錯誤: {e}"))

    def stop(self):
        """停止線程"""
        self.running = False


# ==================== 主應用類 ====================

class TkinterDashboard:
    """主應用類"""

    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.create_queues()
        self.create_widgets()
        self.start_threads()
        self.process_queues()  # 開始處理隊列

    def setup_window(self):
        """配置主窗口"""
        self.root.title("Discord 音樂機器人監控 - Tkinter 版本")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)

        # 設置主窗口背景色
        self.root.configure(bg="#f0f0f0")

        # 綁定關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_queues(self):
        """創建線程安全隊列"""
        self.data_queue = queue.Queue()
        self.log_queue = queue.Queue()

    def create_widgets(self):
        """創建所有 UI 組件"""
        # 左側面板容器
        left_panel = tk.Frame(self.root, bg="#f0f0f0")
        left_panel.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=5, pady=5)

        # 左上：機器人狀態
        self.bot_status_frame = BotStatusFrame(left_panel)
        self.bot_status_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 左下：當前播放
        self.now_playing_frame = NowPlayingFrame(left_panel)
        self.now_playing_frame.pack(fill=tk.BOTH, expand=True)

        # 右側：播放佇列
        self.queue_frame = QueueFrame(self.root)
        self.queue_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=5, pady=5)

        # 底部：實時日誌
        self.log_frame = LogFrame(self.root)
        self.log_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        # Grid 權重配置（實現比例布局）
        self.root.grid_rowconfigure(0, weight=1)     # 上半部分 25%
        self.root.grid_rowconfigure(1, weight=1)     # 上半部分 25%
        self.root.grid_rowconfigure(2, weight=2)     # 底部日誌 50%
        self.root.grid_columnconfigure(0, weight=1)  # 左側 33%
        self.root.grid_columnconfigure(1, weight=2)  # 右側 67%

    def start_threads(self):
        """啟動背景線程"""
        self.json_thread = JSONUpdateThread(self.data_queue)
        self.log_thread = LogTailThread(self.log_queue)

        self.json_thread.start()
        self.log_thread.start()

    def process_queues(self):
        """處理隊列中的數據（主線程，線程安全）"""
        # 處理數據隊列
        try:
            while True:
                msg_type, msg_data = self.data_queue.get_nowait()
                if msg_type == "DATA":
                    self.update_ui_with_data(msg_data)
                elif msg_type == "WARNING":
                    self.log_frame.append_log(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠ {msg_data}", level="WARNING")
                elif msg_type == "ERROR":
                    self.log_frame.append_log(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ {msg_data}", level="ERROR")
        except queue.Empty:
            pass

        # 處理日誌隊列
        try:
            while True:
                msg_type, log_line = self.log_queue.get_nowait()
                if msg_type == "LOG":
                    self.log_frame.append_log(log_line)
                elif msg_type == "SYSTEM":
                    self.log_frame.append_log(log_line, level="SYSTEM")
                elif msg_type == "WARNING":
                    self.log_frame.append_log(log_line, level="WARNING")
                elif msg_type == "ERROR":
                    self.log_frame.append_log(log_line, level="ERROR")
        except queue.Empty:
            pass

        # 100ms 後再次調用（Tkinter 主循環安全）
        self.root.after(100, self.process_queues)

    def update_ui_with_data(self, data):
        """使用 JSON 數據更新所有組件"""
        self.bot_status_frame.update_data(data)
        self.now_playing_frame.update_data(data.get('current_playing', {}))
        self.queue_frame.update_data(data.get('queue', []))

    def on_closing(self):
        """窗口關閉事件處理"""
        # 停止所有線程
        if hasattr(self, 'json_thread'):
            self.json_thread.stop()
        if hasattr(self, 'log_thread'):
            self.log_thread.stop()

        # 銷毀窗口
        self.root.destroy()

    def run(self):
        """啟動主循環"""
        self.root.mainloop()


# ==================== 主程序入口 ====================

def main():
    """啟動控制台應用"""
    app = TkinterDashboard()
    app.run()


if __name__ == "__main__":
    main()
