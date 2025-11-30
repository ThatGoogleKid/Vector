import discord
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cogs.tickets import TicketCog

class TicketButtons(discord.ui.View):
    """Control buttons shown in each ticket"""

    def __init__(self, ticket_cog: 'TicketCog'):
        super().__init__(timeout=None)
        self.ticket_cog = ticket_cog

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, custom_id="ticket_close")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Permission check
        allowed_roles = ["manager", "admin", "sr_admin", "owner", "sr_mod", "mod"]
        if not self.ticket_cog.bot.config.has_role(interaction.user.roles, allowed_roles):
            return await interaction.response.send_message(
                "You do not have permission to close this ticket.",
                ephemeral=True
            )
        
        countdown_view = TicketCloseView()

        await interaction.response.send_message(
            content="⚠️ **Ticket Closure Initiated!** Closing in 10 seconds...",
            view=countdown_view,
            ephemeral=False
        )

        for sec in range (9, 0, -1):
            if countdown_view.cancelled:
                return
            
            await interaction.edit_original_response(content=f"Closing in {sec}...")
            await asyncio.sleep(1)

        if countdown_view.cancelled:
            return
        
        await interaction.edit_original_response(content="Archiving ticket now...", view=None)

        # Archive the ticket
        await self.ticket_cog.archive_ticket(interaction.channel, interaction.user)
        await interaction.followup.send("Ticket successfully archived.", ephemeral=True)

class TicketCloseView(discord.ui.View):
    """View for cancelling ticket closure during countdown"""

    def __init__(self):
        super().__init__(timeout=60)
        self.cancelled = False

    @discord.ui.button(label="❌ Cancel Close", style=discord.ButtonStyle.grey, custom_id="ticket_cancel_close")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.cancelled = True
        
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        
        await interaction.response.edit_message(
            content="**Ticket closing CANCELLED.** You can close it again later.", 
            view=self
        )
        self.stop()