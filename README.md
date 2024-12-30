How to use for your own servers:
Go To https://discord.com/developers/applications
Create a New Application
Go Into The Bot Tab
Click Reset Token
Copy The Token
In The Folder with bot.py make a file called .env
inside of that file, put

DISCORD_BOT_TOKEN=your_token

replace your_token with the token you copied from discord
then, inside of command prompt, type

pip install discord.py yt-dlp python-dotenv pydub aiohttp

make sure ffmpeg is installed

Mac OS: brew install ffmpeg

Linux: sudo apt update

       sudo apt install ffmpeg

Windows: https://ffmpeg.org/download.html

Then just run the python file and it is ready to go!
