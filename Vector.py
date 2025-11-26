import discord, json, os, asyncio
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

# Load config
with open("config.json") as f:
    config = json.load(f)

GUILD_ID = config["public_guild_id"]
GUILD = discord.Object(id=GUILD_ID)
TOKEN = config["token"]
status_text = config.get("status", "Watching Vilyx Network")
data_file = "data.json"

# Define the hierarchy in order from lowest to highest
ROLE_HIERARCHY = [
    config["public_roles"]["member"],        # Member
    config["public_roles"]["mod"],        # Mod
    config["public_roles"]["sr_mod"],     # Sr Mod
    config["public_roles"]["admin"],      # Admin
    config["public_roles"]["sr_admin"],   # Sr Admin
    config["public_roles"]["manager"],    # Manager
    config["public_roles"]["owner"],      # Owner
]

# Load persistent ticket data
if not os.path.exists(data_file):
    with open(data_file, "w") as f: json.dump({}, f)
with open(data_file) as f:
    ticket_data = json.load(f)

def save_data():
    with open(data_file, "w") as f:
        json.dump(ticket_data, f, indent=2)

bot = commands.Bot(command_prefix="!", intents=intents)

async def log(msg):
    ch = bot.get_channel(config["channels"]["logs"])
    if ch: await ch.send(msg)

class TicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # General Tickets
    @discord.ui.button(label="🎫 General Support", style=discord.ButtonStyle.green)
    async def general_support(self, i, b): await create_ticket(i, "General Support")
    @discord.ui.button(label="🐛 Bug Report", style=discord.ButtonStyle.green)
    async def bug_report(self, i, b): await create_ticket(i, "Bug Report")
    @discord.ui.button(label="🔪 Player Report", style=discord.ButtonStyle.green)
    async def player_report(self, i, b): await create_ticket(i, "Player Report")
    @discord.ui.button(label="👮‍♂️ Staff Applications", style=discord.ButtonStyle.green)
    async def staff_app(self, i, b): await create_ticket(i, "Staff Applications")
    @discord.ui.button(label="🎥 Media Applications", style=discord.ButtonStyle.green)
    async def media_app(self, i, b): await create_ticket(i, "Media Applications")

    # Staff / Store Tickets
    @discord.ui.button(label="🔨 Appeal a Punishment", style=discord.ButtonStyle.red)
    async def appeal_punishment(self, i, b): await create_ticket(i, "Appeals") 
    
    @discord.ui.button(label="❗ Report a Staff Member", style=discord.ButtonStyle.red)
    async def staff_report(self, i, b): await create_ticket(i, "Report a Staff Member")
    @discord.ui.button(label="🛒 Store Issues", style=discord.ButtonStyle.red)
    async def store_issue(self, i, b): await create_ticket(i, "Store Issues")

async def create_ticket(interaction, category):
    guild = interaction.guild

    # Category IDs
    GENERAL_CATEGORY_ID = config["ticket_categories"]["general_tickets"] 
    STAFF_CATEGORY_ID = config["ticket_categories"]["staff_store_tickets"] 

    # 1. Determine which category to place the ticket in AND its sensitivity
    is_sensitive = False
    if category in ["General Support", "Bug Report", "Player Report", "Staff Applications", "Media Applications"]:
        parent_category = guild.get_channel(GENERAL_CATEGORY_ID)
    elif category in ["Report a Staff Member", "Store Issues", "Appeals"]:
        parent_category = guild.get_channel(STAFF_CATEGORY_ID)
        is_sensitive = True
    else:
        parent_category = None  # fallback to guild root if needed

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
    }

    # 2. Add roles based on ticket type

    # Add generic 'staff' role access for ALL General Tickets
    staff_role = guild.get_role(config["public_roles"]["staff"])
    if not is_sensitive and staff_role:
        overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
    
    # 3. Restricted/High-level tickets: Layer on specific permissions
    
    # Bug Reports and General tickets still get high-level roles layered on top
    if category == "Bug Report":
        # Only Developers, Managers, and Owners can see Bug Reports
        for role_key in ["developer","manager","owner"]:
            role = guild.get_role(config["public_roles"].get(role_key))
            if role: overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
            
    # Staff/Store Tickets: Only Sr Admin+ can see these (Crucial for restriction)
    elif category in ["Report a Staff Member","Store Issues", "Appeals"]:
        for role_key in ["sr_admin","manager","owner"]:
            role = guild.get_role(config["public_roles"].get(role_key))
            if role: overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    # 4. Create ticket channel
    ch_name = interaction.user.name.lower()
    ch = await guild.create_text_channel(ch_name, overwrites=overwrites, topic=f"Ticket by {interaction.user.id}", category=parent_category)

    ticket_data[str(ch.id)] = {"user": interaction.user.id, "category": category, "claimed": False}
    save_data()
    await log(f"🎟️ {interaction.user} opened a {category} ticket.")

    embed = discord.Embed(
        title=f"{category} Ticket",
        description=f"{interaction.user.mention}, please explain your issue below.\nA staff member will assist you shortly.",
        color=0x00AAEE
    )
    view = TicketButtons()
    

    mention_content = f"{staff_role.mention} | {interaction.user.mention}"
        
    await ch.send(content=mention_content, embed=embed, view=view)
    await interaction.response.send_message("Ticket created.", ephemeral=True)

class TicketCloseView(discord.ui.View):
    def __init__(self):
        # Set a timeout just to prevent the view from lingering too long if not used
        super().__init__(timeout=60) 
        self.cancelled = False

    @discord.ui.button(label="❌ Cancel Close", style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 1. Set the flag to true to stop the countdown loop
        self.cancelled = True
        
        # 2. Disable the button and update the message
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        
        await interaction.response.edit_message(content="**Ticket closing CANCELLED.** You can close it again later.", view=self)
        self.stop() # Stop the view to clean up resources

class TicketButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Roles allowed to close (Permission check for INITIATING closure)
        allowed_roles = ["manager", "admin", "sr_admin", "owner", "sr_mod", "mod"]
        user_roles = [r.id for r in interaction.user.roles]
        allowed = False
        for role_key in allowed_roles:
            role_id = config["public_roles"].get(role_key)
            if role_id in user_roles:
                allowed = True
                break
        if not allowed:
            return await interaction.response.send_message("You do not have permission to close this ticket.", ephemeral=True)

        # 1. Instantiate the new countdown view
        countdown_view = TicketCloseView()
        
        # 2. FIX: Send a new public message (not ephemeral) to start the countdown
        # This message will contain the cancel button.
        await interaction.response.send_message(
            content="⚠️ **Ticket Closure Initiated!** Closing in 10 seconds...",
            view=countdown_view,
            ephemeral=False # Set to False to make it a regular channel message
        )

        # 3. 10 second countdown
        for sec in range(9, 0, -1): # Start at 9 since 10 was used in the initial message
            if countdown_view.cancelled:
                # If cancelled by the button, the TicketCloseView handles the message edit, so we just exit.
                return 
                
            # Use edit_original_response to update the NEW message (the countdown message)
            await interaction.edit_original_response(content=f"Closing in {sec}...")
            await asyncio.sleep(1)

        # Check cancellation one last time after the loop finishes
        if countdown_view.cancelled:
            return
            
        # Final message update before archiving
        await interaction.edit_original_response(content="Archiving ticket now...", view=None)

        # 4. Handle Archive logic
        await archive_ticket(interaction.channel, interaction.user)
        # Use a follow-up to confirm the action, visible only to the staff member
        await interaction.followup.send("Ticket successfully archived.", ephemeral=True)



async def archive_ticket(channel, user):
    guild = channel.guild
    archive_category = guild.get_channel(config["ticket_categories"]["archived"])

    await log(f"📦 Ticket {channel.name} archived by {user}.")
    
    # FIX: Set sync_permissions=True to inherit permissions from the category
    await channel.edit(
        category=archive_category, 
        name=f"archived-{channel.name}",
        sync_permissions=True # <-- This is the key
    )
    
    if str(channel.id) in ticket_data:
        ticket_data[str(channel.id)]["archived"] = True
        save_data()


async def close_ticket(channel, user):
    await log(f"🗑️ Ticket {channel.name} closed by {user}.")
    ticket_data.pop(str(channel.id), None)
    save_data()
    await channel.delete()

# Commands

@bot.tree.command(name="deleteticket", guild=GUILD)
async def deleteticket(i: discord.Interaction):

    # Sr Admin+ only
    allowed_roles = [
        config["public_roles"]["sr_admin"],
        config["public_roles"]["manager"],
        config["public_roles"]["owner"]
    ]

    if not any(i.guild.get_role(rid) in i.user.roles for rid in allowed_roles):
        return await i.response.send_message("No permission.", ephemeral=True)

    # Must be archived
    t = ticket_data.get(str(i.channel.id))
    if not t or not t.get("archived"):
        return await i.response.send_message("This ticket is not archived.", ephemeral=True)

    await log(f"❌ Archived ticket deleted: {i.channel.name} by {i.user}")
    ticket_data.pop(str(i.channel.id))
    save_data()

    await i.channel.delete()


@bot.tree.command(name="ip", guild=GUILD)
async def ip(i: discord.Interaction):
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
    await i.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="sendip", description="Sends the server IP.", guild=GUILD)
async def sendip(i: discord.Interaction):
    allowed_roles = [
        config["public_roles"]["mod"],
        config["public_roles"]["sr_mod"],
        config["public_roles"]["admin"],
        config["public_roles"]["sr_admin"],
        config["public_roles"]["manager"],
        config["public_roles"]["developer"],
        config["public_roles"]["owner"]
    ]

    # Check if the user has at least one of the allowed roles
    if not any(i.guild.get_role(rid) in i.user.roles for rid in allowed_roles):
        return await i.response.send_message("You do not have permission to use this command.", ephemeral=True)

    # Create the embed
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

    # Send it publicly (non-ephemeral)
    await i.response.send_message(embed=embed, ephemeral=False)


# Promote / Demote syncing roles
async def sync_roles(user, rank):
    public_guild = bot.get_guild(config["public_guild_id"])
    
    # Remove old roles
    for r in config["public_roles"].values():
        if r and r != 0:  # <-- skip invalid roles
            role = public_guild.get_role(r)
            if role:
                await user.remove_roles(role)
    
    # Add new roles
    new_pub_role = public_guild.get_role(config["public_roles"].get(rank.lower()))
    if new_pub_role: await user.add_roles(new_pub_role)



@bot.tree.command(name="promote", guild=GUILD)
async def promote(i: discord.Interaction, user: discord.Member):
    # Check if user has Manager+ permission
    allowed_roles = [
        config["public_roles"]["manager"],
        config["public_roles"]["owner"]
    ]
    if not any(i.guild.get_role(rid) in i.user.roles for rid in allowed_roles):
        return await i.response.send_message("You do not have permission to use this command.", ephemeral=True)

    guild_roles = [i.guild.get_role(rid) for rid in ROLE_HIERARCHY]

    # Get the highest role the user currently has in the hierarchy
    current_index = -1
    for idx, role in enumerate(guild_roles):
        if role in user.roles:
            current_index = idx

    # If already at the top, cannot promote
    if current_index >= len(guild_roles) - 1:
        return await i.response.send_message(f"{user.display_name} is already at the highest rank.", ephemeral=True)

    # Promote to next role
    next_role = guild_roles[current_index + 1]
    await user.add_roles(next_role)

    # Role references
    member_role = i.guild.get_role(config["public_roles"]["member"])
    mod_role = i.guild.get_role(config["public_roles"]["mod"])
    staff_role = i.guild.get_role(config["public_roles"]["staff"])  # staff role in same guild

    # Remove previous role if applicable — except when going from Member -> Mod
    if current_index >= 0:
        current_role = guild_roles[current_index]
        if not (current_role == member_role and next_role == mod_role):
            await user.remove_roles(current_role)

    # If promoted from Member -> Mod, give Staff role
    if member_role in user.roles and next_role == mod_role and staff_role:
        await user.add_roles(staff_role)

    await i.response.send_message(f"{user.display_name} has been promoted to {next_role.name}.", ephemeral=True)
    await log(f"📈 **{i.user}** promoted **{user.display_name}** to **{next_role.name}**.")


@bot.tree.command(name="demote", guild=GUILD)
async def demote(i: discord.Interaction, user: discord.Member):
    # Check if user has Manager+ permission
    allowed_roles = [
        config["public_roles"]["manager"],
        config["public_roles"]["owner"]
    ]
    if not any(i.guild.get_role(rid) in i.user.roles for rid in allowed_roles):
        return await i.response.send_message("You do not have permission to use this command.", ephemeral=True)

    guild_roles = [i.guild.get_role(rid) for rid in ROLE_HIERARCHY]

    # Get the highest role the user currently has in the hierarchy
    current_index = -1
    for idx, role in enumerate(guild_roles):
        if role in user.roles:
            current_index = idx

    # If already at the lowest, cannot demote
    if current_index <= 0:
        return await i.response.send_message(f"{user.display_name} is already at the lowest rank.", ephemeral=True)

    # Demote to previous role
    prev_role = guild_roles[current_index - 1]
    await user.add_roles(prev_role)

    # Role references
    member_role = i.guild.get_role(config["public_roles"]["member"])
    mod_role = i.guild.get_role(config["public_roles"]["mod"])
    staff_role = i.guild.get_role(config["public_roles"]["staff"])

    # Remove old role
    current_role = guild_roles[current_index]
    await user.remove_roles(current_role)

    # If demoted from Mod -> Member, remove Staff role
    if current_role == mod_role and prev_role == member_role and staff_role:
        await user.remove_roles(staff_role)

    await i.response.send_message(f"{user.display_name} has been demoted to {prev_role.name}.", ephemeral=True)
    await log(f"📉 **{i.user}** demoted **{user.display_name}** to **{prev_role.name}**.")

@bot.event
async def on_ready():
    GUILD_ID = config["public_guild_id"]  # Guild to sync slash commands to
    guild = discord.Object(id=GUILD_ID)

    try:
        synced = await bot.tree.sync(guild=guild)
        print(f"✅ Synced {len(synced)} slash commands to guild {GUILD_ID}")
    except Exception as e:
        print(f"⚠️ Failed to sync commands to guild {GUILD_ID}: {e}")

    await bot.change_presence(
        status=discord.Status.dnd,
        activity=discord.Activity(type=discord.ActivityType.watching, name=status_text)
    )

    # Send ticket panel
    panel_ch = bot.get_channel(config["channels"]["ticket_panel"])
    if panel_ch:
        await panel_ch.purge()
        embed = discord.Embed(
            title="🎫 Vilyx Tickets",
            description="Select a category below to open a ticket:",
            color=0x00AAEE
        )
        view = TicketPanel()
        await panel_ch.send(embed=embed, view=view)

    print(f"Bot online as {bot.user}")

bot.run(TOKEN)
