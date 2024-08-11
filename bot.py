import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import os
import re

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", str(name)).replace(' ', '_')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("You need to be in a voice channel to use this command.")

@bot.command()
async def add(ctx, name_or_link: str):
    try:
        # Check if the input is a URL
        if name_or_link.startswith('http'):
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{sanitize_filename(ctx.guild.id)}/%(title)s.%(ext)s',
                'noplaylist': True,
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(name_or_link, download=True)
                song_name = sanitize_filename(info.get('title', None))
        else:
            song_name = sanitize_filename(name_or_link)

        # Place the song in the correct folder
        guild_folder = sanitize_filename(str(ctx.guild.id))
        if not os.path.exists(guild_folder):
            os.makedirs(guild_folder)
        song_path = f"{guild_folder}/{song_name}.mp3"
        
        if not os.path.isfile(song_path):
            await ctx.send(f"Downloaded and added {song_name} to the playlist.")
        else:
            await ctx.send(f"{song_name} already exists in the playlist.")

    except Exception as e:
        await ctx.send(f"Error adding the song: {str(e)}")

@bot.command()
async def playlist(ctx, action, playlist_name=None, *, url=None):
    playlist_folder = os.path.join(os.getcwd(), sanitize_filename(ctx.guild.id), sanitize_filename(playlist_name))
    if action == "add" and playlist_name and url:
        if not os.path.exists(playlist_folder):
            os.makedirs(playlist_folder)
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{playlist_folder}/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)
            await ctx.send(f"Added {url} to the playlist {playlist_name}!")
        except Exception as e:
            await ctx.send(f"Error downloading the song: {str(e)}")
    elif action == "play" and playlist_name:
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You need to be in a voice channel to play music.")
                return

        if ctx.voice_client.is_playing():
            await ctx.send("Already playing audio.")
            return

        playlist_folder = os.path.join(os.getcwd(), sanitize_filename(ctx.guild.id), sanitize_filename(playlist_name))
        if os.path.exists(playlist_folder):
            files = os.listdir(playlist_folder)
            if files:
                for file in files:
                    file_path = os.path.join(playlist_folder, file)
                    audio_source = discord.FFmpegPCMAudio(file_path)
                    ctx.voice_client.play(audio_source, after=lambda e: print(f'Finished playing {file}'))
                    await ctx.send(f"Now playing {file}")
            else:
                await ctx.send("The playlist is empty.")
        else:
            await ctx.send("Playlist not found.")

@bot.command()
async def play(ctx, *, songname):
    if ctx.voice_client is None:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("You need to be in a voice channel to play music.")
            return

    if ctx.voice_client.is_playing():
        await ctx.send("Already playing audio.")
        return

    song_path = os.path.join(os.getcwd(), sanitize_filename(ctx.guild.id), f'{sanitize_filename(songname)}.mp3')
    if os.path.isfile(song_path):
        audio_source = discord.FFmpegPCMAudio(song_path)
        ctx.voice_client.play(audio_source, after=lambda e: print(f'Finished playing {songname}'))
        await ctx.send(f"Now playing {songname}")
    else:
        await ctx.send("Song not found.")

@bot.command()
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Playback stopped.")
    else:
        await ctx.send("No audio is playing currently.")

@bot.command()
async def songlist(ctx):
    song_folder = os.path.join(os.getcwd(), sanitize_filename(ctx.guild.id))
    if os.path.exists(song_folder):
        songs = [f for f in os.listdir(song_folder) if f.endswith('.mp3')]
        if songs:
            await ctx.send("Available songs:\n" + "\n".join(songs))
        else:
            await ctx.send("No songs found.")
    else:
        await ctx.send("No songs directory found for this server.")

TOKEN = 'MTI2NjIxMjI5OTE2NTY2MzI2Mw.GLnj2P.9CispXHv8_jyLY6oT5agUDgGBVVRknFvqpje5o'
bot.run(TOKEN)
