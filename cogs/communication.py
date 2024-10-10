# cogs/communication.py

import discord
from discord.ext import commands, tasks
import config
from datetime import datetime, timedelta

class Communication(commands.Cog):
    """Cog for managing communications, reminders, and notifications."""

    def __init__(self, bot):
        self.bot = bot
        self.reminder_tasks = {}  # {channel_id: task}
        self.broadcast_channel_id = config.BROADCAST_CHANNEL_ID  # Channel ID for broadcasting messages

    @commands.command(name='send_reminder')
    @commands.has_permissions(manage_guild=True)
    async def send_reminder(self, ctx, member: discord.Member, *, message):
        """
        Admin command to send a reminder to a member.
        Usage: !send_reminder @member Your reminder message here
        """
        try:
            await member.send(f"⏰ Reminder from {ctx.guild.name}: {message}")
            await ctx.send(f"✅ Reminder sent to {member.display_name}.")
        except discord.Forbidden:
            await ctx.send(f"❌ Unable to send a reminder to {member.display_name}. They may have DMs disabled.")

    @commands.command(name='schedule_broadcast')
    @commands.has_permissions(manage_guild=True)
    async def schedule_broadcast(self, ctx, time: str, *, message):
        """
        Admin command to schedule a broadcast message.
        Usage: !schedule_broadcast YYYY-MM-DD HH:MM Message
        """
        try:
            broadcast_time = datetime.strptime(time, "%Y-%m-%d %H:%M")
            now = datetime.now()
            delay = (broadcast_time - now).total_seconds()
            if delay <= 0:
                await ctx.send("⚠️ The scheduled time must be in the future.")
                return

            self.bot.loop.create_task(self._broadcast_message(delay, message))
            await ctx.send(f"✅ Broadcast scheduled for {broadcast_time.strftime('%Y-%m-%d %H:%M')}.")
        except ValueError:
            await ctx.send("⚠️ Please provide the time in the format: YYYY-MM-DD HH:MM")

    async def _broadcast_message(self, delay, message):
        await asyncio.sleep(delay)
        channel = self.bot.get_channel(self.broadcast_channel_id)
        if channel:
            await channel.send(message)
        else:
            print("Broadcast channel not found.")

    @commands.command(name='send_dm')
    @commands.has_permissions(manage_guild=True)
    async def send_dm(self, ctx, member: discord.Member, *, message):
        """
        Admin command to send a direct message to a member.
        Usage: !send_dm @member Your message here
        """
        try:
            await member.send(message)
            await ctx.send(f"✅ DM sent to {member.display_name}.")
        except discord.Forbidden:
            await ctx.send(f"❌ Unable to send a DM to {member.display_name}. They may have DMs disabled.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """
        Event listener for when a member joins the server.
        Sends a welcome message via DM.
        """
        try:
            await member.send(f"Welcome to {member.guild.name}! Feel free to reach out if you have any questions.")
        except discord.Forbidden:
            pass  # Member has DMs disabled

async def setup(bot):
    await bot.add_cog(Communication(bot))
