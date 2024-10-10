# cogs/feedback.py

import discord
from discord.ext import commands
import config
from datetime import datetime

class Feedback(commands.Cog):
    """Cog for handling feedback, reviews, and dispute resolutions."""

    def __init__(self, bot):
        self.bot = bot
        self.reviews_channel_id = config.REVIEWS_CHANNEL_ID  # Channel ID for #reviews channel

    @commands.command(name='leave_review')
    async def leave_review(self, ctx, rating: int, *, comment=None):
        """
        Command for students to leave a review.
        Usage: !leave_review rating [comment]
        """
        if ctx.channel.name.startswith('assignment-'):
            assignment_id = ctx.channel.name.replace('assignment-', '')
            student = ctx.author

            if rating < 1 or rating > 5:
                await ctx.send("⚠️ Please provide a rating between 1 and 5.")
                return

            reviews_channel = self.bot.get_channel(self.reviews_channel_id)
            if reviews_channel:
                embed = discord.Embed(title="New Review", color=discord.Color.blue())
                embed.add_field(name="Assignment ID", value=assignment_id, inline=False)
                embed.add_field(name="Student", value=student.display_name, inline=False)
                embed.add_field(name="Rating", value=f"{rating}/5", inline=False)
                if comment:
                    embed.add_field(name="Comment", value=comment, inline=False)
                embed.timestamp = datetime.utcnow()

                await reviews_channel.send(embed=embed)
                await ctx.send("✅ Thank you for your review!")
            else:
                await ctx.send("⚠️ Reviews channel not found.")
        else:
            await ctx.send("⚠️ This command can only be used in your assignment channel.")

    @commands.command(name='initiate_dispute')
    async def initiate_dispute(self, ctx, *, reason):
        """
        Command for students to initiate a dispute.
        Usage: !initiate_dispute Reason for the dispute
        """
        if ctx.channel.name.startswith('assignment-'):
            assignment_id = ctx.channel.name.replace('assignment-', '')
            student = ctx.author

            # Notify admins of the dispute
            for admin_id in config.ADMIN_IDS:
                admin_user = self.bot.get_user(admin_id)
                if admin_user:
                    await admin_user.send(
                        f"⚠️ Dispute initiated by {student.display_name} for Assignment {assignment_id}.\n"
                        f"Reason: {reason}\n"
                        f"Channel: {ctx.channel.mention}"
                    )

            await ctx.send("⚠️ Your dispute has been recorded. An admin will review it shortly.")
        else:
            await ctx.send("⚠️ This command can only be used in your assignment channel.")

    @commands.command(name='resolve_dispute')
    @commands.has_permissions(manage_guild=True)
    async def resolve_dispute(self, ctx, *, resolution):
        """
        Admin command to resolve a dispute.
        Usage: !resolve_dispute Resolution details
        """
        if ctx.channel.name.startswith('assignment-'):
            assignment_id = ctx.channel.name.replace('assignment-', '')
            assignment_cog = self.bot.get_cog('AssignmentManagement')
            assignment = assignment_cog.assignments.get(ctx.channel.id)
            if not assignment:
                await ctx.send("⚠️ Assignment data not found.")
                return

            student = assignment['student']

            # Notify the student of the resolution
            try:
                await student.send(
                    f"Hello {student.display_name},\n"
                    f"Your dispute for Assignment {assignment_id} has been reviewed.\n"
                    f"Resolution: {resolution}"
                )
            except discord.Forbidden:
                await ctx.send(f"⚠️ Unable to send DM to {student.display_name}.")

            await ctx.send("✅ Dispute has been resolved and the student has been notified.")
        else:
            await ctx.send("⚠️ This command can only be used in an assignment channel.")

async def setup(bot):
    await bot.add_cog(Feedback(bot))