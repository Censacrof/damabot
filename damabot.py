import discord
import logging

# configuro il logger
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("damabot")

client = discord.Client()

@client.event
async def on_ready():
    log.info('Login effettuato come {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

client.run('NzM5NjYxNjUwOTUyNTg1Mjc3.Xydtlw.H6wzJOtzXu8elFVo-4SJ4jDvD-4')