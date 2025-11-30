import discord
from discord.ext import commands
from discord import app_commands

class EmbedCommandsCog(commands.Cog):
    """Commands for creating custom embeds"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="sendembed", description="Send a custom embed to the channel")
    @app_commands.describe(
        title="The title of the embed",
        message="The main message/description. Use '||' for a new line",
        hex_color="The embed color in hex format (e.g., FF0000 for red). Optional"
    )
    @app_commands.guild_only()
    async def sendembed(
        self, 
        interaction: discord.Interaction, 
        title: str, 
        message: str, 
        hex_color: str = None
    ):
        """Send a custom embed (Manager+ only)"""
        allowed_roles = ["manager", "owner"]
        
        if not self.bot.config.has_role(interaction.user.roles, allowed_roles):
            return await interaction.response.send_message(
                "You do not have permission to use this command.", 
                ephemeral=True
            )
        
        # Process message (replace || with newlines)
        processed_message = message.replace("||", "\n")
        
        # Process color
        embed_color = 0x00AAEE  # Default blue
        
        if hex_color:
            hex_color = hex_color.lstrip('#')
            
            if len(hex_color) == 6:
                try:
                    embed_color = int(hex_color, 16)
                except ValueError:
                    await interaction.channel.send(
                        f"⚠️ Staff warning: The hex color '{hex_color}' was invalid. Using default color.", 
                        delete_after=10
                    )
            else:
                await interaction.channel.send(
                    f"⚠️ Staff warning: Hex color must be exactly 6 characters. Using default color.", 
                    delete_after=10
                )
        
        # Create embed
        embed = discord.Embed(
            title=title,
            description=processed_message,
            color=embed_color
        )
        
        # Send responses
        try:
            await interaction.response.send_message("Sending embed...", ephemeral=True)
            await interaction.channel.send(embed=embed)
            await interaction.followup.send("Embed successfully sent!", ephemeral=True)
        except discord.InteractionResponded:
            await interaction.channel.send(embed=embed)
            await interaction.followup.send("Embed successfully sent!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(EmbedCommandsCog(bot))