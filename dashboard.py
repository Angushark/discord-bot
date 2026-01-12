"""
Discord 音樂機器人 - 終端 GUI 控制台
使用 Textual 創建美觀的實時監控界面
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Log
from textual.reactive import reactive
from textual import work


class BotStatusWidget(Static):
    """機器人狀態顯示小部件"""

    bot_online = reactive(False)
    lavalink_online = reactive(False)
    guild_count = reactive(0)
    voice_connections = reactive(0)

    def render(self) -> str:
        status_icon = "✅" if self.bot_online else "❌"
        lavalink_icon = "✅" if self.lavalink_online else "❌"

        return f"""[bold cyan]━━━ 機器人狀態 ━━━[/bold cyan]

[bold]狀態:[/bold] {status_icon} {"在線" if self.bot_online else "離線"}
[bold]Lavalink:[/bold] {lavalink_icon} {"已連接" if self.lavalink_online else "未連接"} (localhost:2333)
[bold]伺服器數:[/bold] {self.guild_count}  |  [bold]語音連接:[/bold] {self.voice_connections}
"""


class NowPlayingWidget(Static):
    """當前播放資訊小部件"""

    song_title = reactive("無")
    requester = reactive("無")
    mode = reactive("🔁 歌單循環")
    volume = reactive(100)
    playing_status = reactive("⏹️ 已停止")

    def render(self) -> str:
        return f"""[bold cyan]━━━ 當前播放 ━━━[/bold cyan]

[bold]🎵 歌曲:[/bold] {self.song_title}
[bold]👤 請求者:[/bold] {self.requester}
[bold]🔁 模式:[/bold] {self.mode}
[bold]🔊 音量:[/bold] {self.volume}%
[bold]▶️ 狀態:[/bold] {self.playing_status}
"""


class QueueWidget(Static):
    """播放佇列顯示小部件"""

    queue_items = reactive([])

    def render(self) -> str:
        content = "[bold cyan]━━━ 播放佇列 ━━━[/bold cyan]\n\n"

        if not self.queue_items:
            content += "[dim]佇列為空[/dim]"
        else:
            for i, item in enumerate(self.queue_items[:10], 1):
                content += f"{i}. {item}\n"

            if len(self.queue_items) > 10:
                content += f"\n[dim]...還有 {len(self.queue_items) - 10} 首歌曲[/dim]"

        return content


class DashboardApp(App):
    """Discord 音樂機器人控制台主應用"""

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        layout: vertical;
        height: 100%;
    }

    #top-section {
        layout: horizontal;
        height: 50%;
    }

    #left-panel {
        width: 50%;
        padding: 1;
    }

    #right-panel {
        width: 50%;
        padding: 1;
    }

    #log-section {
        height: 50%;
        padding: 1;
    }

    BotStatusWidget, NowPlayingWidget, QueueWidget {
        border: solid $primary;
        height: auto;
        margin-bottom: 1;
    }

    Log {
        border: solid $primary;
        background: $surface;
    }
    """

    BINDINGS = [
        ("q", "quit", "退出"),
        ("r", "refresh", "刷新"),
        ("l", "clear_log", "清除日誌"),
        ("s", "save_log", "保存日誌"),
    ]

    def __init__(self):
        super().__init__()
        self.status_file = Path("bot_status.json")
        self.log_file = Path("logs/music_bot.log")
        self.bot_status_widget = None
        self.now_playing_widget = None
        self.queue_widget = None
        self.log_widget = None

    def compose(self) -> ComposeResult:
        """創建 UI 布局"""
        yield Header()

        with Container(id="main-container"):
            with Horizontal(id="top-section"):
                with Vertical(id="left-panel"):
                    self.bot_status_widget = BotStatusWidget()
                    yield self.bot_status_widget
                    self.now_playing_widget = NowPlayingWidget()
                    yield self.now_playing_widget

                with Vertical(id="right-panel"):
                    self.queue_widget = QueueWidget()
                    yield self.queue_widget

            with Container(id="log-section"):
                self.log_widget = Log(highlight=True)
                yield self.log_widget

        yield Footer()

    def on_mount(self) -> None:
        """應用啟動時執行"""
        self.title = "Discord 音樂機器人控制台"
        self.sub_title = "實時監控與日誌查看"

        # 啟動數據更新任務
        self.update_data()
        self.tail_log()

    @work(exclusive=True)
    async def update_data(self) -> None:
        """定期更新機器人狀態數據"""
        while True:
            try:
                if self.status_file.exists():
                    with open(self.status_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # 更新機器人狀態
                    if self.bot_status_widget:
                        self.bot_status_widget.bot_online = data.get('bot_online', False)
                        self.bot_status_widget.lavalink_online = data.get('lavalink_online', False)
                        self.bot_status_widget.guild_count = data.get('guild_count', 0)
                        self.bot_status_widget.voice_connections = data.get('voice_connections', 0)

                    # 更新當前播放
                    if self.now_playing_widget:
                        current = data.get('current_playing', {})
                        self.now_playing_widget.song_title = current.get('title', '無')
                        self.now_playing_widget.requester = current.get('requester', '無')
                        self.now_playing_widget.mode = current.get('mode', '🔁 歌單循環')
                        self.now_playing_widget.volume = current.get('volume', 100)
                        self.now_playing_widget.playing_status = current.get('status', '⏹️ 已停止')

                    # 更新佇列
                    if self.queue_widget:
                        queue = data.get('queue', [])
                        self.queue_widget.queue_items = queue

            except Exception as e:
                if self.log_widget:
                    self.log_widget.write(f"[red]❌ 更新數據錯誤: {e}[/red]")

            await asyncio.sleep(2)  # 每 2 秒更新一次

    @work(exclusive=True)
    async def tail_log(self) -> None:
        """實時追蹤日誌文件"""
        if not self.log_file.exists():
            if self.log_widget:
                self.log_widget.write("[yellow]⚠ 日誌文件不存在，等待創建...[/yellow]")
            await asyncio.sleep(5)
            return self.tail_log()

        try:
            # 讀取最後 50 行
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[-50:]:
                    self._write_log_line(line.strip())

            # 持續追蹤新行
            with open(self.log_file, 'r', encoding='utf-8') as f:
                f.seek(0, 2)  # 移動到文件末尾

                while True:
                    line = f.readline()
                    if line:
                        self._write_log_line(line.strip())
                    else:
                        await asyncio.sleep(0.5)

        except Exception as e:
            if self.log_widget:
                self.log_widget.write(f"[red]❌ 讀取日誌錯誤: {e}[/red]")

    def _write_log_line(self, line: str) -> None:
        """根據日誌級別添加顏色"""
        if not line or not self.log_widget:
            return

        if "ERROR" in line:
            self.log_widget.write(f"[red]{line}[/red]")
        elif "WARNING" in line:
            self.log_widget.write(f"[yellow]{line}[/yellow]")
        elif "INFO" in line:
            self.log_widget.write(f"[green]{line}[/green]")
        else:
            self.log_widget.write(line)

    def action_refresh(self) -> None:
        """手動刷新數據"""
        if self.log_widget:
            self.log_widget.write(f"[cyan]🔄 {datetime.now().strftime('%H:%M:%S')} 手動刷新數據[/cyan]")

    def action_clear_log(self) -> None:
        """清除日誌顯示"""
        if self.log_widget:
            self.log_widget.clear()
            self.log_widget.write(f"[cyan]🗑️ {datetime.now().strftime('%H:%M:%S')} 日誌已清除[/cyan]")

    def action_save_log(self) -> None:
        """保存當前日誌到文件"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_path = Path(f"logs/dashboard_log_{timestamp}.txt")

            if self.log_widget:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(str(self.log_widget))

                self.log_widget.write(f"[green]✅ 日誌已保存到: {save_path}[/green]")

        except Exception as e:
            if self.log_widget:
                self.log_widget.write(f"[red]❌ 保存日誌失敗: {e}[/red]")


def main():
    """啟動控制台應用"""
    app = DashboardApp()
    app.run()


if __name__ == "__main__":
    main()
