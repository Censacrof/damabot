import discord
from discord.ext import commands
import logging
import argparse

from cogs.roles import Roles
from cogs.temporary_channels import TemporaryChannels

# configuro il parsing dei parametri di ingresso
parser = argparse.ArgumentParser(description="La dama della gilda.")
parser.add_argument('token', help="Il token del bot")
args = parser.parse_args()

# configuro il logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("damabot.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("damabot")

bot = commands.Bot(command_prefix='$', description='La dama della gilda si occupa di gestire i ruoli degli utenti')

bot.add_cog(Roles(bot, log))
bot.add_cog(TemporaryChannels(bot, log))
bot.run(args.token)