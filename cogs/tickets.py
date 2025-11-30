import discord
from discord.ext import commands
from discord import app_commands
from utils.data_manager import DataManager
from utils.logger import log_to_channel
from views.ticket_panel import TicketPanel
from views.ticket_controls import TicketButtons

class TicketCog(commands.Cog):
    """Handles all ticket-related functionality"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data = DataManager()
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Send ticket panel when bot is ready"""
        # Register persistent views so they work after restarts
        self.bot.add_view(TicketPanel(self))
        self.bot.add_view(TicketButtons(self))
        
        panel_channel = self.bot.get_channel(self.bot.config.get_channel_id("ticket_panel"))
        if panel_channel:
            await panel_channel.purge()
            embed = discord.Embed(
                title="🎫 Vilyx Tickets",
                description="Select a category below to open a ticket:",
                color=0x00AAEE
            )
            view = TicketPanel(self)
            await panel_channel.send(embed=embed, view=view)
    
    async def create_ticket(self, interaction: discord.Interaction, category: str):
        """Create a new ticket channel"""
        guild = interaction.guild
        
        # Determine category and sensitivity
        general_categories = ["General Support", "Bug Report", "Player Report", "Media Applications"]
        staff_categories = ["Report a Staff Member", "Store Issues", "Appeals", "Staff Applications"]
        
        is_sensitive = category in staff_categories
        
        # Get parent category and validate it
        parent_category = None
        if category in general_categories:
            category_id = self.bot.config.ticket_categories.get("general_tickets")
            if category_id:
                parent_category = guild.get_channel(category_id)
        elif category in staff_categories:
            category_id = self.bot.config.ticket_categories.get("staff_store_tickets")
            if category_id:
                parent_category = guild.get_channel(category_id)
        
        # Validate that it's actually a category
        if parent_category and not isinstance(parent_category, discord.CategoryChannel):
            await interaction.response.send_message(
                f"❌ Configuration error: The ticket category is not a valid category channel. Please contact an administrator.",
                ephemeral=True
            )
            return
        
        # Setup permissions
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        
        # Add role access based on ticket type
        if not is_sensitive:
            # General tickets - staff role can see
            staff_role = guild.get_role(self.bot.config.get_role_id("staff"))
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        else:
            # Staff/Store tickets - only Sr Admin+ can see
            for role_key in ["admin", "sr_admin", "manager", "owner"]:
                role = guild.get_role(self.bot.config.get_role_id(role_key))
                if role:
                    overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        
        # Create channel
        channel_name = interaction.user.name.lower()
        channel = await guild.create_text_channel(
            channel_name,
            overwrites=overwrites,
            topic=f"Ticket by {interaction.user.id}",
            category=parent_category
        )
        
        # Save ticket data
        self.data.create_ticket(str(channel.id), interaction.user.id, category)
        
        # Log ticket creation
        await log_to_channel(self.bot, f"🎟️ {interaction.user} opened a {category} ticket.")
        
        # Send ticket message
        embed = discord.Embed(
            title=f"{category} Ticket",
            description=f"{interaction.user.mention}, please explain your issue below.\nA staff member will assist you shortly.",
            color=0x00AAEE
        )
        view = TicketButtons(self)
        
        mention_content = f"{interaction.user.mention}"
        if not is_sensitive and guild.get_role(self.bot.config.get_role_id("staff")):
            staff_role = guild.get_role(self.bot.config.get_role_id("staff"))
            mention_content = f"{staff_role.mention} | {interaction.user.mention}"
        
        await channel.send(content=mention_content, embed=embed, view=view)
        await interaction.response.send_message("Ticket created.", ephemeral=True)
    
    async def archive_ticket(self, channel: discord.TextChannel, user: discord.Member):
        """Archive a ticket channel"""
        guild = channel.guild
        archive_category = guild.get_channel(self.bot.config.ticket_categories["archived"])
        
        await log_to_channel(self.bot, f"📦 Ticket {channel.name} archived by {user}.")
        
        await channel.edit(
            category=archive_category,
            name=f"archived-{channel.name}",
            sync_permissions=True
        )
        
        self.data.update_ticket(str(channel.id), archived=True)
    
    @app_commands.command(name="deleteticket", description="Delete an archived ticket")
    @app_commands.guild_only()
    async def deleteticket(self, interaction: discord.Interaction):
        """Delete an archived ticket (Sr Admin+ only)"""
        allowed_roles = ["sr_admin", "manager", "owner"]
        
        if not self.bot.config.has_role(interaction.user.roles, allowed_roles):
            return await interaction.response.send_message("No permission.", ephemeral=True)
        
        # Check if ticket is archived
        if not self.data.is_archived(str(interaction.channel.id)):
            return await interaction.response.send_message(
                "This ticket is not archived.", 
                ephemeral=True
            )
        
        await log_to_channel(
            self.bot, 
            f"❌ Archived ticket deleted: {interaction.channel.name} by {interaction.user}"
        )
        
        self.data.delete_ticket(str(interaction.channel.id))
        await interaction.channel.delete()

async def setup(bot):
    await bot.add_cog(TicketCog(bot))