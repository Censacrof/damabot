import discord
from discord.ext import commands
import logging
import json
import emoji as EMOJI
import re


# configuro il logger
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("damabot")

bot = commands.Bot(command_prefix='$', description='La dama della gilda si occupa di gestire i ruoli degli utenti')

# dizionario (key: message_id, val: associazioni ruolo reaction)
whatchedMessages = {}

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
    global whatchedMessages

    # cancello in messaggio che contiene il comando
    await ctx.message.delete()

    # apro il file contenente le definizioni dei ruoli
    roleDefinitions = None
    try:
        with open('roles.json', 'r') as roles_file:
            roleDefinitions = json.load(roles_file)
    except Exception as e:
        err = 'Errore: Impossibile fare il parsing dei ruoli\n' + ' - ' + str(e)
        log.error(err)
        await ctx.send(err)
        return
    
    whatchedMessages = {}
    for group in roleDefinitions['groups']:
        embed = discord.Embed(title=group['title'], description=group['description'], color=0x08457E)
        
        for role in group['roles']:
            embed.add_field(name=role['title'], value=role['description'], inline=False)
        msg = await ctx.send(embed=embed)
        
        reactionRoleAssociation = []
        for role in group['roles']:
            emoji = None
            if role['emoji'] in EMOJI.UNICODE_EMOJI:
                # emoji unicode
                emoji = discord.PartialEmoji(name=role['emoji'])
            else:
                # emoji custom
                match = re.match('^:[^:]+:([0-9]+)$', role['emoji'])

                if match is not None:
                    # se la regex ha prodotto un match uso l' id dell'emoji per trovarla
                    emoji = bot.get_emoji(int(match.group(1)))

            if emoji is None:
                log.warn("Non e' stata trovata un emoji corrispondente a: " + role['emoji'])
                continue

            await msg.add_reaction(emoji)
            reactionRoleAssociation.append({ 
                "emoji": emoji, 
                "roleID":  role['roleID']
            })

        whatchedMessages[msg.id] = reactionRoleAssociation
    pass

@bot.event
async def on_raw_reaction_add(payload):
    # se la reaction e' stata messa dal bot stesso la ignoro
    if payload.member.bot:
        return
    
    print(payload)

    if payload.message_id in whatchedMessages:        
        for assoc in whatchedMessages[payload.message_id]:
            if assoc['emoji'] == payload.emoji:
                role = discord.utils.get(payload.member.guild.roles, id=assoc['roleID'])
                await payload.member.add_roles(role)    
    pass

bot.run('NzM5NjYxNjUwOTUyNTg1Mjc3.Xydtlw.H6wzJOtzXu8elFVo-4SJ4jDvD-4')