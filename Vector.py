import discord
from discord.ext import commands
from utils.config import Config
from utils.logger import setup_logging
from cogs.tickets import TicketCog
from cogs.utility import UtilityCog
from cogs.moderation import ModerationCog
from cogs.embed_commands import EmbedCommandsCog

class VilyxBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.messages = True
        intents.guilds = True
        intents.message_content = True

        super().__init__(command_prefix="!", intents=intents)

        self.config = Config()
        setup_logging()

    async def setup_hook(self):
        """Called when the bot is starting up"""
        # Load cogs
        await self.add_cog(TicketCog(self))
        await self.add_cog(UtilityCog(self))
        await self.add_cog(ModerationCog(self))
        await self.add_cog(EmbedCommandsCog(self))

        # Sync commands to guild
        guild = discord.Object(id=self.config.guild_id)
        try:
            synced = await self.tree.sync(guild=guild)
            print(f"Synced {len(synced)} slash commands to guild ${self.config.guild_id}")
        except Exception as e:
            print(f"Failed to sync commands: ${e}")

    async def on_ready(self):
        """Called when the bot is ready"""
        await self.change_presence(
            status=discord.Status.dnd,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=self.config.status_text
            )
        )
        print(f"Bot online as {self.user}")

def main():
    bot = VilyxBot()
    bot.run(bot.config.token)

if __name__ == "__main__":
    main()