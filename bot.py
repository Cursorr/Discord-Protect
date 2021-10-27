import discord
import asyncio
import json
import os

from discord.ext import commands
from discord_slash import SlashCommand

class DiscordProtect(commands.Bot):
    def __init__(self):
        self._config = json.load(open("config.json", "r"))
        super().__init__(
            self._config["prefix"],
            intents=discord.Intents.all(),
        )
        SlashCommand(self, sync_commands=True)

    async def on_ready(self):
        print(f"[{self._config['bot_name']}] - Connected.")
        self.status_loop = asyncio.ensure_future(self.bot_presence())

    async def bot_presence(self):
        while True:
            await self.change_presence(activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Hello !"
            ))
            await asyncio.sleep(120)

    def run(self):
        for extention in os.listdir("cogs"):
            if extention.endswith(".py"):
                self.load_extension(f"cogs.{extention[:-3]}")
                print(f"{extention} Loaded Successfully")
        super().run(self._config["token"])
        

if __name__ == '__main__':
    bot_instance = DiscordProtect()
    bot_instance.run()