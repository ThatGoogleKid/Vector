import discord
from discord.ext import commands
from discord import app_commands
from utils.logger import log_to_channel

class ModerationCog(commands.Cog):
    """Staff promotion and demotion commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="promote", description="Promote a user to the next rank")
    @app_commands.guild_only()
    async def promote(self, interaction: discord.Interaction, user: discord.Member):
        """Promote a user (Manager+ only)"""
        allowed_roles = ["manager", "owner"]
        
        if not self.bot.config.has_role(interaction.user.roles, allowed_roles):
            return await interaction.response.send_message(
                "You do not have permission to use this command.", 
                ephemeral=True
            )
        
        guild = interaction.guild
        guild_roles = [guild.get_role(rid) for rid in self.bot.config.role_hierarchy]
        
        # Find current rank
        current_index = -1
        for idx, role in enumerate(guild_roles):
            if role in user.roles:
                current_index = idx
        
        # Check if already at top
        if current_index >= len(guild_roles) - 1:
            return await interaction.response.send_message(
                f"{user.display_name} is already at the highest rank.", 
                ephemeral=True
            )
        
        # Get roles
        next_role = guild_roles[current_index + 1]
        member_role = guild.get_role(self.bot.config.get_role_id("member"))
        mod_role = guild.get_role(self.bot.config.get_role_id("mod"))
        staff_role = guild.get_role(self.bot.config.get_role_id("staff"))
        
        # Add new role
        await user.add_roles(next_role)
        
        # Remove old role (except Member -> Mod transition)
        if current_index >= 0:
            current_role = guild_roles[current_index]
            if not (current_role == member_role and next_role == mod_role):
                await user.remove_roles(current_role)
        
        # Add staff role when promoting from Member to Mod
        if member_role in user.roles and next_role == mod_role and staff_role:
            await user.add_roles(staff_role)
        
        await interaction.response.send_message(
            f"{user.display_name} has been promoted to {next_role.name}.", 
            ephemeral=True
        )
        await log_to_channel(
            self.bot, 
            f"📈 **{interaction.user}** promoted **{user.display_name}** to **{next_role.name}**."
        )
    
    @app_commands.command(name="demote", description="Demote a user to the previous rank")
    @app_commands.guild_only()
    async def demote(self, interaction: discord.Interaction, user: discord.Member):
        """Demote a user (Manager+ only)"""
        allowed_roles = ["manager", "owner"]
        
        if not self.bot.config.has_role(interaction.user.roles, allowed_roles):
            return await interaction.response.send_message(
                "You do not have permission to use this command.", 
                ephemeral=True
            )
        
        guild = interaction.guild
        guild_roles = [guild.get_role(rid) for rid in self.bot.config.role_hierarchy]
        
        # Find current rank
        current_index = -1
        for idx, role in enumerate(guild_roles):
            if role in user.roles:
                current_index = idx
        
        # Check if already at bottom
        if current_index <= 0:
            return await interaction.response.send_message(
                f"{user.display_name} is already at the lowest rank.", 
                ephemeral=True
            )
        
        # Get roles
        prev_role = guild_roles[current_index - 1]
        current_role = guild_roles[current_index]
        member_role = guild.get_role(self.bot.config.get_role_id("member"))
        mod_role = guild.get_role(self.bot.config.get_role_id("mod"))
        staff_role = guild.get_role(self.bot.config.get_role_id("staff"))
        
        # Add new role
        await user.add_roles(prev_role)
        
        # Remove old role
        await user.remove_roles(current_role)
        
        # Remove staff role when demoting from Mod to Member
        if current_role == mod_role and prev_role == member_role and staff_role:
            await user.remove_roles(staff_role)
        
        await interaction.response.send_message(
            f"{user.display_name} has been demoted to {prev_role.name}.", 
            ephemeral=True
        )
        await log_to_channel(
            self.bot, 
            f"📉 **{interaction.user}** demoted **{user.display_name}** to **{prev_role.name}**."
        )

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))