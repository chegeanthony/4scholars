# bot.py

import discord
from discord.ext import commands
import logging
import config
import os
import sys
import asyncio

# ---------------------------
# Logging Configuration
# ---------------------------

# Create logs directory if it doesn't exist
if not os.path.exists('data/logs'):
    os.makedirs('data/logs')

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOGGING_LEVEL.upper(), None),
    format='%(asctime)s:%(levelname)s:%(name)s: %(message)s',
    handlers=[
        logging.FileHandler(filename='data/logs/bot.log', encoding='utf-8', mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)

# ---------------------------
# Intents and Bot Initialization
# ---------------------------

intents = discord.Intents.default()
intents.members = True  # Required for member-related events
intents.message_content = True  # Required to read message content

bot = commands.Bot(command_prefix='!', intents=intents)

# Remove the default help command to implement a custom one if needed
bot.remove_command('help')

# ---------------------------
# Load Cogs Asynchronously
# ---------------------------

async def load_extensions():
    initial_extensions = [
        'cogs.assignment_management',
        'cogs.payment_handling',
        'cogs.communication',
        'cogs.feedback'
    ]
    for extension in initial_extensions:
        try:
            await bot.load_extension(extension)
            logging.info(f'Loaded extension: {extension}')
        except Exception as e:
            logging.error(f'Failed to load extension {extension}.', exc_info=True)

# ---------------------------
# Global Events
# ---------------------------

@bot.event
async def on_ready():
    logging.info(f'{bot.user.name} has connected to Discord!')
    logging.info(f'Bot User ID: {bot.user.id}')
    logging.info('------')

    # Set the bot's status
    activity = discord.Game(name="Helping with assignments")
    await bot.change_presence(status=discord.Status.online, activity=activity)

@bot.event
async def on_command_error(ctx, error):
    """
    Global error handler for commands.
    """
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("⚠️ Command not found. Please use `!help` to see all available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Missing arguments. Please check the command usage.")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("⚠️ You do not have permission to use this command.")
    else:
        await ctx.send("⚠️ An unexpected error occurred. Please contact the admin.")
        logging.error(f'Unhandled exception in command {ctx.command}:', exc_info=True)

@bot.event
async def on_member_join(member):
    """
    Event handler for when a new member joins the server.
    Sends a welcome message if needed.
    """
    logging.info(f'New member joined: {member.name} (ID: {member.id})')

    # You can send a welcome message or assign roles here if needed

# ---------------------------
# Main Function to Run the Bot
# ---------------------------

async def main():
    async with bot:
        await load_extensions()
        try:
            await bot.start(config.BOT_TOKEN)
        except discord.errors.LoginFailure:
            logging.error('Invalid bot token. Please check your BOT_TOKEN in config.py')
            print('Invalid bot token. Please check your BOT_TOKEN in config.py')

if __name__ == '__main__':
    asyncio.run(main())
