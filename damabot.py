import discord
from discord.ext import commands
import logging


# configuro il logger
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("damabot")

bot = commands.Bot(command_prefix='$', description='La dama della gilda si occupa di gestire i ruoli degli utenti')

@bot.event
async def on_ready():
    log.info('Login effettuato come {0.user}'.format(bot))

# comandi
@bot.command()
async def ping(ctx):
    """Risponde pong! utile per testare se il bot e' online"""
    await ctx.send('pong!')
    pass

@bot.command()
async def clear(ctx):
    """Rimove tutti i messaggi dal canale testuale"""
    async for message in ctx.channel.history():
        await message.delete()
    pass

@bot.command()
async def ruoli(ctx):
    """Genera ed invia il messaggio di selezione ruolo"""
    await ctx.message.delete()
    pass

bot.run('NzM5NjYxNjUwOTUyNTg1Mjc3.Xydtlw.H6wzJOtzXu8elFVo-4SJ4jDvD-4')