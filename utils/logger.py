import discord
from typing import Optional

def setup_logging():
    """Setup initial logging configuration"""
    pass

async def log_to_channel(bot, message: str):
    """Send a log message to the configured log channel"""
    from utils.config import Config
    config = Config()

    channel = bot.get_channel(config.get_channel_id("logs"))
    if channel:
        await channel.send(message)