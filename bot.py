import discord
from discord.ext import commands
from discord import app_commands
import os
import yt_dlp  # Updated to yt-dlp
import time
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

#------ /add Command (Add Song to Playlist) ------
@bot.tree.command(name="add", description="Add a song to a playlist")
async def add(interaction: discord.Interaction, url: str, title: str, playlist: str):
    """Add a song to the specified playlist."""
    try:
        if not title or not playlist:
            await interaction.response.send_message("Please provide both a song title and playlist name using `/add [url] [title] [playlist]`.")
            return

        # Define the folder for the playlist
        guild_folder = str(interaction.guild.id)
        playlist_folder = os.path.join(guild_folder, playlist)

        # Create the folder if it doesn't exist
        if not os.path.exists(playlist_folder):
            os.makedirs(playlist_folder)

        # Define the temporary download file path
        temp_file_path = f'{playlist_folder}/{title}.webm'

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
        final_mp3_path = f'{playlist_folder}/{title}.mp3'

        # Check if the webm file exists before renaming
        if os.path.isfile(temp_file_path):
            os.rename(temp_file_path, final_mp3_path)
        else:
            await interaction.response.send_message(f"Downloaded file not found at {temp_file_path}")
            return

        # Check if the mp3 file exists now
        if os.path.isfile(final_mp3_path):
            await interaction.response.send_message(f"Downloaded and added {title} to the playlist {playlist}.")
        else:
            await interaction.response.send_message(f"Error: The file {final_mp3_path} does not exist.")
    
    except Exception as e:
        await interaction.response.send_message(f"Error adding the song: {str(e)}")

#------ /play Command (Play Playlist) ------
@bot.tree.command(name="play", description="Play a playlist")
async def play(interaction: discord.Interaction, playlist: str):
    """Play all songs in a playlist."""
    guild_folder = str(interaction.guild.id)
    playlist_folder = os.path.join(guild_folder, playlist)

    # Check if the playlist folder exists
    if not os.path.exists(playlist_folder):
        await interaction.response.send_message(f"Playlist '{playlist}' not found.")
        return

    # Get the list of .mp3 files in the playlist folder
    mp3_files = [f for f in os.listdir(playlist_folder) if f.endswith(".mp3")]
    
    if not mp3_files:
        await interaction.response.send_message(f"No MP3 files found in the playlist '{playlist}'.")
        return

    # Ensure the bot is connected to a voice channel
    if not interaction.guild.voice_client:
        if interaction.user.voice:
            channel = interaction.user.voice.channel
            await channel.connect()
            print(f"Bot connected to voice channel: {channel.name}")
        else:
            await interaction.response.send_message("You need to be in a voice channel first.")
            print("Error: User is not in a voice channel.")
            return

    # Play all songs in the playlist one by one
    for mp3_file in mp3_files:
        file_path = os.path.join(playlist_folder, mp3_file)
        print(f"Attempting to play: {file_path}")

        # Ensure FFmpeg is correctly set up
        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn',
        }

        try:
            # Play the audio in the voice channel
            interaction.guild.voice_client.play(
                discord.FFmpegPCMAudio(file_path, **ffmpeg_options), after=lambda e: print('done', e)
            )
            await interaction.response.send_message(f"Now playing {mp3_file}.")
            print(f"Successfully started playing {mp3_file}")

            # Wait for the song to finish before playing the next one
            while interaction.guild.voice_client.is_playing():
                await asyncio.sleep(1)

        except Exception as e:
            await interaction.response.send_message(f"Error playing {mp3_file}: {str(e)}")
            print(f"Error playing {mp3_file}: {str(e)}")

    await interaction.response.send_message(f"Finished playing the playlist '{playlist}'.")

# Run the bot
bot.run(TOKEN)
