from __future__ import annotations

import re
import asyncio
import requests

from discord import Embed, Intents, Activity, Status, Color, ActivityType
from discord import FFmpegOpusAudio, Message, utils
from discord.ext import commands
from yt_dlp import YoutubeDL
from youtubesearchpython import VideosSearch
 
from discord import VoiceClient, Member, VoiceState
from typing import TYPE_CHECKING , Union , Optional

if TYPE_CHECKING:
    from discord.ext.commands import Bot

from os import getenv

EMBED_COLOR = 0x000000

bot = commands.Bot(command_prefix='!', 
                   intents=Intents.all(), 
                   activity=Activity(type=ActivityType.listening, 
                                     name="Music Bot."),
                   status=Status.idle,
                   help_command=None)


ytdl_format_options = {
    'format': 'worstaudio',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

def is_youtube_link(message_content):
    pattern = [r'https?://(?:www\.)?youtu\.be/([^/?]+)',r'https?://(?:www\.)?youtube\.com/watch\?v=([^&]+)']
    for valid_url in pattern:
        if re.match(valid_url,message_content):
            return True
    return False


def is_link_valid(url):
    try:
        response = requests.head(url, allow_redirects=True)
        return response.status_code == 200
    except:
        return False
    

def get_duration(time):
    if time is None:
        return "LIVE STREAM :purple_circle:"
    hours,minutes,seconds = int(f"{time // 3600:02}"),int(f"{(time % 3600) // 60:02}"),int(f"{time % 60:02}")
    return f"{hours if hours > 0 else ''}{':' if hours > 0 else ''}{minutes:02d}:{seconds:02d}"

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot
        self.voice_client: Union[VoiceClient, None] = None
        self.isloop = False
        self.skip = False
        self.data: dict = {}

    def get_data(self, url : str , ctx : commands.Context) -> dict:
        ytdl = YoutubeDL(ytdl_format_options)
        ytdl_info = ytdl.extract_info(url, download=False)
        return {
            'user': ctx.author,
            'title': ytdl_info.get('title' , 'غير معروف'),
            'url': ytdl_info.get('url'),
            'duration': ytdl_info.get('duration'),
            'thumbnail': ytdl_info.get('thumbnail')
        }
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Connected To {self.bot.user.name}")

    @commands.command(name='repeat', aliases=['r','loop'])
    async def repeat_command(self, ctx: commands.Context):
        if ctx.author.voice is None:
            return
        if ctx.guild.get_member(self.bot.user.id) not in ctx.author.voice.channel.members:
            return
        if self.voice_client.is_playing() or self.voice_client.is_paused():
            if self.data is None:
                await ctx.reply("**إذا كـنـت تــقـرأ الــرســالـة يــرجــى التــواصــل مــع <@526805114091208734>**")
            else:
                if self.data['user'] is not None and self.data['user'] != ctx.author:
                    await ctx.reply(f"**:x: Only The Music Player ({self.data['user'].mention}) Can Use This Command**")
                elif self.isloop:
                    self.isloop = False
                    await ctx.reply(f":arrow_forward: Playing **{self.data['title']} (`{get_duration(self.data['duration'])}`)**")
                else:
                    self.isloop = True
                    await ctx.reply(f"<:repeat:1279207003172110447> Repeat **{self.data['title']} (`{get_duration(self.data['duration'])}`)**")
        else:
            await ctx.reply("**لا يــوجــد اي أغــنـيـة لأعــادتــها مــره أخــرى  :x:**")

    @commands.command(name='play', aliases= ['p','ش'])
    async def play_command(self, ctx: commands.Context, *, message: Optional[str]):
        if ctx.author.voice is None:
            await ctx.reply(f"**:x: You Need To Be In A voice Channel To use This Command**")
            return
        if message is None:
            await ctx.reply(f"**{self.bot.command_prefix}play `<song name || URL>`**")
            return
        if not(self.voice_client):
            await ctx.author.voice.channel.connect(self_deaf=True)
        elif self.voice_client.is_playing() or self.voice_client.is_paused():
            await ctx.reply("**:x: Music Bot Are Currently In Use. Please Wait A Moment To Complete. <:timer:1279207037619929259>**")
            return
        elif self.voice_client.channel != ctx.author.voice.channel:
            await ctx.voice_client.move_to(ctx.author.voice.channel)
        async with ctx.typing():
            if not is_youtube_link(message):
                try:
                    search_result = VideosSearch(message, limit=1).result()['result']
                except:
                    await ctx.reply(f"**:x: I Couldn't Find A Song With This Name `{message}`**")
                    return
                if len(search_result) <= 0:
                    await ctx.reply(f"**:x: I Couldn't Find A Song With This Name `{message}`**")
                    return
                url = search_result[0]['link']
            else:
                if is_link_valid(message):
                    url = message
                else:
                    await ctx.reply("**:x: Link You Enter Is Invalid**")
                    return
        
        self.data = self.get_data(url=url, ctx=ctx)
        
        if self.data['url'] is None:
            await ctx.reply("**:x: Cannot Fetch This Song**")
            return
        
        embed = Embed(
            description=f"**:arrow_forward: [{self.data['title']}]({url}) - [`{get_duration(self.data['duration'])}`]**",
            color=EMBED_COLOR
        )
        embed.set_thumbnail(url=self.data['thumbnail'])
        embed.set_footer(text=f"By {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        embed.set_author(name="Now Playing",icon_url=self.bot.user.display_avatar.url)
        await ctx.send(embed=embed)

        while True:
            self.voice_client.play(FFmpegOpusAudio(self.data['url']))
            while self.voice_client.is_playing() or self.voice_client.is_paused():
                await asyncio.sleep(0.1)
                if self.skip:
                    self.voice_client.stop()
                    self.skip = False
            if self.isloop:
                continue
            self.data = {}
            return
        
    @commands.command(name='skip', aliases=['s'])
    async def skip_command(self , ctx: commands.Context):
        if ctx.author.voice is None:
            return
        if ctx.guild.get_member(self.bot.user.id) not in ctx.author.voice.channel.members:
            return
        if self.voice_client.is_playing() or self.voice_client.is_paused():
            if self.data is None:
                await ctx.reply("**إذا كـنـت تــقـرأ الــرســالـة يــرجــى التــواصــل مــع <@526805114091208734>**", delete_after=10)
            else:
                if self.data['user'] is not None and (self.data['user'] != ctx.author and self.data['user'] in ctx.author.voice.channel.members):
                    await ctx.reply(f"**:x: Only The Music Player ({self.data['user'].mention}) Can Use This Command**")
                else:
                    self.skip = True
                    self.isloop = False
                    await ctx.reply(f":track_next: Skipped **{self.data['title']} (`{get_duration(self.data['duration'])}`)**")
        else:
            await ctx.reply("**:x: There Are No Song To Skip**")
    
    @commands.command(name='stop', aliases=['leave','disconnect'])
    async def stop_command(self , ctx: commands.Context):
        if ctx.author.voice is None:
            return
        if ctx.guild.get_member(self.bot.user.id) not in ctx.author.voice.channel.members:
            return
        if self.voice_client.is_playing() or self.voice_client.is_paused():
            if self.data is None:
                await ctx.reply("**إذا كـنـت تــقـرأ الــرســالـة يــرجــى التــواصــل مــع <@526805114091208734>**", delete_after=10)
            else:
                if self.data['user'] is not None and (self.data['user'] != ctx.author and self.data['user'] in ctx.author.voice.channel.members):
                    await ctx.reply(f"**:x: Only The Music Player ({self.data['user'].mention}) Can Use This Command**")
                else:
                    await self.voice_client.disconnect()
                    self.skip = False
                    self.isloop = False
                    await ctx.reply(f"**:wave: Bye**")
        else:
            if self.voice_client:
                await self.voice_client.disconnect()
                self.skip = False
                self.isloop = False
                await ctx.reply(f"**:wave: Bye**")
            else:
                await ctx.reply(f"**:x: I'm Not Connected To A Voice Channel**")
    @commands.Cog.listener()
    async def on_voice_state_update(self,member: Member, before: VoiceState, after: VoiceState):

        if member.id == self.bot.user.id:
            if after.channel is None:
                self.voice_client = None
                self.data = {}

            else:
                self.voice_client = utils.get(self.bot.voice_clients, guild=member.guild)

async def on_setup():
    await bot.add_cog(Music(bot))

bot.setup_hook = on_setup

bot.run('MTQ4MTgxNjgzOTc3NTU4NDQ0MA.GCLsO2.kvUhWdHCJVz6OaU1IXx2daL410YHQE6qBhldaU')
