import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import asyncio


SPOTIPY_CLIENT_ID = 'YOUR_CLIENT_ID'
SPOTIPY_CLIENT_SECRET = 'YOUR_CLIENT_SECRET'

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

song_queue = []


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


async def play_next(ctx):
    if song_queue:
        url = song_queue.pop(0)
        await play_song(ctx, url)

async def play_song(ctx, url):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client is None:
        channel = ctx.message.author.voice.channel
        voice_client = await channel.connect()

    ydl_opts = {
        'format': 'bestaudio',
        'quiet': True,
        'noplaylist': True,
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info['url']

    source = discord.FFmpegPCMAudio(audio_url)
    voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))

    await ctx.send(f'Now playing: {info["title"]}')


@bot.command(name='play', help='Plays a song')
async def play(ctx, url):
    if 'spotify.com' in url:
        track_info = sp.track(url)
        track_name = track_info['name']
        track_artist = track_info['artists'][0]['name']
        search_query = f"{track_name} {track_artist} audio"
        
        ydl_opts = {
            'format': 'bestaudio',
            'quiet': True,
            'noplaylist': True,
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{search_query}", download=False)['entries'][0]
            url = info['url']

    song_queue.append(url)
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client is None or not voice_client.is_playing():
        await play_song(ctx, url)
    else:
        await ctx.send(f'Added to queue: {url}')


@bot.command(name='skip', help='Skips the current song')
async def skip(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send('Skipped the current song.')


@bot.command(name='stop', help='Stops the song')
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        song_queue.clear()
        await ctx.send('Stopped playing and cleared the queue.')

bot.run('YOUR_BOT_TOKEN')