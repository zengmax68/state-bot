import discord
from discord import app_commands
import config
import time
import traceback

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.start_time = time.time()

    async def setup_hook(self):
        guild = discord.Object(id=config.GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        guild = self.get_guild(config.GUILD_ID)
        if guild:
            log_channel = discord.utils.get(guild.text_channels, name="moderator-only")
            if log_channel:
                embed = discord.Embed(
                    title="Bot Online",
                    description=f"Logged in as {self.user} (ID: {self.user.id})",
                    color=discord.Color.green()
                )
                await safe_send(log_channel, embed=embed)

    async def on_error(self, event_method, *args, **kwargs):
        tb = traceback.format_exc()
        guild = self.get_guild(config.GUILD_ID)
        if guild:
            log_channel = discord.utils.get(guild.text_channels, name="moderator-only")
            if log_channel:
                embed = discord.Embed(
                    title="Bot Error",
                    description=f"Error in `{event_method}`",
                    color=discord.Color.red()
                )
                embed.add_field(name="Traceback", value=f"```{tb}```", inline=False)
                await safe_send(log_channel, embed=embed)
        else:
            print("Error occurred but target guild not found")
            print(tb)

    async def on_guild_join(self, guild):
        if guild.id != config.GUILD_ID:
            await guild.leave()

client = MyBot()

async def safe_send(channel: discord.abc.Messageable, **kwargs):
    """
    Try to send to a channel. If the bot lacks permissions or sending fails,
    print the error to console instead of raising.
    """
    try:
        return await channel.send(**kwargs)
    except discord.Forbidden:
        print(f"Missing permissions to send to channel: {getattr(channel, 'name', channel)}")
    except discord.HTTPException as e:
        print(f"HTTP error when sending to channel {getattr(channel, 'name', channel)}: {e}")
    except Exception as e:
        print(f"Unexpected error when sending to channel {getattr(channel, 'name', channel)}: {e}")

async def log_command(interaction: discord.Interaction):
    if interaction.user.id == config.OWNER_ID:
        return
    guild = interaction.guild
    if not guild:
        return
    log_channel = discord.utils.get(guild.text_channels, name="moderator-only")
    if not log_channel:
        return
    command_name = getattr(interaction.command, "name", str(interaction.data.get("name")) if getattr(interaction, "data", None) else "unknown")
    embed = discord.Embed(title="Command Used", color=discord.Color.blue())
    embed.add_field(name="Command", value=command_name, inline=True)
    embed.add_field(name="User", value=f"{interaction.user} (ID: {interaction.user.id})", inline=False)
    channel_info = f"{interaction.channel} (ID: {getattr(interaction.channel, 'id', 'unknown')})"
    embed.add_field(name="Channel", value=channel_info, inline=False)
    embed.add_field(name="Time", value=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), inline=False)
    await safe_send(log_channel, embed=embed)

@client.tree.command(name="send", description="Send a message to a channel")
async def send(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    try:
        await safe_send(channel, content=message)
        await interaction.response.send_message(f"Message sent to {channel.mention}", ephemeral=True)
        await log_command(interaction)
    except discord.Forbidden:
        await interaction.response.send_message("Bot lacks permission to send messages to that channel.", ephemeral=True)
        await log_command(interaction)
    except Exception as e:
        await interaction.response.send_message(f"Failed to send message: {e}", ephemeral=True)
        await log_command(interaction)

@client.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    latency_ms = round(client.latency * 1000)
    await interaction.response.send_message(f"Latency: {latency_ms} ms", ephemeral=True)
    await log_command(interaction)

@client.tree.command(name="userinfo", description="Get information about a user")
async def userinfo(interaction: discord.Interaction, user: discord.User):
    embed = discord.Embed(title="User Information", color=discord.Color.blue())
    embed.add_field(name="Username", value=user.name, inline=True)
    embed.add_field(name="Discriminator", value=user.discriminator, inline=True)
    embed.add_field(name="ID", value=user.id, inline=False)
    embed.set_thumbnail(url=user.display_avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await log_command(interaction)

@client.tree.command(name="serverinfo", description="Get information about this server")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title="Server Information", color=discord.Color.green())
    embed.add_field(name="Name", value=guild.name, inline=True)
    embed.add_field(name="ID", value=guild.id, inline=True)
    embed.add_field(name="Member Count", value=guild.member_count, inline=True)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await log_command(interaction)

@client.tree.command(name="clear", description="Delete a number of messages from a channel")
async def clear(interaction: discord.Interaction, channel: discord.TextChannel, limit: int):
    try:
        deleted = await channel.purge(limit=limit)
        await interaction.response.send_message(f"Deleted {len(deleted)} messages from {channel.mention}", ephemeral=True)
        await log_command(interaction)
    except discord.Forbidden:
        await interaction.response.send_message("Bot lacks permission to manage messages in that channel.", ephemeral=True)
        await log_command(interaction)
    except Exception as e:
        await interaction.response.send_message(f"Failed to clear messages: {e}", ephemeral=True)
        await log_command(interaction)

@client.tree.command(name="purgeall", description="Delete ALL messages from a channel")
async def purgeall(interaction: discord.Interaction, channel: discord.TextChannel):
    try:
        # Attempt a bulk purge; wrap in try/except because large purges can fail
        deleted = await channel.purge(limit=None)
        await interaction.response.send_message(f"Purged {len(deleted)} messages from {channel.mention}", ephemeral=True)
        await log_command(interaction)
    except discord.Forbidden:
        await interaction.response.send_message("Bot lacks permission to manage messages in that channel.", ephemeral=True)
        await log_command(interaction)
    except TypeError:
        # Some discord.py versions may not accept limit=None; try a large limit fallback
        try:
            deleted = await channel.purge(limit=100000)
            await interaction.response.send_message(f"Purged {len(deleted)} messages from {channel.mention}", ephemeral=True)
            await log_command(interaction)
        except Exception as e:
            await interaction.response.send_message(f"Failed to purge: {e}", ephemeral=True)
            await log_command(interaction)
    except Exception as e:
        await interaction.response.send_message(f"Failed to purge: {e}", ephemeral=True)
        await log_command(interaction)

@client.tree.command(name="roles", description="List all roles in the server")
async def roles(interaction: discord.Interaction):
    role_names = [role.name for role in interaction.guild.roles if role.name != "@everyone"]
    await interaction.response.send_message("Roles:\n" + "\n".join(role_names), ephemeral=True)
    await log_command(interaction)

@client.tree.command(name="uptime", description="Show how long the bot has been running")
async def uptime(interaction: discord.Interaction):
    uptime_seconds = round(time.time() - client.start_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    await interaction.response.send_message(f"Uptime: {hours}h {minutes}m {seconds}s", ephemeral=True)
    await log_command(interaction)

@client.tree.command(name="channels", description="List all text channels in the server")
async def channels(interaction: discord.Interaction):
    text_channels = [ch.name for ch in interaction.guild.text_channels]
    await interaction.response.send_message("Channels:\n" + "\n".join(text_channels), ephemeral=True)
    await log_command(interaction)

client.run(config.TOKEN)
