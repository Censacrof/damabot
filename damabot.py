import discord
from discord.ext import commands
import logging
import argparse

from cogs.roles import Roles
from cogs.temporary_channels import TemporaryChannels

# configure argument parsing
parser = argparse.ArgumentParser(description="La dama della gilda.")
parser.add_argument('token', help="Il token del bot")
args = parser.parse_args()

# configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("damabot.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("damabot")

bot = commands.Bot(command_prefix='$', description='Dama takes care of the guild members\' roles and makes sure there\'s always room for everybody')

bot.add_cog(Roles(bot, log))
bot.add_cog(TemporaryChannels(bot, log))
bot.run(args.token)