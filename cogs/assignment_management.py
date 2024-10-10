# cogs/assignment_management.py

import discord
from discord.ext import commands, tasks
import asyncio
import uuid
from datetime import datetime, timedelta
from .utilities import generate_unique_id, format_message, validate_input
import config

class AssignmentManagement(commands.Cog):
    """Cog for handling assignment submission, delivery, and revision management."""

    def __init__(self, bot):
        self.bot = bot
        self.assignments = {}  # Stores assignment data
        self.deadline_reminder.start()  # Start the deadline reminder task

    def cog_unload(self):
        self.deadline_reminder.cancel()

    @commands.command(name='upload_assignment')
    async def upload_assignment(self, ctx):
        """
        Command for students to initiate an assignment submission.
        Usage: !upload_assignment
        """

        # Check if the command is used in the designated channel
        if ctx.channel.id != config.UPLOAD_ASSIGNMENT_CHANNEL_ID:
            await ctx.send(f"Please use this command in the <#{config.UPLOAD_ASSIGNMENT_CHANNEL_ID}> channel.")
            return

        student = ctx.author
        guild = ctx.guild

        # Generate a unique assignment ID
        assignment_id = generate_unique_id()

        # Create a private channel for the assignment
        channel_name = f"assignment-{assignment_id}"

        # Set permissions for the private channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            student: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        # Add admin permissions
        for admin_id in config.ADMIN_IDS:
            admin_member = guild.get_member(admin_id)
            if admin_member:
                overwrites[admin_member] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        # Create the 'Assignments' category if it doesn't exist
        category_name = "Assignments"
        category = discord.utils.get(guild.categories, name=category_name)
        if category is None:
            category = await guild.create_category(category_name)

        # Create the private assignment channel
        assignment_channel = await guild.create_text_channel(
            name=channel_name,
            overwrites=overwrites,
            category=category
        )

        # Notify the student
        await ctx.send(
            f"✅ A private channel has been created for your assignment: {assignment_channel.mention}"
        )

        # Send initial messages in the private channel
        await assignment_channel.send(
            f"{student.mention}, welcome to your private assignment channel.\n"
            "Please upload your assignment details and any relevant files here."
        )

        # Store assignment data
        self.assignments[assignment_channel.id] = {
            'assignment_id': assignment_id,
            'student': student,
            'channel': assignment_channel,
            'reviewed': False,
            'doable': None,
            'deadline': None,
            'status': 'Pending Review',
            'last_reminder': None,
            'revisions': []
        }

        # Send a reminder to admin to review the assignment
        for admin_id in config.ADMIN_IDS:
            admin_user = self.bot.get_user(admin_id)
            if admin_user:
                await admin_user.send(
                    f"📥 New assignment submitted by {student.mention} in {assignment_channel.mention}."
                )

    @commands.command(name='confirm_assignment')
    @commands.has_permissions(manage_guild=True)
    async def confirm_assignment(self, ctx, doable: bool):
        """
        Admin command to confirm if the assignment is doable.
        Usage: !confirm_assignment True/False
        """

        # Check if the command is used in an assignment channel
        assignment = self.assignments.get(ctx.channel.id)
        if not assignment:
            await ctx.send("This command can only be used in an assignment channel.")
            return

        assignment['reviewed'] = True
        assignment['doable'] = doable

        student = assignment['student']

        if doable:
            assignment['status'] = 'Awaiting Payment'

            await ctx.send(
                f"✅ The assignment has been accepted. Please proceed to payment."
            )

            # Proceed to payment handling
            # Here you might call a function or dispatch an event to initiate payment

            # Notify student
            await student.send(
                f"Hello {student.display_name},\n"
                f"Your assignment has been accepted. Please proceed to payment."
                f" Visit your assignment channel {ctx.channel.mention} for payment instructions."
            )

        else:
            assignment['status'] = 'Rejected'

            await ctx.send(
                f"❌ The assignment cannot be accepted."
            )

            # Notify student
            await student.send(
                f"Hello {student.display_name},\n"
                "We regret to inform you that we cannot assist with your assignment at this time."
            )

            # Optionally delete or archive the channel
            await ctx.send("This channel will be deleted in 1 minute.")
            await asyncio.sleep(60)
            await ctx.channel.delete()
            del self.assignments[ctx.channel.id]

    @commands.command(name='set_deadline')
    async def set_deadline(self, ctx, *, deadline_str):
        """
        Command for the student to set the assignment deadline.
        Usage: !set_deadline YYYY-MM-DD HH:MM (24-hour format)
        """
        # Check if the command is used in an assignment channel
        assignment = self.assignments.get(ctx.channel.id)
        if not assignment:
            await ctx.send("This command can only be used in your assignment channel.")
            return

        student = assignment['student']
        if ctx.author != student:
            await ctx.send("Only the assignment owner can set the deadline.")
            return

        # Validate deadline
        try:
            deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
            if deadline < datetime.now():
                await ctx.send("The deadline cannot be in the past.")
                return
        except ValueError:
            await ctx.send("Please enter the deadline in the format: YYYY-MM-DD HH:MM")
            return

        assignment['deadline'] = deadline
        assignment['status'] = 'In Progress'

        await ctx.send(f"⏰ Deadline has been set to: {deadline.strftime('%Y-%m-%d %H:%M')}")

        # Notify admin
        for admin_id in config.ADMIN_IDS:
            admin_user = self.bot.get_user(admin_id)
            if admin_user:
                await admin_user.send(
                    f"📅 Deadline for assignment {assignment['assignment_id']} in {ctx.channel.mention} "
                    f"has been set to: {deadline.strftime('%Y-%m-%d %H:%M')}"
                )

    @commands.command(name='deliver_assignment')
    @commands.has_permissions(manage_guild=True)
    async def deliver_assignment(self, ctx):
        """
        Admin command to deliver the completed assignment to the student.
        Usage: !deliver_assignment
        """

        # Check if the command is used in an assignment channel
        assignment = self.assignments.get(ctx.channel.id)
        if not assignment:
            await ctx.send("This command can only be used in an assignment channel.")
            return

        assignment['status'] = 'Delivered'

        student = assignment['student']

        await ctx.send(f"{student.mention}, your assignment has been completed and delivered.")
        await ctx.send("Please review the assignment and confirm if it meets your requirements.")

        # Notify student
        await student.send(
            f"Hello {student.display_name},\n"
            f"Your assignment has been delivered in {ctx.channel.mention}.\n"
            "Please review it and let us know if any revisions are needed."
        )

    @commands.command(name='request_revision')
    async def request_revision(self, ctx, *, revision_details):
        """
        Command for the student to request a revision.
        Usage: !request_revision Details of the revision needed
        """

        # Check if the command is used in an assignment channel
        assignment = self.assignments.get(ctx.channel.id)
        if not assignment:
            await ctx.send("This command can only be used in your assignment channel.")
            return

        student = assignment['student']
        if ctx.author != student:
            await ctx.send("Only the assignment owner can request a revision.")
            return

        assignment['status'] = 'Revision Requested'
        assignment['revisions'].append({
            'details': revision_details,
            'timestamp': datetime.now()
        })

        await ctx.send("🔄 Your revision request has been received. We will work on it promptly.")

        # Notify admin
        for admin_id in config.ADMIN_IDS:
            admin_user = self.bot.get_user(admin_id)
            if admin_user:
                await admin_user.send(
                    f"🔄 Revision requested by {student.mention} in {ctx.channel.mention}.\n"
                    f"Details: {revision_details}"
                )

    @commands.command(name='close_assignment')
    @commands.has_permissions(manage_guild=True)
    async def close_assignment(self, ctx):
        """
        Admin command to close the assignment and delete or archive the channel.
        Usage: !close_assignment
        """

        # Check if the command is used in an assignment channel
        assignment = self.assignments.get(ctx.channel.id)
        if not assignment:
            await ctx.send("This command can only be used in an assignment channel.")
            return

        await ctx.send("✅ This assignment channel will be closed in 1 minute.")
        await asyncio.sleep(60)
        await ctx.channel.delete()
        del self.assignments[ctx.channel.id]

    @tasks.loop(minutes=60)
    async def deadline_reminder(self):
        """Task that runs every hour to check for upcoming deadlines and send reminders."""

        now = datetime.now()
        for assignment in list(self.assignments.values()):
            if assignment['deadline'] and assignment['status'] == 'In Progress':
                time_to_deadline = assignment['deadline'] - now
                # If less than 24 hours to deadline and no reminder sent in last 24 hours
                if time_to_deadline < timedelta(hours=24) and (not assignment['last_reminder'] or (now - assignment['last_reminder'] > timedelta(hours=24))):
                    # Send reminder to admin
                    for admin_id in config.ADMIN_IDS:
                        admin_user = self.bot.get_user(admin_id)
                        if admin_user:
                            await admin_user.send(
                                f"⏰ Reminder: Assignment {assignment['assignment_id']} in {assignment['channel'].mention} "
                                f"is due in {time_to_deadline}."
                            )
                    assignment['last_reminder'] = now

    @deadline_reminder.before_loop
    async def before_deadline_reminder(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(AssignmentManagement(bot))
