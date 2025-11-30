import discord
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cogs.tickets import TicketCog

class TicketPanel(discord.ui.View):
    """Main ticket panel with all ticket type buttons"""

    def __init__(self, ticket_cog: 'TicketCog'):
        super().__init__(timeout=None)
        self.ticket_cog = ticket_cog
        
    # General Tickets   
    @discord.ui.button(label="🎫 General Support", style=discord.ButtonStyle.green, custom_id="ticket_general")
    async def general_support(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.ticket_cog.create_ticket(interaction, "General Support")
    
    @discord.ui.button(label="🐛 Bug Report", style=discord.ButtonStyle.green, custom_id="ticket_bug")
    async def bug_report(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.ticket_cog.create_ticket(interaction, "Bug Report")
    
    @discord.ui.button(label="🔪 Player Report", style=discord.ButtonStyle.green, custom_id="ticket_player")
    async def player_report(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.ticket_cog.create_ticket(interaction, "Player Report")
    
    @discord.ui.button(label="🎥 Media Applications", style=discord.ButtonStyle.green, custom_id="ticket_media")
    async def media_app(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.ticket_cog.create_ticket(interaction, "Media Applications")

    # Staff / Store Tickets
    @discord.ui.button(label="👮‍♂️ Staff Applications", style=discord.ButtonStyle.red, custom_id="ticket_staff")
    async def staff_app(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.ticket_cog.create_ticket(interaction, "Staff Applications")
    
    @discord.ui.button(label="🔨 Appeal a Punishment", style=discord.ButtonStyle.red, custom_id="ticket_appeal")
    async def appeal_punishment(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.ticket_cog.create_ticket(interaction, "Appeals")
    
    @discord.ui.button(label="❗ Report a Staff Member", style=discord.ButtonStyle.red, custom_id="ticket_staff_report")
    async def staff_report(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.ticket_cog.create_ticket(interaction, "Report a Staff Member")
    
    @discord.ui.button(label="🛒 Store Issues", style=discord.ButtonStyle.red, custom_id="ticket_store")
    async def store_issue(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.ticket_cog.create_ticket(interaction, "Store Issues")