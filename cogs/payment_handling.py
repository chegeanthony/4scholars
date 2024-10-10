# cogs/payment_handling.py

import discord
from discord.ext import commands
import asyncio
from .utilities import create_payment_links, verify_payment
import config

class PaymentHandling(commands.Cog):
    """Cog for handling payment processing and status tracking."""

    def __init__(self, bot):
        self.bot = bot
        self.payment_sessions = {}  # Stores payment data

    @commands.command(name='generate_payment')
    async def generate_payment(self, ctx, amount: float):
        """
        Command to generate payment links after assignment confirmation.
        Usage: !generate_payment amount
        """

        # Only allow admins to use this command
        if ctx.author.id not in config.ADMIN_IDS:
            await ctx.send("You do not have permission to use this command.")
            return

        # Check if the command is used in an assignment channel
        assignment_channel = ctx.channel
        assignment_id = assignment_channel.name.replace('assignment-', '')

        # Retrieve the assignment data (assuming it's stored in a shared variable)
        assignment_cog = self.bot.get_cog('AssignmentManagement')
        assignment = assignment_cog.assignments.get(assignment_channel.id)
        if not assignment:
            await ctx.send("This command can only be used in an assignment channel.")
            return

        if assignment['status'] != 'Awaiting Payment':
            await ctx.send("Payment has already been generated or the assignment is not ready for payment.")
            return

        # Generate payment links
        payment_id = f"{assignment_id}-{assignment['student'].id}"
        payment_links = create_payment_links(payment_id, amount)

        if not payment_links:
            await ctx.send("Error generating payment links. Please check the payment gateway configuration.")
            return

        # Store the payment session
        self.payment_sessions[payment_id] = {
            'assignment_id': assignment_id,
            'student_id': assignment['student'].id,
            'channel_id': assignment_channel.id,
            'amount': amount,
            'paid': False
        }

        # Update assignment status
        assignment['status'] = 'Awaiting Payment Confirmation'

        # Send payment links to the student in the assignment channel
        await assignment_channel.send(
            f"{assignment['student'].mention}, please complete your payment of **${amount:.2f}** using one of the following options:\n"
            f"**PayPal:** {payment_links['paypal']}\n"
            f"**Stripe:** {payment_links['stripe']}\n"
            "After completing the payment, please use the `!confirm_payment` command."
        )

    @commands.command(name='confirm_payment')
    async def confirm_payment(self, ctx):
        """
        Command for students to confirm payment.
        Usage: !confirm_payment
        """

        # Check if the command is used in an assignment channel
        assignment_channel = ctx.channel
        assignment_id = assignment_channel.name.replace('assignment-', '')

        # Retrieve the assignment data
        assignment_cog = self.bot.get_cog('AssignmentManagement')
        assignment = assignment_cog.assignments.get(assignment_channel.id)
        if not assignment:
            await ctx.send("This command can only be used in your assignment channel.")
            return

        student = assignment['student']
        if ctx.author != student:
            await ctx.send("Only the assignment owner can confirm payment.")
            return

        if assignment['status'] != 'Awaiting Payment Confirmation':
            await ctx.send("Payment is not pending for this assignment.")
            return

        payment_id = f"{assignment_id}-{student.id}"

        # Verify the payment
        payment_successful = verify_payment(payment_id)

        if payment_successful:
            await ctx.send("✅ Thank you! Your payment has been received. We will start working on your assignment shortly.")
            assignment['status'] = 'In Progress'
            self.payment_sessions[payment_id]['paid'] = True

            # Log payment status in #payment-status channel
            payment_status_channel = self.bot.get_channel(config.PAYMENT_STATUS_CHANNEL_ID)
            if payment_status_channel:
                await payment_status_channel.send(f"**Assignment ID:** {assignment_id} | **Status:** Paid | **Amount:** ${self.payment_sessions[payment_id]['amount']:.2f}")

            # Notify admins
            for admin_id in config.ADMIN_IDS:
                admin_user = self.bot.get_user(admin_id)
                if admin_user:
                    await admin_user.send(
                        f"💵 Payment received for Assignment {assignment_id} in {assignment_channel.mention}. You may begin working on the assignment."
                    )

        else:
            await ctx.send("⚠️ We could not verify your payment. Please ensure you've completed the payment and try again.")

    @commands.command(name='check_payment_status')
    @commands.has_permissions(manage_guild=True)
    async def check_payment_status(self, ctx, assignment_id: str):
        """
        Admin command to check the payment status of an assignment.
        Usage: !check_payment_status assignment_id
        """

        payment_id = f"{assignment_id}-{ctx.author.id}"

        payment_session = self.payment_sessions.get(payment_id)
        if not payment_session:
            await ctx.send(f"No payment record found for Assignment ID: {assignment_id}")
            return

        if payment_session['paid']:
            await ctx.send(f"✅ Payment has been received for Assignment ID: {assignment_id}.")
        else:
            await ctx.send(f"❌ Payment is still pending for Assignment ID: {assignment_id}.")

async def setup(bot):
    await bot.add_cog(PaymentHandling(bot))
