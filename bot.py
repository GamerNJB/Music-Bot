import discord
from discord.ext import commands
import os
import time
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

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
async def add(ctx, url: str, *, title: str = None):
    try:
        if not title:
            await ctx.send("Please provide a title for the song using `/add [url] [title]`.")
            return

        # Define the folder based on the server ID
        guild_folder = str(ctx.guild.id)
        if not os.path.exists(guild_folder):
            os.makedirs(guild_folder)

        # Define the temporary download file path
        temp_file_path = f'{guild_folder}/{title}.webm'

        # Set up the download options for yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': temp_file_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'noplaylist': True,
        }

        # Download the audio file
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        # Wait to ensure the download completes
        time.sleep(1)

        # Define the final mp3 file path
        final_mp3_path = f'{guild_folder}/{title}.mp3'

        # Rename the webm file to mp3
        if os.path.isfile(temp_file_path):
            os.rename(temp_file_path, final_mp3_path)

        await ctx.send(f"Downloaded and added {title} to the playlist.")
    except Exception as e:
        await ctx.send(f"Error adding the song: {str(e)}")

@bot.command()
async def playlist(ctx, action, playlist_name=None, *, url=None):
    playlist_folder = os.path.join(os.getcwd(),
                                   str(ctx.guild.id),
                                   playlist_name)

    if action == "add" and playlist_name and url:
        # Check if the song already exists in the playlist
        if os.path.exists(playlist_folder):
            files = os.listdir(playlist_folder)
            for file in files:
                if file.endswith(".mp3") and file.lower() in url.lower():
                    await ctx.send(f"{file} already exists in the playlist.")
                    return

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

        playlist_folder = os.path.join(os.getcwd(),
                                       str(ctx.guild.id),
                                       playlist_name)
        if os.path.exists(playlist_folder):
            files = [f for f in os.listdir(playlist_folder) if f.endswith('.mp3')]
            if files:
                for file in files:
                    file_path = os.path.join(playlist_folder, file)
                    audio_source = discord.FFmpegPCMAudio(file_path)
                    ctx.voice_client.play(
                        audio_source,
                        after=lambda e: print(f'Finished playing {file}'))
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

    song_path = os.path.join(os.getcwd(), str(ctx.guild.id),
                             f'{songname}.mp3')
    if os.path.isfile(song_path):
        audio_source = discord.FFmpegPCMAudio(song_path)
        ctx.voice_client.play(
            audio_source,
            after=lambda e: print(f'Finished playing {songname}'))
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
    song_folder = os.path.join(os.getcwd(), str(ctx.guild.id))
    if os.path.exists(song_folder):
        songs = [f for f in os.listdir(song_folder) if f.endswith('.mp3')]
        if songs:
            await ctx.send("Available songs:\n" + "\n".join(songs))
        else:
            await ctx.send("No songs found.")
    else:
        await ctx.send("No songs directory found for this server.")

bot.run(TOKEN)
