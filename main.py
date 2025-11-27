# main.py
import discord
import os
import aiohttp
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")


class AnimeBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='/', intents=discord.Intents.default())
        self.session = None

    async def setup_hook(self):
        # Create a single session for the entire lifetime of the bot
        self.session = aiohttp.ClientSession()

        # Load the Search Cog
        await self.load_extension('cogs.search')

        # Sync Slash Commands
        await self.tree.sync()
        print("Commands synced and Cogs loaded!")

    async def close(self):
        # Close the session properly when bot shuts down
        await super().close()
        if self.session:
            await self.session.close()


bot = AnimeBot()

if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("Error: DISCORD_TOKEN not found in .env")