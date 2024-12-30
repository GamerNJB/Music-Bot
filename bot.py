import discord
from discord.ext import commands
from discord import app_commands
import os
import time
import yt_dlp  # Updated to yt-dlp
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Get the bot token from the environment variables
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

#------ Bot Setup ------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

#--- Bot Startup
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')  # Bot Name
    print(bot.user.id)  # Bot ID

    # Sync the commands globally
    try:
        await bot.tree.sync()  # Sync globally
        print("Successfully synced commands globally")
    except Exception as e:
        print(f"Error syncing commands: {str(e)}")

#------ Slash Commands ------
@bot.tree.command()
async def help(interaction: discord.Interaction):
    """Help"""  # Description when viewing / commands
    await interaction.response.send_message("hello")

#------ Sync Tree ------
@bot.command()
@commands.is_owner()
async def sync(ctx: commands.Context):
    """Sync commands globally."""
    try:
        await ctx.bot.tree.sync()
        await ctx.send("Synced commands globally.")
    except Exception as e:
        await ctx.send(f"Error syncing commands: {str(e)}")

#------ Add Command (Add Song) ------
@bot.tree.command(name="add", description="Add a song to the playlist")
async def add(interaction: discord.Interaction, url: str, title: str):
    try:
        if not title:
            await interaction.response.send_message("Please provide a title for the song using `/add [url] [title]`.")
            return

        # Define the folder based on the server ID
        guild_folder = str(interaction.guild.id)
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

        # Download the audio file using yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
            except Exception as e:
                await interaction.response.send_message(f"Error downloading the audio: {str(e)}")
                return

        # Wait to ensure the download completes
        time.sleep(1)

        # Define the final mp3 file path
        final_mp3_path = f'{guild_folder}/{title}.mp3'

        # Check if the webm file exists before renaming
        if os.path.isfile(temp_file_path):
            os.rename(temp_file_path, final_mp3_path)
        else:
            await interaction.response.send_message(f"Downloaded file not found at {temp_file_path}")
            return

        # Check if the mp3 file exists now
        if os.path.isfile(final_mp3_path):
            await interaction.response.send_message(f"Downloaded and added {title} to the playlist.")
        else:
            await interaction.response.send_message(f"Error: The file {final_mp3_path} does not exist.")
    
    except Exception as e:
        await interaction.response.send_message(f"Error adding the song: {str(e)}")

#------ /songlist Command ------
@bot.tree.command(name="songlist", description="List all the MP3 files in the server's folder")
async def songlist(interaction: discord.Interaction):
    """List all MP3 files in the server's folder."""
    guild_folder = str(interaction.guild.id)
    
    # Check if the folder exists
    if not os.path.exists(guild_folder):
        await interaction.response.send_message("No songs found for this server.")
        return

    # Get the list of .mp3 files in the folder
    mp3_files = [f for f in os.listdir(guild_folder) if f.endswith(".mp3")]
    
    if mp3_files:
        file_list = "\n".join(mp3_files)
        await interaction.response.send_message(f"Available songs:\n{file_list}")
    else:
        await interaction.response.send_message("No MP3 files found in the server's folder.")

#------ Example Slash Command to Join Voice Channel ------
@bot.tree.command(name="join", description="Join the voice channel")
async def join(interaction: discord.Interaction):
    """Join the voice channel."""
    if interaction.user.voice:
        channel = interaction.user.voice.channel
        await channel.connect()
        await interaction.response.send_message(f"Joined {channel.name}")
    else:
        await interaction.response.send_message("You need to be in a voice channel to use this command.")

#------ Example Slash Command to Stop Music------
@bot.tree.command(name="stop", description="Stop the currently playing song")
async def stop(interaction: discord.Interaction):
    """Stop the currently playing song."""
    if interaction.guild.voice_client:
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("Music stopped.")
    else:
        await interaction.response.send_message("No music is currently playing.")

#------ Example Slash Command to Play Song ------
@bot.tree.command(name="play", description="Play a song by name")
async def play(interaction: discord.Interaction, songname: str):
    """Play a song."""
    if interaction.guild.voice_client is None:
        if interaction.user.voice:
            await interaction.user.voice.channel.connect()
        else:
            await interaction.response.send_message("You need to be in a voice channel to play music.")
            return

    if interaction.guild.voice_client.is_playing():
        await interaction.response.send_message("Already playing audio.")
        return

    song_path = os.path.join(os.getcwd(), f'{songname}.mp3')
    if os.path.isfile(song_path):
        audio_source = discord.FFmpegPCMAudio(song_path)
        interaction.guild.voice_client.play(audio_source, after=lambda e: print(f'Finished playing {songname}'))
        await interaction.response.send_message(f"Now playing {songname}")
    else:
        await interaction.response.send_message("Song not found.")

# Run the bot with your token loaded from the .env file
bot.run(TOKEN)
