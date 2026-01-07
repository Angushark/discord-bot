import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import random

# 載入環境變數
load_dotenv()
import datetime
import calendar
import time
import asyncio
import yt_dlp
import logging

import urllib.parse, urllib.request, re

from discord import FFmpegPCMAudio
from discord.ext import commands
from discord.ui import Button, View

logging.basicConfig(level=logging.DEBUG)

# 設定機器人的意圖，允許機器人接收所有類型的事件
intents = discord.Intents.all()
intents.members = True

# 設定機器人的指令前綴
bot = commands.Bot(command_prefix='$',  intents=intents)
# 移除內建的 help 指令，以便自定義 help 指令
bot.remove_command('help')

# 音樂相關的全域變數
queues = {}
current_songs = {}
repeat_modes = {}
loop_modes = {}

# YouTube-dl 設定
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'extract_flat': False,
    'cachedir': False
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.uploader = data.get('uploader')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        if 'entries' in data:
            # 如果是播放列表，取第一個
            data = data['entries'][0]
        
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

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

def get_loop_mode(guild_id):
    return loop_modes.get(guild_id, True)  # 預設開啟循環模式

def set_loop_mode(guild_id, mode):
    loop_modes[guild_id] = mode

async def play_next(ctx):
    guild_id = ctx.guild.id
    queue = get_queue(guild_id)
    current_song = get_current_song(guild_id)
    
    if not ctx.voice_client:
        return
    
    if get_repeat_mode(guild_id) and current_song:
        # 單曲重複模式 - 不改變佇列，直接重複播放
        song = current_song
        try:
            player = await YTDLSource.from_url(song['url'], loop=bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
            await ctx.send(f"🔂 重複播放: **{song['title']}**")
        except Exception as e:
            await ctx.send(f"播放時發生錯誤: {e}")
            await play_next(ctx)
    elif queue:
        # 如果開啟循環模式，先將當前播放的歌曲加回佇列末尾
        if get_loop_mode(guild_id) and current_song:
            queue.append(current_song)
        
        # 然後播放佇列下一首
        song = queue.pop(0)
        set_current_song(guild_id, song)
        try:
            player = await YTDLSource.from_url(song['url'], loop=bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
            loop_indicator = "🔁 " if get_loop_mode(guild_id) else ""
            await ctx.send(f"{loop_indicator}🎵 正在播放: **{song['title']}**")
        except Exception as e:
            await ctx.send(f"播放時發生錯誤: {e}")
            await play_next(ctx)
    else:
        # 佇列為空
        set_current_song(guild_id, None)
        await ctx.send("🎵 播放佇列已結束")

@bot.event
async def on_message(message):
    # 避免机器人自己触发事件
    if message.author == bot.user:
        return

    # 如果消息内容是"..."，则发送",,,"
    if message.content == '下巴':
        await message.channel.send('下八')

    # 继续处理其他消息
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print("i am online")

@bot.command()
async def loop(ctx):
    if not ctx.voice_client:
        await ctx.send("❌ 機器人不在語音頻道中")
        return
    
    guild_id = ctx.guild.id
    current_mode = get_loop_mode(guild_id)
    new_mode = not current_mode
    set_loop_mode(guild_id, new_mode)
    
    if new_mode:
        await ctx.send("🔁 循環播放模式已開啟")
    else:
        await ctx.send("➡️ 循環播放模式已關閉")

@bot.command() 
async def help(ctx): 
    embed = discord.Embed(title="沒用指令區", description="指令如下:", color=0xeee657)

    embed.add_field(name="$ping", value="傳出這隻機器人的人延遲", inline=False) 
    embed.add_field(name="$sleep", value="當你想睡覺的時候可以用", inline=False)
    embed.add_field(name="$takina", value="就婆阿", inline=False)
    embed.add_field(name="$guess", value="小遊戲", inline=False) 
    embed.add_field(name="$now", value="現在時間", inline=False) 
    embed.add_field(name="$join", value="加入你所在的語音頻道", inline=False)
    embed.add_field(name="$leave", value="退出頻道", inline=False)
    embed.add_field(name="$cal", value="你電腦時間當時月曆", inline=False)
    embed.add_field(name="$play [URL]", value="播放YouTube影片音樂", inline=False)
    embed.add_field(name="$skip", value="跳過當前歌曲", inline=False)
    embed.add_field(name="$repeat", value="切換單曲重複模式", inline=False)
    embed.add_field(name="$loop", value="切換循環播放模式", inline=False)
    embed.add_field(name="$queue", value="顯示播放佇列", inline=False)
    embed.add_field(name="$nowplaying", value="顯示當前播放歌曲", inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
async def ping(ctx):  #ctx 上下文 A:(上文) B:(下文)
    await ctx.send(f'{round(bot.latency*1000)} (ms)')

@bot.command()
async def sleep(ctx):
    await ctx.send("晚安~")

@bot.command()
async def takina(ctx):
    pic = discord.File(os.path.join("items", "takina.jpg"))
    await ctx.send(file=pic)

@bot.command()
async def duck(ctx):
    with open("items",'duck.gif') as f:
        pic = discord.File(f)
    
        await ctx.send(file=pic)

@bot.command()
async def pic(ctx):
    await ctx.send("輸入1-3")
    number = await bot.wait_for("message", timeout=300.0)
    
    if number.content == '1':
        pic = discord.File(os.path.join("items","p1.gif"))
        
    
    if number.content == '2':
        pic = discord.File(os.path.join("items", "p2.gif"))
        
    
    if number.content == '3':
        pic = discord.File(os.path.join("items", "p3.gif"))
    
    await ctx.send(file=pic)

@bot.command()
async def mygo(ctx):
    a = random.randint(1,10)
    print(a)
    if a==1:
        pic = discord.File(os.path.join("items","mygo1.jpeg"))
    elif a==2:
        pic = discord.File(os.path.join("items","mygo2.jpeg"))
    elif a==3:
        pic = discord.File(os.path.join("items","mygo3.png"))
    elif a==4:
        pic = discord.File(os.path.join("items","mygo4.jpeg"))
    elif a==5:
        pic = discord.File(os.path.join("items","mygo5.jpeg"))
    elif a==6:
        pic = discord.File(os.path.join("items","mygo6.png"))
    elif a==7:
        pic = discord.File(os.path.join("items","mygo7.gif"))
    elif a==8:
        pic = discord.File(os.path.join("items","mygo8.png"))
    elif a==9:
        pic = discord.File(os.path.join("items","mygo9.jpg"))
    elif a==10:
        pic = discord.File(os.path.join("items","mygo10.jpg"))
    await ctx.send(file=pic)

@bot.command()
async def guess(ctx):
    
    ans = random.randint(1, 100)
    print(ans)
    
    await ctx.send("請在10次內猜1-100的整數數字 輸入:退出遊戲以退出")
    count = 1
    def is_valid(m):
        return m.author == ctx.author
    
    for _ in range(10):
        try:
        
            Guess = await bot.wait_for("message", timeout=300.0)
            
            if Guess.content == "退出遊戲":
                await ctx.send(f"已退出遊戲，你總共猜了{count}次")
                return
            
            elif int(Guess.content) == ans:
                await ctx.send(f"答對，你總共猜了{count}次")
                return
            
            else:
                
                if int(Guess.content) > ans:
                    await ctx.send("太大")
                    count = count+1
                
                elif int(Guess.content) < ans:
                    await ctx.send("太小")
                    count = count+1
                
                else:
                    await ctx.send("請輸入數字")

        except:
            await ctx.send("請輸入數字")
    await ctx.send("猜太多次了")

@bot.command()
async def now(ctx):
    
    await ctx.send(datetime.datetime.now())
    

@bot.command() 
async def test(ctx):

    retStr = str("""```css\n"This is some colored Text"\n```""")
    await ctx.send(retStr)

@bot.command(pass_context = True)
async def leave(ctx):
    if(ctx.voice_client):
        guild_id = ctx.guild.id
        # 清除佇列和當前歌曲
        queues[guild_id] = []
        current_songs[guild_id] = None
        repeat_modes[guild_id] = False
        loop_modes[guild_id] = True  # 重置為預設值
        
        await ctx.voice_client.disconnect()
        await ctx.send("👋 已離開語音頻道")
    else:
        await ctx.send("是在哭喔")
        
@bot.command()
async def cal(ctx):
    b = time.localtime().tm_year
    c = time.localtime().tm_mon
    a = calendar.month(b,c)
    await ctx.send(a)

@bot.command()
async def getsticker(ctx):
    guild = ctx.guild
    emojis = guild.emojis
    
    if emojis:
        emoji_list = "\n".join([str(emoji) for emoji in emojis])
        await ctx.send(f"伺服器貼圖列表：\n{emoji_list}")
    else:
        await ctx.send("伺服器內沒有自訂貼圖。")

@bot.command()
async def tag(ctx, target: discord.Member):
    print(target)
    await ctx.send(f"你被提及了，{target.mention}！")
    
    if str(target) == "_zongon":
        await ctx.send(f"{target.mention}今天醜巴 超過12:00")

@bot.command(pass_context = True)
async def join(ctx):
    if ctx.voice_client is None:
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            await channel.connect()
        else:
            await ctx.send("你不在語音頻道裡。")
    else:
        await ctx.send("我已經在語音頻道了。")

@bot.command()
async def detect(ctx, member: discord.Member):
    if member.status == discord.Status.online:
        await ctx.send(f"{member.display_name} 現在在線上！")
    else:
        await ctx.send(f"{member.display_name} 不在線上！")

# 新增的音樂播放指令
@bot.command()
async def play(ctx, url):
    # 檢查用戶是否在語音頻道
    if not ctx.author.voice:
        await ctx.send("❌ 你必須先加入語音頻道！")
        return
    
    # 自動加入語音頻道
    if not ctx.voice_client:
        channel = ctx.author.voice.channel
        await channel.connect()
    
    guild_id = ctx.guild.id
    queue = get_queue(guild_id)
    
    try:
        # 取得影片資訊
        await ctx.send("🔍 正在搜尋影片...")
        data = await bot.loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        
        if 'entries' in data:
            data = data['entries'][0]
        
        song_info = {
            'title': data['title'],
            'url': data['webpage_url'],
            'duration': data.get('duration', 0),
            'uploader': data.get('uploader', '未知'),
            'requester': ctx.author.display_name
        }
        
        # 如果目前沒有播放，直接播放
        if not ctx.voice_client.is_playing():
            set_current_song(guild_id, song_info)
            player = await YTDLSource.from_url(song_info['url'], loop=bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
            
            embed = discord.Embed(title="🎵 正在播放", color=0x00ff00)
            embed.add_field(name="歌曲", value=song_info['title'], inline=False)
            embed.add_field(name="上傳者", value=song_info['uploader'], inline=True)
            embed.add_field(name="請求者", value=song_info['requester'], inline=True)
            await ctx.send(embed=embed)
        else:
            # 加入佇列
            queue.append(song_info)
            embed = discord.Embed(title="➕ 已加入佇列", color=0xffff00)
            embed.add_field(name="歌曲", value=song_info['title'], inline=False)
            embed.add_field(name="佇列位置", value=f"第 {len(queue)} 首", inline=True)
            embed.add_field(name="請求者", value=song_info['requester'], inline=True)
            await ctx.send(embed=embed)
            
    except Exception as e:
        await ctx.send(f"❌ 播放時發生錯誤: {str(e)}")

@bot.command()
async def skip(ctx):
    if not ctx.voice_client:
        await ctx.send("❌ 機器人不在語音頻道中")
        return
    
    if not ctx.voice_client.is_playing():
        await ctx.send("❌ 沒有正在播放的歌曲")
        return
    
    # 停止當前播放並自動播放下一首
    # play_next 函數會自動處理循環邏輯，所以這裡不需要手動添加到佇列
    ctx.voice_client.stop()
    await ctx.send("⏭️ 已跳過當前歌曲")

@bot.command()
async def repeat(ctx):
    if not ctx.voice_client:
        await ctx.send("❌ 機器人不在語音頻道中")
        return
    
    guild_id = ctx.guild.id
    current_mode = get_repeat_mode(guild_id)
    new_mode = not current_mode
    set_repeat_mode(guild_id, new_mode)
    
    if new_mode:
        await ctx.send("🔂 單曲重複模式已開啟")
    else:
        await ctx.send("▶️ 單曲重複模式已關閉")

@bot.command()
async def queue(ctx):
    guild_id = ctx.guild.id
    queue = get_queue(guild_id)
    current_song = get_current_song(guild_id)
    
    embed = discord.Embed(title="🎵 播放佇列", color=0x0099ff)
    
    # 顯示播放模式
    modes = []
    if get_repeat_mode(guild_id):
        modes.append("🔂 單曲重複")
    if get_loop_mode(guild_id):
        modes.append("🔁 循環播放")
    
    if modes:
        embed.add_field(name="播放模式", value=" | ".join(modes), inline=False)
    
    if current_song:
        embed.add_field(name="正在播放", value=f"{current_song['title']}", inline=False)
    
    if queue:
        queue_list = []
        for i, song in enumerate(queue[:10], 1):  # 只顯示前10首
            queue_list.append(f"{i}. {song['title']}")
        
        embed.add_field(name="即將播放", value="\n".join(queue_list), inline=False)
        
        if len(queue) > 10:
            embed.add_field(name="", value=f"... 還有 {len(queue)-10} 首歌曲", inline=False)
    else:
        embed.add_field(name="佇列", value="佇列為空", inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
async def nowplaying(ctx):
    guild_id = ctx.guild.id
    current_song = get_current_song(guild_id)
    
    if not current_song:
        await ctx.send("❌ 沒有正在播放的歌曲")
        return
    
    embed = discord.Embed(title="🎵 正在播放", color=0x00ff00)
    embed.add_field(name="歌曲", value=current_song['title'], inline=False)
    embed.add_field(name="上傳者", value=current_song['uploader'], inline=True)
    embed.add_field(name="請求者", value=current_song['requester'], inline=True)
    
    # 顯示播放模式
    modes = []
    if get_repeat_mode(guild_id):
        modes.append("🔂 單曲重複")
    if get_loop_mode(guild_id):
        modes.append("🔁 循環播放")
    
    if modes:
        embed.add_field(name="模式", value=" | ".join(modes), inline=False)
    
    await ctx.send(embed=embed)

# 從環境變數讀取 Bot Token
token = os.getenv('DISCORD_BOT_TOKEN')

if not token:
    print("❌ 找不到 DISCORD_BOT_TOKEN 環境變數")
    print("請按照以下步驟設定：")
    print("1. 複製 .env.example 為 .env")
    print("2. 在 .env 中填入你的 Bot Token")
    exit(1)

bot.run(token)