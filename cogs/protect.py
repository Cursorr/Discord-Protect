import discord
import json
import random
import string
import asyncio
import os

from captcha.image import ImageCaptcha
from discord.ext import commands, tasks


class Captcha(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self._config = json.load(open("config.json", "r"))
        self._captchas = {}
        self._verification_phase = {}
        self._user_tries = {}
        self.update_json.start()

    # Creating this task to not open the json file every join 
    @tasks.loop(seconds=10)
    async def update_json(self):
        self._config = json.load(open("config.json", "r"))

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.User):
        if member.bot: return
        
        captcha_config = self._config["captcha"]
        is_captcha_enable = captcha_config["is_enable"]
        verification_channel: discord.TextChannel = self.bot.get_channel(captcha_config["verify_channel"])

        if not is_captcha_enable: return
        
        # I will comment my code in this part to understant what
        # I did because the other parts are easy to understand
        
        # Adding member in cache (k -> member.id, v -> Tries numbers)
        self._verification_phase[member.id] = 0
        
        # Storing messages sent by users to delete them later
        self._user_tries[member.id] = []

        # Generationg the captcha text
        text = ''.join(random.choice(string.ascii_uppercase) for _ in range(6))

        # Creating an image instance
        captcha = ImageCaptcha(width=300, height=100)
        
        # Merging image and text 
        captcha.generate(text)

        # Saving captcha image
        captcha.write(text, f"captchas/{member.id}.png")

        captcha_file = discord.File(f"captchas/{member.id}.png")
        temp_captcha = await verification_channel.send("Please write the captcha down here.", file=captcha_file) 
        
        self._captchas[member.id] = temp_captcha

        try:
            msg = await self.bot.wait_for('message', 
            check=lambda message: message.content.upper() == text and message.author.id == member.id and message.channel == verification_channel, timeout=captcha_config["timeout"])
            
            # Deleting user from cache after succeding the verification phase
            del self._verification_phase[member.id]
            temp_succes_message = await verification_channel.send(f"{member} Just passed the Captcha")

            # Deleting captcha img from directory 
            os.remove(f"captchas/{member.id}.png")

        except asyncio.TimeoutError:
            await member.kick()

        # Deleting messages in channel
        await asyncio.sleep(10)
        
        await temp_captcha.delete()
        await temp_succes_message.delete()

        for user_try in self._user_tries[member.id]:
            await user_try.delete()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        member: discord.Member = message.author

        # Adding tries to the cache
        if member.id in self._verification_phase and message.channel.id == self._config["captcha"]["verify_channel"]:
            self._verification_phase[member.id] += 1
            self._user_tries[member.id].append(message)

            # Kicking the member if it goes higher than tries you give
            if self._verification_phase[member.id] >= self._config["captcha"]["tries"]:
                await member.kick()

                for user_try in self._user_tries[member.id]:
                    await user_try.delete()

                await self._captchas[member.id].delete()
                del self._captchas[member.id]

                try:
                    del self._verification_phase[member.id]
                except KeyError:
                    raise
                
                os.remove(f"captchas/{member.id}.png")
                del self._user_tries[member.id]

def setup(bot):
    bot.add_cog(Captcha(bot))