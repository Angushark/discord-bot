import discord
from discord.ext import commands
import asyncio
import wavelink
import logging
from discord.ui import Button, View
import os
from dotenv import load_dotenv
from datetime import datetime
from logging.handlers import RotatingFileHandler

# 載入環境變數
load_dotenv()

# 設定日誌系統
if not os.path.exists('logs'):
    os.makedirs('logs')

# 創建日誌格式
log_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 設定文件處理器（自動輪轉，每個文件最大 5MB，保留 5 個備份）
file_handler = RotatingFileHandler(
    'logs/music_bot.log',
    maxBytes=5*1024*1024,
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG)

# 設定控制台處理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

# 設定根日誌記錄器
logger = logging.getLogger('MusicBot')
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# 啟用 Discord 語音調試
logging.getLogger('discord').setLevel(logging.INFO)
logging.getLogger('discord.voice_client').setLevel(logging.INFO)
logging.getLogger('discord.gateway').setLevel(logging.WARNING)
logging.getLogger('discord.http').setLevel(logging.WARNING)
logging.getLogger('wavelink').setLevel(logging.INFO)

# 設定機器人的意圖
intents = discord.Intents.all()
intents.members = True

# 設定機器人的指令前綴
bot = commands.Bot(command_prefix='$', intents=intents)
bot.remove_command('help')

# 音樂相關的全域變數
queues = {}
current_songs = {}
repeat_modes = {}  # True=單曲重複, False=歌單循環
is_paused = {}
control_messages = {}  # 存儲每個伺服器的控制面板訊息

class MusicControlView(View):
    def __init__(self, ctx, disable_all=False):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.guild_id = ctx.guild.id
        self.disable_all = disable_all

    @discord.ui.button(label='⏸️', style=discord.ButtonStyle.secondary)
    async def pause_resume(self, interaction: discord.Interaction, button: Button):
        player: wavelink.Player = interaction.guild.voice_client
        if not player:
            await interaction.response.send_message("❌ 機器人不在語音頻道中", ephemeral=True)
            return

        if player.paused:
            await player.pause(False)
            is_paused[self.guild_id] = False
            button.label = '⏸️'
            await interaction.response.edit_message(content="▶️ 繼續播放", view=self)
        elif player.playing:
            await player.pause(True)
            is_paused[self.guild_id] = True
            button.label = '▶️'
            await interaction.response.edit_message(content="⏸️ 已暫停", view=self)
        else:
            await interaction.response.send_message("❌ 沒有正在播放的歌曲", ephemeral=True)

    @discord.ui.button(label='⏭️', style=discord.ButtonStyle.primary)
    async def skip_song(self, interaction: discord.Interaction, button: Button):
        player: wavelink.Player = interaction.guild.voice_client
        if not player:
            await interaction.response.send_message("❌ 機器人不在語音頻道中", ephemeral=True)
            return

        if not player.playing and not player.paused:
            await interaction.response.send_message("❌ 沒有正在播放的歌曲", ephemeral=True)
            return

        guild_id = interaction.guild.id
        current_song = get_current_song(guild_id)
        queue = get_queue(guild_id)

        logger.info(f"[{interaction.guild.name}] 用戶 {interaction.user.name} 點擊跳過按鈕: {current_song['title'] if current_song else 'None'}, 佇列長度: {len(queue)}")

        await player.stop()
        await interaction.response.send_message("⏭️ 已跳過當前歌曲", ephemeral=True)

    @discord.ui.button(label='🔁', style=discord.ButtonStyle.secondary)
    async def toggle_repeat(self, interaction: discord.Interaction, button: Button):
        player: wavelink.Player = interaction.guild.voice_client
        if not player:
            await interaction.response.send_message("❌ 機器人不在語音頻道中", ephemeral=True)
            return

        current_mode = get_repeat_mode(self.guild_id)
        new_mode = not current_mode
        set_repeat_mode(self.guild_id, new_mode)

        if hasattr(self.ctx, '_repeat_count'):
            delattr(self.ctx, '_repeat_count')

        if new_mode:
            button.style = discord.ButtonStyle.success
            button.label = '🔂'
            current_song = get_current_song(self.guild_id)
            if current_song:
                embed = discord.Embed(title="🔂 單曲重複模式已開啟", color=0x00ff00)
                embed.add_field(name="正在播放", value=current_song['title'], inline=False)
                embed.add_field(name="模式說明", value="當前歌曲會不斷重複播放", inline=False)
            else:
                embed = discord.Embed(title="🔂 單曲重複模式已開啟", color=0x00ff00)
                embed.add_field(name="模式說明", value="當前歌曲會不斷重複播放", inline=False)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            button.style = discord.ButtonStyle.secondary
            button.label = '🔁'
            current_song = get_current_song(self.guild_id)
            if current_song:
                embed = discord.Embed(title="🔁 歌單循環模式已開啟", color=0x0099ff)
                embed.add_field(name="正在播放", value=current_song['title'], inline=False)
                embed.add_field(name="上傳者", value=current_song['uploader'], inline=True)
                embed.add_field(name="請求者", value=current_song['requester'], inline=True)
                embed.add_field(name="模式說明", value="播放完佇列會自動循環", inline=False)
            else:
                embed = discord.Embed(title="🔁 歌單循環模式已開啟", color=0x0099ff)
                embed.add_field(name="模式說明", value="播放完佇列會自動循環", inline=False)
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='📜', style=discord.ButtonStyle.secondary)
    async def show_queue(self, interaction: discord.Interaction, button: Button):
        queue = get_queue(self.guild_id)
        current_song = get_current_song(self.guild_id)

        embed = discord.Embed(title="🎵 播放佇列", color=0x0099ff)

        if get_repeat_mode(self.guild_id):
            embed.add_field(name="播放模式", value="🔂 單曲重複", inline=False)
        else:
            embed.add_field(name="播放模式", value="🔁 歌單循環", inline=False)

        if current_song:
            embed.add_field(name="正在播放", value=f"{current_song['title']}", inline=False)

        if queue:
            queue_list = []
            for i, song in enumerate(queue[:10], 1):
                queue_list.append(f"{i}. {song['title']}")
            embed.add_field(name="即將播放", value="\n".join(queue_list), inline=False)
            if len(queue) > 10:
                embed.add_field(name="", value=f"... 還有 {len(queue)-10} 首歌曲", inline=False)
        else:
            embed.add_field(name="佇列", value="佇列為空", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label='⏹️', style=discord.ButtonStyle.danger)
    async def stop_music(self, interaction: discord.Interaction, button: Button):
        player: wavelink.Player = interaction.guild.voice_client
        if not player:
            await interaction.response.send_message("❌ 機器人不在語音頻道中", ephemeral=True)
            return

        queues[self.guild_id] = []
        current_songs[self.guild_id] = None
        repeat_modes[self.guild_id] = False
        is_paused[self.guild_id] = False

        await player.stop()

        await interaction.response.send_message("⏹️ 已停止播放並清除佇列", ephemeral=True)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except:
            pass

def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = []
    return queues[guild_id]

def get_current_song(guild_id):
    return current_songs.get(guild_id)

def set_current_song(guild_id, song):
    current_songs[guild_id] = song

def get_repeat_mode(guild_id):
    return repeat_modes.get(guild_id, False)

def set_repeat_mode(guild_id, mode):
    repeat_modes[guild_id] = mode

async def update_control_panel(ctx, embed, disable_buttons=False):
    """
    更新控制面板

    Args:
        ctx: 命令上下文
        embed: 要顯示的 Embed
        disable_buttons: 是否禁用所有按鈕（播放結束時使用）
    """
    guild_id = ctx.guild.id
    view = MusicControlView(ctx, disable_all=disable_buttons)

    # 設定循環模式按鈕樣式
    if get_repeat_mode(guild_id):
        view.children[2].style = discord.ButtonStyle.success
        view.children[2].label = '🔂'
    else:
        view.children[2].style = discord.ButtonStyle.secondary
        view.children[2].label = '🔁'

    # 設定暫停/繼續按鈕標籤
    player: wavelink.Player = ctx.voice_client
    if player and player.paused:
        view.children[0].label = '▶️'
    else:
        view.children[0].label = '⏸️'

    # 如果需要禁用所有按鈕
    if disable_buttons:
        for child in view.children:
            child.disabled = True

    # 更新或創建控制面板訊息
    if guild_id in control_messages:
        try:
            await control_messages[guild_id].edit(embed=embed, view=view)
            view.message = control_messages[guild_id]
        except:
            message = await ctx.send(embed=embed, view=view)
            control_messages[guild_id] = message
            view.message = message
    else:
        message = await ctx.send(embed=embed, view=view)
        control_messages[guild_id] = message
        view.message = message

async def play_next(guild_id):
    """播放下一首歌曲"""
    player: wavelink.Player = discord.utils.get(bot.voice_clients, guild__id=guild_id)

    if not player:
        logger.debug(f"[{guild_id}] player 不存在，停止播放")
        return

    queue = get_queue(guild_id)
    current_song = get_current_song(guild_id)

    # 獲取 ctx（從 player 的 context）
    if not hasattr(player, 'ctx'):
        logger.warning(f"[{guild_id}] Player 沒有 ctx，無法繼續播放")
        return

    ctx = player.ctx

    logger.debug(f"[{ctx.guild.name}] play_next 開始執行，佇列長度: {len(queue)}, 當前歌曲: {current_song['title'] if current_song else 'None'}, 重複模式: {get_repeat_mode(guild_id)}")

    if get_repeat_mode(guild_id) and current_song:
        # 單曲重複模式
        song = current_song
        retry_count = 0
        max_retries = 3

        while retry_count < max_retries:
            try:
                tracks = await wavelink.Playable.search(song['url'])
                if not tracks:
                    raise Exception("找不到音頻源")

                track = tracks[0]
                await player.play(track)

                if not hasattr(ctx, '_repeat_count'):
                    ctx._repeat_count = 0
                ctx._repeat_count += 1

                logger.info(f"[{ctx.guild.name}] 單曲重複播放: {song['title']} (第 {ctx._repeat_count} 次)")

                if ctx._repeat_count == 1 or ctx._repeat_count % 5 == 0:
                    embed = discord.Embed(title="🔂 單曲重複播放中", color=0x00ff00)
                    embed.add_field(name="歌曲", value=song['title'], inline=False)
                    embed.add_field(name="重複次數", value=f"第 {ctx._repeat_count} 次", inline=True)
                    embed.add_field(name="提示", value="💡 想播放下一首？使用 $repeat 切換到歌單循環模式", inline=False)
                    await update_control_panel(ctx, embed)
                break

            except Exception as e:
                retry_count += 1
                logger.error(f"[{ctx.guild.name}] 播放錯誤 (嘗試 {retry_count}/{max_retries}): {song['title']} - {str(e)}")
                if retry_count < max_retries:
                    await asyncio.sleep(2 * retry_count)
                else:
                    logger.error(f"[{ctx.guild.name}] 播放失敗: {song['title']}")
                    if hasattr(ctx, '_repeat_count'):
                        delattr(ctx, '_repeat_count')
                    await ctx.send(f"❌ 播放時發生錯誤: {song['title']}")
                    return

    elif queue:
        # 歌單循環模式 - 播放佇列中的歌曲
        if hasattr(ctx, '_repeat_count'):
            delattr(ctx, '_repeat_count')

        # 如果不是單曲重複模式，先將剛播放完的歌曲加入佇列末尾（歌單循環）
        if current_song and not get_repeat_mode(guild_id):
            queue.append(current_song)

        # 播放佇列第一首歌
        song = queue.pop(0)
        set_current_song(guild_id, song)

        retry_count = 0
        max_retries = 3

        while retry_count < max_retries:
            try:
                tracks = await wavelink.Playable.search(song['url'])
                if not tracks:
                    raise Exception("找不到音頻源")

                track = tracks[0]
                await player.play(track)

                logger.info(f"[{ctx.guild.name}] 正在播放: {song['title']} (請求者: {song['requester']})")

                embed = discord.Embed(title="🔁 正在播放", color=0x00ff00)
                embed.add_field(name="歌曲", value=song['title'], inline=False)
                embed.add_field(name="上傳者", value=song['uploader'], inline=True)
                embed.add_field(name="請求者", value=song['requester'], inline=True)
                embed.add_field(name="模式", value="🔁 歌單循環", inline=True)

                await update_control_panel(ctx, embed)
                break

            except Exception as e:
                retry_count += 1
                logger.error(f"[{ctx.guild.name}] 播放錯誤 (嘗試 {retry_count}/{max_retries}): {song['title']} - {str(e)}")
                if retry_count < max_retries:
                    await asyncio.sleep(2 * retry_count)
                else:
                    logger.error(f"[{ctx.guild.name}] 無法播放歌曲，將自動嘗試下一首: {song['title']}")
                    await ctx.send(f"❌ 無法播放歌曲: {song['title']}\n將自動嘗試下一首")
                    return

    elif current_song and not get_repeat_mode(guild_id):
        # 歌單循環模式但佇列為空，重複播放當前歌曲
        if hasattr(ctx, '_repeat_count'):
            delattr(ctx, '_repeat_count')

        song = current_song
        retry_count = 0
        max_retries = 3

        while retry_count < max_retries:
            try:
                tracks = await wavelink.Playable.search(song['url'])
                if not tracks:
                    raise Exception("找不到音頻源")

                track = tracks[0]
                await player.play(track)

                logger.info(f"[{ctx.guild.name}] 歌單循環重複播放: {song['title']}")

                embed = discord.Embed(title="🔁 正在播放", color=0x00ff00)
                embed.add_field(name="歌曲", value=song['title'], inline=False)
                embed.add_field(name="上傳者", value=song['uploader'], inline=True)
                embed.add_field(name="請求者", value=song['requester'], inline=True)
                embed.add_field(name="模式", value="🔁 歌單循環 (重複播放)", inline=True)

                await update_control_panel(ctx, embed)
                break

            except Exception as e:
                retry_count += 1
                logger.error(f"[{ctx.guild.name}] 播放錯誤 (嘗試 {retry_count}/{max_retries}): {song['title']} - {str(e)}")
                if retry_count < max_retries:
                    await asyncio.sleep(2 * retry_count)
                else:
                    logger.error(f"[{ctx.guild.name}] 無法重複播放歌曲: {song['title']}")
                    await ctx.send(f"❌ 無法播放歌曲: {song['title']}\n播放佇列已結束")
                    set_current_song(guild_id, None)
                    return
    else:
        # 沒有當前歌曲且佇列為空
        if hasattr(ctx, '_repeat_count'):
            delattr(ctx, '_repeat_count')
        set_current_song(guild_id, None)
        embed = discord.Embed(title="🎵 播放佇列已結束", color=0xff0000)
        embed.add_field(name="提示", value="使用 `$play [歌曲名稱或 URL]` 添加新歌曲", inline=False)
        # 禁用所有按鈕，因為沒有歌曲在播放
        await update_control_panel(ctx, embed, disable_buttons=True)
        logger.info(f"[{ctx.guild.name}] 播放佇列已結束，控制面板已禁用")

@bot.event
async def on_ready():
    logger.info(f'機器人已上線：{bot.user.name} (ID: {bot.user.id})')
    logger.info(f'連接到 {len(bot.guilds)} 個伺服器')

    # 設置 Wavelink 節點
    try:
        # 嘗試連接到本地 Lavalink 伺服器
        node: wavelink.Node = wavelink.Node(uri='http://localhost:2333', password='youshallnotpass')
        await wavelink.Pool.connect(client=bot, nodes=[node])
        logger.info('✓ 已連接到 Lavalink 伺服器')
    except Exception as e:
        logger.error(f'❌ 無法連接到 Lavalink 伺服器: {e}')
        logger.error('請確保 Lavalink 伺服器正在運行')
        logger.error('下載地址: https://github.com/lavalink-devs/Lavalink/releases')

    print(f"Music Bot is online: {bot.user.name}")

@bot.event
async def on_wavelink_track_end(payload: wavelink.TrackEndEventPayload):
    """當歌曲播放完成或跳過時自動播放下一首"""
    player = payload.player
    if not player:
        return

    guild_id = player.guild.id

    # 處理自然播放完成和手動跳過
    if payload.reason == "finished":
        logger.info(f"[{player.guild.name}] 歌曲播放完成，準備播放下一首")
        await asyncio.sleep(0.5)
        await play_next(guild_id)

    elif payload.reason == "stopped":
        # 手動跳過 - 需要判斷是 skip 還是 stop
        queue = get_queue(guild_id)
        current_song = get_current_song(guild_id)

        # 如果是 stop 命令，佇列和當前歌曲都會被清空（見 line 934-939）
        # 如果是 skip，佇列或當前歌曲仍然存在
        if queue or current_song:
            logger.info(f"[{player.guild.name}] 用戶跳過歌曲，準備播放下一首")
            await asyncio.sleep(0.5)
            await play_next(guild_id)
        else:
            logger.info(f"[{player.guild.name}] 停止播放，佇列已清空")

    else:
        # 忽略其他事件：REPLACED(被新歌替換), LOAD_FAILED(載入失敗) 等
        logger.debug(f"[{player.guild.name}] 歌曲結束原因: {payload.reason}，不處理")

@bot.event
async def on_voice_state_update(member, before, after):
    if member == bot.user:
        return

    for voice_client in bot.voice_clients:
        members_in_channel = [m for m in voice_client.channel.members if not m.bot]

        if len(members_in_channel) == 0:
            guild_id = voice_client.guild.id

            if guild_id in queues:
                queues[guild_id] = []
            if guild_id in current_songs:
                current_songs[guild_id] = None
            if guild_id in repeat_modes:
                repeat_modes[guild_id] = False
            if guild_id in is_paused:
                is_paused[guild_id] = False
            if guild_id in control_messages:
                del control_messages[guild_id]

            await voice_client.disconnect()

            for channel in voice_client.guild.text_channels:
                if channel.permissions_for(voice_client.guild.me).send_messages:
                    await channel.send("👋 語音頻道沒有其他用戶，機器人自動離開")
                    break

@bot.command()
async def help(ctx):
    """顯示所有可用的指令"""
    embed = discord.Embed(
        title="🎵 音樂機器人指令總覽",
        description="使用以下指令控制音樂播放",
        color=0x0099ff
    )

    # 基本播放控制
    embed.add_field(
        name="📀 基本控制",
        value=(
            "**$play** [歌曲名或URL] - 播放歌曲\n"
            "**$play** - 一鍵繼續/開始播放 🆕\n"
            "**$skip** - 跳過當前歌曲\n"
            "**$pause** - 暫停播放\n"
            "**$resume** - 繼續播放\n"
            "**$stop** - 停止並清空佇列"
        ),
        inline=False
    )

    # 佇列管理
    embed.add_field(
        name="📜 佇列管理",
        value=(
            "**$queue** - 查看播放佇列\n"
            "**$undo** - 撤銷最後添加的歌曲 🆕\n"
            "**$remove** [編號] - 移除指定歌曲\n"
            "**$clear** - 清空整個佇列"
        ),
        inline=False
    )

    # 播放模式
    embed.add_field(
        name="🔁 播放模式",
        value=(
            "**$repeat** - 切換模式\n"
            "　🔂 單曲重複\n"
            "　🔁 歌單循環"
        ),
        inline=False
    )

    # 其他功能
    embed.add_field(
        name="⚙️ 其他功能",
        value=(
            "**$nowplaying** - 當前播放資訊\n"
            "**$control** - 顯示控制面板\n"
            "**$volume** [0-100] - 調整音量\n"
            "**$join** - 加入語音頻道\n"
            "**$leave** - 離開語音頻道"
        ),
        inline=False
    )

    # 提示
    embed.set_footer(text="💡 提示：點擊控制面板的按鈕也可以快速操作！ | 🆕 = 新功能")

    await ctx.send(embed=embed)

@bot.command(pass_context=True)
async def join(ctx):
    if ctx.voice_client is None:
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            player: wavelink.Player = await channel.connect(cls=wavelink.Player)
            player.ctx = ctx  # 保存 ctx 供後續使用
            await ctx.send(f"✅ 已加入語音頻道: {channel.name}")
        else:
            await ctx.send("❌ 你不在語音頻道裡")
    else:
        await ctx.send("❌ 機器人已經在語音頻道中")

@bot.command(pass_context=True)
async def leave(ctx):
    player: wavelink.Player = ctx.voice_client
    if player:
        guild_id = ctx.guild.id
        queues[guild_id] = []
        current_songs[guild_id] = None
        repeat_modes[guild_id] = False
        is_paused[guild_id] = False
        if guild_id in control_messages:
            del control_messages[guild_id]
        await player.disconnect()
        await ctx.send("👋 已離開語音頻道")
    else:
        await ctx.send("❌ 機器人不在語音頻道中")

@bot.command()
async def play(ctx, *, query=None):
    """
    播放音樂指令

    用法:
        $play [歌曲名稱或 URL] - 搜尋並播放歌曲
        $play - 如果暫停則繼續播放，如果有佇列則開始播放
    """
    if not ctx.author.voice:
        await ctx.send("❌ 你必須先加入語音頻道！")
        return

    player: wavelink.Player = ctx.voice_client
    guild_id = ctx.guild.id

    # 如果沒有提供查詢參數，實現一鍵播放功能
    if query is None:
        if not player:
            await ctx.send("❌ 機器人不在語音頻道中，請使用 `$play [歌曲名稱]` 添加歌曲")
            return

        # 如果正在暫停，則繼續播放
        if player.paused:
            await player.pause(False)
            await ctx.send("▶️ 繼續播放")
            logger.info(f"[{ctx.guild.name}] 用戶 {ctx.author.name} 使用一鍵繼續播放")
            return

        # 如果有佇列但沒在播放，開始播放佇列
        queue = get_queue(guild_id)
        if not player.playing and queue:
            await play_next(guild_id)
            logger.info(f"[{ctx.guild.name}] 用戶 {ctx.author.name} 使用一鍵開始播放佇列")
            return

        # 其他情況提示用戶
        if player.playing:
            current = get_current_song(guild_id)
            if current:
                await ctx.send(f"🎵 正在播放: **{current['title']}**\n使用 `$nowplaying` 查看詳情")
            else:
                await ctx.send("✅ 已在播放中")
        else:
            await ctx.send("❌ 佇列為空，請使用 `$play [歌曲名稱]` 添加歌曲")
        return

    # 以下是原有的搜尋和播放邏輯
    if not player:
        channel = ctx.author.voice.channel
        player: wavelink.Player = await channel.connect(cls=wavelink.Player)
        player.ctx = ctx  # 保存 ctx 供後續使用
        logger.info(f"[{ctx.guild.name}] 機器人加入語音頻道: {channel.name}")

    queue = get_queue(guild_id)

    try:
        search_msg = await ctx.send("🔍 正在搜尋影片...")
        logger.info(f"[{ctx.guild.name}] 使用者 {ctx.author.name} 請求播放: {query}")

        # 使用 Wavelink 搜索
        tracks = await wavelink.Playable.search(query)

        if not tracks:
            await search_msg.delete()
            await ctx.send("❌ 找不到任何結果")
            return

        track = tracks[0]
        await search_msg.delete()

        song_info = {
            'title': track.title,
            'url': track.uri,
            'duration': track.length,
            'uploader': track.author,
            'requester': ctx.author.display_name
        }

        # 檢查是否正在播放或暫停
        if not player.playing and not player.paused:
            set_current_song(guild_id, song_info)

            await player.play(track)
            logger.info(f"[{ctx.guild.name}] 開始播放: {song_info['title']}")

            embed = discord.Embed(title="🎵 正在播放", color=0x00ff00)
            embed.add_field(name="歌曲", value=song_info['title'], inline=False)
            embed.add_field(name="上傳者", value=song_info['uploader'], inline=True)
            embed.add_field(name="請求者", value=song_info['requester'], inline=True)
            await update_control_panel(ctx, embed)
        else:
            queue.append(song_info)
            logger.info(f"[{ctx.guild.name}] 加入佇列: {song_info['title']} (位置: {len(queue)})")

            embed = discord.Embed(title="➕ 已加入佇列", color=0xffff00)
            embed.add_field(name="歌曲", value=song_info['title'], inline=False)
            embed.add_field(name="佇列位置", value=f"第 {len(queue)} 首", inline=True)
            embed.add_field(name="請求者", value=song_info['requester'], inline=True)
            await ctx.send(embed=embed)

    except Exception as e:
        logger.error(f"[{ctx.guild.name}] 播放時發生錯誤: {query} - {str(e)}")
        await ctx.send(f"❌ 播放時發生錯誤: {str(e)}")

@bot.command()
async def skip(ctx):
    player: wavelink.Player = ctx.voice_client
    if not player:
        await ctx.send("❌ 機器人不在語音頻道中")
        return
    if not player.playing and not player.paused:
        await ctx.send("❌ 沒有正在播放的歌曲")
        return

    guild_id = ctx.guild.id
    current_song = get_current_song(guild_id)
    queue = get_queue(guild_id)

    logger.info(f"[{ctx.guild.name}] 用戶 {ctx.author.name} 跳過歌曲: {current_song['title'] if current_song else 'None'}, 佇列長度: {len(queue)}")

    await player.stop()
    await ctx.send("⏭️ 已跳過當前歌曲")

@bot.command()
async def repeat(ctx):
    player: wavelink.Player = ctx.voice_client
    if not player:
        await ctx.send("❌ 機器人不在語音頻道中")
        return

    guild_id = ctx.guild.id
    current_mode = get_repeat_mode(guild_id)
    new_mode = not current_mode
    set_repeat_mode(guild_id, new_mode)

    if hasattr(ctx, '_repeat_count'):
        delattr(ctx, '_repeat_count')

    if new_mode:
        embed = discord.Embed(title="🔂 單曲重複模式已開啟", color=0x00ff00)
        embed.add_field(name="說明", value="當前歌曲會不斷重複播放", inline=False)
        current_song = get_current_song(guild_id)
        if current_song:
            embed.add_field(name="正在重複", value=current_song['title'], inline=False)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="🔁 歌單循環模式已開啟", color=0x0099ff)
        embed.add_field(name="說明", value="播放完佇列會自動循環", inline=False)
        current_song = get_current_song(guild_id)
        if current_song:
            embed.add_field(name="正在播放", value=current_song['title'], inline=False)
        await ctx.send(embed=embed)

    current_song = get_current_song(guild_id)
    if current_song:
        if new_mode:
            control_embed = discord.Embed(title="🔂 單曲重複播放中", color=0x00ff00)
            control_embed.add_field(name="歌曲", value=current_song['title'], inline=False)
            control_embed.add_field(name="模式", value="🔂 單曲重複", inline=True)
        else:
            control_embed = discord.Embed(title="🔁 歌單循環播放中", color=0x0099ff)
            control_embed.add_field(name="歌曲", value=current_song['title'], inline=False)
            control_embed.add_field(name="上傳者", value=current_song['uploader'], inline=True)
            control_embed.add_field(name="請求者", value=current_song['requester'], inline=True)
            control_embed.add_field(name="模式", value="🔁 歌單循環", inline=True)
        await update_control_panel(ctx, control_embed)

@bot.command()
async def queue(ctx):
    """顯示播放佇列和當前狀態"""
    guild_id = ctx.guild.id
    queue = get_queue(guild_id)
    current_song = get_current_song(guild_id)
    player: wavelink.Player = ctx.voice_client

    embed = discord.Embed(title="📜 播放佇列", color=0x0099ff)

    # 播放模式
    mode_icon = "🔂" if get_repeat_mode(guild_id) else "🔁"
    mode_text = "單曲重複" if get_repeat_mode(guild_id) else "歌單循環"
    embed.add_field(name="播放模式", value=f"{mode_icon} {mode_text}", inline=True)

    # 佇列狀態
    queue_status = f"共 {len(queue)} 首歌曲" if queue else "空"
    embed.add_field(name="佇列狀態", value=queue_status, inline=True)

    # 播放狀態
    if player:
        if player.paused:
            status = "⏸️ 已暫停"
        elif player.playing:
            status = "▶️ 播放中"
        else:
            status = "⏹️ 已停止"
        embed.add_field(name="播放狀態", value=status, inline=True)

    # 正在播放
    if current_song:
        current_text = f"🎵 **{current_song['title']}**\n👤 請求者：{current_song['requester']}"
        embed.add_field(name="正在播放", value=current_text, inline=False)

    # 佇列內容
    if queue:
        queue_list = []
        for i, song in enumerate(queue[:10], 1):
            queue_list.append(f"`{i}.` {song['title']}")
        embed.add_field(name=f"即將播放 (前{min(len(queue), 10)}首)", value="\n".join(queue_list), inline=False)
        if len(queue) > 10:
            embed.add_field(name="", value=f"... 還有 **{len(queue)-10}** 首歌曲", inline=False)
    else:
        embed.add_field(name="佇列", value="🚫 佇列為空\n使用 `$play` 添加歌曲", inline=False)

    embed.set_footer(text="提示：使用 $remove [編號] 移除歌曲 | $undo 撤銷最後添加")

    await ctx.send(embed=embed)

@bot.command()
async def nowplaying(ctx):
    """顯示當前播放的歌曲詳細資訊"""
    guild_id = ctx.guild.id
    current_song = get_current_song(guild_id)
    player: wavelink.Player = ctx.voice_client

    if not current_song:
        await ctx.send("❌ 沒有正在播放的歌曲")
        return

    embed = discord.Embed(title="🎵 正在播放", color=0x00ff00)

    # 歌曲資訊
    embed.add_field(name="歌曲名稱", value=f"**{current_song['title']}**", inline=False)
    embed.add_field(name="上傳者", value=current_song['uploader'], inline=True)
    embed.add_field(name="請求者", value=f"👤 {current_song['requester']}", inline=True)

    # 播放狀態
    if player:
        if player.paused:
            status = "⏸️ 已暫停"
        elif player.playing:
            status = "▶️ 播放中"
        else:
            status = "⏹️ 已停止"
        embed.add_field(name="狀態", value=status, inline=True)

        # 音量
        volume = player.volume
        embed.add_field(name="音量", value=f"🔊 {volume}%", inline=True)

    # 播放模式
    mode_icon = "🔂" if get_repeat_mode(guild_id) else "🔁"
    mode_text = "單曲重複" if get_repeat_mode(guild_id) else "歌單循環"
    embed.add_field(name="播放模式", value=f"{mode_icon} {mode_text}", inline=True)

    # 佇列資訊
    queue = get_queue(guild_id)
    queue_info = f"📜 {len(queue)} 首歌曲等待中" if queue else "📜 佇列為空"
    embed.add_field(name="佇列", value=queue_info, inline=True)

    embed.set_footer(text="使用 $control 顯示控制面板")

    await ctx.send(embed=embed)

@bot.command()
async def control(ctx):
    player: wavelink.Player = ctx.voice_client
    if not player:
        await ctx.send("❌ 機器人不在語音頻道中")
        return

    guild_id = ctx.guild.id
    current_song = get_current_song(guild_id)

    if current_song:
        embed = discord.Embed(title="🎵 音樂控制面板", color=0x0099ff)
        embed.add_field(name="正在播放", value=current_song['title'], inline=False)

        if get_repeat_mode(guild_id):
            embed.add_field(name="播放模式", value="🔂 單曲重複", inline=False)
        else:
            embed.add_field(name="播放模式", value="🔁 歌單循環", inline=False)

        if player.paused:
            embed.add_field(name="狀態", value="⏸️ 已暫停", inline=True)
        elif player.playing:
            embed.add_field(name="狀態", value="▶️ 播放中", inline=True)
        else:
            embed.add_field(name="狀態", value="⏹️ 已停止", inline=True)
    else:
        embed = discord.Embed(title="🎵 音樂控制面板", description="目前沒有播放歌曲", color=0x0099ff)

    await update_control_panel(ctx, embed)

@bot.command()
async def pause(ctx):
    player: wavelink.Player = ctx.voice_client
    if not player:
        await ctx.send("❌ 機器人不在語音頻道中")
        return

    if player.playing:
        await player.pause(True)
        is_paused[ctx.guild.id] = True
        await ctx.send("⏸️ 已暫停播放")
    elif player.paused:
        await ctx.send("❌ 音樂已經暫停了")
    else:
        await ctx.send("❌ 沒有正在播放的歌曲")

@bot.command()
async def resume(ctx):
    player: wavelink.Player = ctx.voice_client
    if not player:
        await ctx.send("❌ 機器人不在語音頻道中")
        return

    if player.paused:
        await player.pause(False)
        is_paused[ctx.guild.id] = False
        await ctx.send("▶️ 繼續播放")
    elif player.playing:
        await ctx.send("❌ 音樂正在播放中")
    else:
        await ctx.send("❌ 沒有暫停的歌曲")

@bot.command()
async def volume(ctx, vol: int = None):
    """設定播放音量 (0-100)"""
    player: wavelink.Player = ctx.voice_client
    if not player:
        await ctx.send("❌ 機器人不在語音頻道中")
        return

    if not player.playing and not player.paused:
        await ctx.send("❌ 沒有正在播放的歌曲")
        return

    # 如果沒有提供音量參數，顯示當前音量
    if vol is None:
        current_volume = player.volume
        await ctx.send(f"🔊 當前音量：{current_volume}%")
        return

    # 檢查音量範圍
    if vol < 0 or vol > 100:
        await ctx.send("❌ 音量必須在 0-100 之間")
        return

    # 設定音量
    await player.set_volume(vol)
    logger.info(f"[{ctx.guild.name}] 音量設定為 {vol}%")
    await ctx.send(f"🔊 音量已設定為 {vol}%")

@bot.command()
async def stop(ctx):
    player: wavelink.Player = ctx.voice_client
    if not player:
        await ctx.send("❌ 機器人不在語音頻道中")
        return

    guild_id = ctx.guild.id
    queues[guild_id] = []
    current_songs[guild_id] = None
    repeat_modes[guild_id] = False
    is_paused[guild_id] = False
    if guild_id in control_messages:
        del control_messages[guild_id]

    await player.stop()

    await ctx.send("⏹️ 已停止播放並清除佇列")

@bot.command()
async def remove(ctx, index: int):
    guild_id = ctx.guild.id
    queue = get_queue(guild_id)

    if not queue:
        await ctx.send("❌ 佇列為空")
        return

    if index < 1 or index > len(queue):
        await ctx.send(f"❌ 請輸入1到{len(queue)}之間的數字")
        return

    removed_song = queue.pop(index - 1)
    await ctx.send(f"🗑️ 已從佇列中移除: **{removed_song['title']}**")

@bot.command()
async def clear(ctx):
    """清除播放佇列"""
    guild_id = ctx.guild.id
    queue = get_queue(guild_id)

    if not queue:
        await ctx.send("❌ 佇列已經是空的")
        return

    count = len(queue)
    queue.clear()
    await ctx.send(f"🗑️ 已清除播放佇列（移除了 {count} 首歌曲）")
    logger.info(f"[{ctx.guild.name}] 用戶 {ctx.author.name} 清除了 {count} 首歌曲")

@bot.command()
async def undo(ctx):
    """
    快速移除最後添加的歌曲（一鍵撤銷）

    這是 $remove [最後一個] 的快捷方式
    """
    guild_id = ctx.guild.id
    queue = get_queue(guild_id)

    if not queue:
        await ctx.send("❌ 佇列為空，沒有可以撤銷的歌曲")
        return

    # 移除最後一首歌曲
    removed_song = queue.pop()
    embed = discord.Embed(title="↩️ 已撤銷", color=0xffa500)
    embed.add_field(name="移除的歌曲", value=removed_song['title'], inline=False)
    embed.add_field(name="剩餘佇列", value=f"{len(queue)} 首歌曲", inline=True)
    await ctx.send(embed=embed)
    logger.info(f"[{ctx.guild.name}] 用戶 {ctx.author.name} 撤銷了歌曲: {removed_song['title']}")

# 從環境變數讀取 Bot Token
token = os.getenv('DISCORD_BOT_TOKEN')

if not token:
    logger.error("❌ 找不到 DISCORD_BOT_TOKEN 環境變數")
    logger.error("請創建 .env 文件並設定 DISCORD_BOT_TOKEN=your_token_here")
    print("\n錯誤：未設定 Discord Bot Token")
    print("請按照以下步驟設定：")
    print("1. 複製 .env.example 為 .env")
    print("2. 在 .env 中填入你的 Bot Token")
    print("3. 重新啟動機器人\n")
    exit(1)

logger.info("正在啟動機器人...")
try:
    bot.run(token)
except discord.LoginFailure:
    logger.error("❌ 登入失敗：Bot Token 無效")
    print("\n錯誤：Bot Token 無效，請檢查 .env 文件中的 DISCORD_BOT_TOKEN\n")
except Exception as e:
    logger.error(f"❌ 機器人啟動失敗: {str(e)}")
    print(f"\n錯誤：{str(e)}\n")
