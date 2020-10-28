import discord
from discord.ext import commands
import logging
import json
import emoji as EMOJI
import re
import os

WATCHED_MESSAGES_FILE = 'watched_messages.json'


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

# carico il dizionario dei messaggi da controllare
watched_messages = {}
if os.path.isfile(WATCHED_MESSAGES_FILE):
    try:
        with open(WATCHED_MESSAGES_FILE, 'r') as f:
            watched_messages = json.load(f)
            f.close()
            log.info('Deserializzato watchedMessages')
    except Exception as e:
        log.warning('Impossibile deserializzare watchedMessages')

log.debug("watched_messages: " + str(watched_messages))

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
async def genera(ctx):
    """Genera ed invia il messaggio di selezione ruolo per il canale testuale in cui viene invocato"""
    global watched_messages

    # cancello in messaggio che contiene il comando
    await ctx.message.delete()

    # apro il file contenente le definizioni dei ruoli
    roleDefinitions = None
    try:
        with open('roles.json', 'r') as roles_file:
            roleDefinitions =  json.load(roles_file)
    except Exception as e:
        err = 'Errore: Impossibile fare il parsing dei ruoli\n' + ' - ' + str(e)
        log.error(err)
        await ctx.send(err)
        return
    
    # controllo che siano stati definiti dei ruoli per questo canale
    channelID = str(ctx.message.channel.id)
    channelRoleDefinitions = None
    for chnRls in roleDefinitions:
        if chnRls['channelID'] == channelID:
            channelRoleDefinitions = chnRls
            break
    
    if channelRoleDefinitions is None:
        await ctx.send('Non sono stati definiti ruoli per questo canale. (ID del canale: ' + str(ctx.message.channel.id) + ')')    

    watched_messages[channelID] = {}
    for group in channelRoleDefinitions['groups']:
        embed = discord.Embed(title=group['title'], description=group['description'], color=0x08457E)
        
        for role in group['roles']:
            reg = r'[^\s]'
            if 'title' in role and role['title'] is not None\
            and re.search(reg, role['title']) is not None\
            and 'description' in role and role['description'] is not None\
            and re.search(reg, role['description']) is not None: 
                title = role['emoji'] + ' ' + role['title']
                desc = role['description']
                embed.add_field(name=title, value=desc, inline=True)
        msg = await ctx.send(embed=embed)
        
        reactionRoleAssociation = []
        for role in group['roles']:
            emoji = None
            if role['emoji'] in EMOJI.UNICODE_EMOJI:
                # emoji unicode
                emoji = discord.PartialEmoji(name=role['emoji'])
            else:
                # emoji custom
                match = re.match('^\\<:[^:]+:([0-9]+)\\>$', role['emoji'])

                if match is not None:
                    # se la regex ha prodotto un match uso l' id dell'emoji per trovarla
                    fullEmoji = bot.get_emoji(int(match.group(1)))
                    if fullEmoji is not None:
                        emoji = discord.PartialEmoji(id=fullEmoji.id, name=fullEmoji.name, animated=fullEmoji.animated)

            if emoji is None:
                log.warning("Non e' stata trovata un emoji corrispondente a: " + role['emoji'])
                continue

            await msg.add_reaction(emoji)
            reactionRoleAssociation.append({ 
                'emojiName': emoji.name,
                'emojiID':  emoji.id,
                'roleID':  role['roleID']
            })
        watched_messages[channelID][str(msg.id)] = reactionRoleAssociation

    # serializzo watchedMessages
    log.info('Serializzo watchedMessage')
    try:
        with open('watched_messages.json', 'w') as f:
            json.dump(watched_messages, f, ensure_ascii=False)
            f.close()
    except Exception as e:
        err = 'Errore: Impossibile serializzare watchedMessages\n' + ' - ' + str(e)
        log.error(err)
        await ctx.send(err)
        return
    pass

@bot.event
async def on_raw_reaction_add(payload):
    # se la reaction e' stata messa dal bot stesso la ignoro
    if payload.member.bot:
        return

    channelID = str(payload.channel_id)
    msgid = str(payload.message_id)
    
    if channelID not in watched_messages:
        return
    
    if msgid not in watched_messages[channelID]:
        return
    
    for assoc in watched_messages[channelID][msgid]:
        if assoc['emojiName'] == payload.emoji.name and assoc['emojiID'] == payload.emoji.id:
            role = discord.utils.get(payload.member.guild.roles, id=assoc['roleID'])
            await payload.member.add_roles(role)    
    pass

@bot.event
async def on_raw_reaction_remove(payload):
    guild = await bot.fetch_guild(payload.guild_id)
    member = await guild.fetch_member(payload.user_id)

    channelID = str(payload.channel_id)
    msgid = str(payload.message_id)

    if channelID not in watched_messages:
        return
    
    if msgid not in watched_messages[channelID]:
        return

    for assoc in watched_messages[channelID][msgid]:
        if assoc['emojiName'] == payload.emoji.name and assoc['emojiID'] == payload.emoji.id:
            role = discord.utils.get(guild.roles, id=assoc['roleID'])
            await member.remove_roles(role)
    pass

bot.run('NDAzODU0MDgyMDIxNzg1NjAx.WmHEbA.09g1vYH_jZ8kRuINuR4PfTGNohY')