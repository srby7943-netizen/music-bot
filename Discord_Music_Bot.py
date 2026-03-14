import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
from youtubesearchpython import VideosSearch
import asyncio
from flask import Flask
from threading import Thread
import os

# --- خدعة تشغيل الموقع عشان Render ميفصلش البوت (24 ساعة مجاناً) ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online!"
def run():
    # استخدام البورت المخصص لـ Render لتجنب خطأ الـ Failed
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

ytdl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'cookiefile': 'cookies.txt.txt',
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@bot.command(name='play', aliases=['p'])
async def play(ctx, *, search: str):
    if not ctx.author.voice: return await ctx.send("❌ ادخل روم الأول!")
    vc = ctx.voice_client or await ctx.author.voice.channel.connect(self_deaf=True)
    async with ctx.typing():
        search_res = VideosSearch(search, limit=1).result()['result']
        if not search_res: return await ctx.send("❌ ملقيتش الأغنية!")
        url = search_res[0]['link']
        with YoutubeDL(ytdl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
    await ctx.send(f"🎵 بدأنا تشغيل: **{info['title']}**")
    # السيرفر بيتعرف على FFmpeg أوتوماتيكياً من المكتبات
    vc.play(discord.FFmpegOpusAudio(audio_url, **FFMPEG_OPTIONS))

@bot.command()
async def stop(ctx):
    if ctx.voice_client: await ctx.voice_client.disconnect()

async def main():
    async with bot:
        keep_alive() # تشغيل الموقع الوهمي لضمان الاستمرارية
        # --- حط التوكن الجديد بتاعك تحت هنا ---
        await bot.start('MTQ4MTgxNjgzOTc3NTU4NDQ0MA.GqIlIa.OiB30et3TGouqFXg-K909ynQsZDSi6ivx2Lvms')

if __name__ == "__main__":
    asyncio.run(main())
