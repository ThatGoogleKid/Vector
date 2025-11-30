import discord
from discord.ext import commands
from discord import app_commands

class UtilityCog(commands.Cog):
    """Utility commands like IP information"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ip", description="Get the server IP")
    @app_commands.guild_only()
    async def ip(self, interaction: discord.Interaction):
        """Show server IP information"""
        embed = discord.Embed(
            title="🎮 How to Join Vilyx",
            description=(
                "> 1. Click on **Multiplayer**\n"
                "> 2. Click on **Add Server**\n"
                "> 3. For **Server Address**, type in `play.vilyx.net`\n"
                "> 4. Save and **Connect!**"
            ),
            color=0x00AAEE
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="sendip", description="Send the server IP publicly")
    @app_commands.guild_only()
    async def sendip(self, interaction: discord.Interaction):
        """Send server IP to channel (staff only)"""
        allowed_roles = ["mod", "sr_mod", "admin", "sr_admin", "manager", "developer", "owner"]
        
        if not self.bot.config.has_role(interaction.user.roles, allowed_roles):
            return await interaction.response.send_message(
                "You do not have permission to use this command.", 
                ephemeral=True
            )
        
        embed = discord.Embed(
            title="🎮 How to Join Vilyx",
            description=(
                "> 1. Click on **Multiplayer**\n"
                "> 2. Click on **Add Server**\n"
                "> 3. For **Server Address**, type in `play.vilyx.net`\n"
                "> 4. Save and **Connect!**"
            ),
            color=0x00AAEE
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=False)

async def setup(bot):
    await bot.add_cog(UtilityCog(bot))