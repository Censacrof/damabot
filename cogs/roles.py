import discord
from discord.ext import commands
import json
import emoji as EMOJI
import re
import os
import argparse
import importlib.resources 
import jsonschema

class Roles(commands.Cog):
    def __init__(self, bot, log):
        self.bot = bot
        self.log = log

        if not os.path.exists('cache'):
            os.mkdir('cache')

        with importlib.resources.path('cogs.schema', 'roles_config_schema.json') as schema_path:
            with open(schema_path, 'r') as f:
                self._config_schema = json.load(f)

        self.WATCHED_MESSAGES_FILE = 'cache/watched_messages.cache'
        self.CONFIG_FILE = 'roles_config.json'

        # carico il dizionario dei messaggi da controllare
        self._watched_messages = {}
        if os.path.isfile(self.WATCHED_MESSAGES_FILE):
            try:
                with open(self.WATCHED_MESSAGES_FILE, 'r') as f:
                    self._watched_messages = json.load(f)
                    f.close()
                    self.log.info('Deserializzato watchedMessages')
            except Exception:
                self.log.warning('Impossibile deserializzare watchedMessages')
    
    # comandi
    @commands.command()
    async def ping(self, ctx):
        """Risponde pong! utile per testare se il bot e' online"""
        await ctx.send('pong!')
        pass

    @commands.command()
    async def clear(self, ctx):
        """Rimove tutti i messaggi dal canale testuale"""
        async for message in ctx.channel.history():
            await message.delete()
        pass

    @commands.command()
    async def genera(self, ctx):
        """Genera ed invia il messaggio di selezione ruolo per il canale testuale in cui viene invocato"""

        # cancello in messaggio che contiene il comando
        await ctx.message.delete()

        # apro il file contenente le definizioni dei ruoli
        roleDefinitions = None
        try:
            with open(self.CONFIG_FILE, 'r') as roles_file:
                roleDefinitions =  json.load(roles_file)
                jsonschema.validate(roleDefinitions, self._config_schema)

        except Exception as e:
            err = 'Errore: Impossibile fare il parsing dei ruoli' + ' - ' + str(e)
            self.log.error(err)
            await ctx.send(err)
            return
        
        # controllo che siano stati definiti dei ruoli per questo canale
        channelID = ctx.message.channel.id
        channelRoleDefinitions = None
        for chnRls in roleDefinitions:
            if chnRls['channelID'] == channelID:
                channelRoleDefinitions = chnRls
                break
        
        if channelRoleDefinitions is None:
            await ctx.send('Non sono stati definiti ruoli per questo canale. (ID del canale: ' + str(ctx.message.channel.id) + ')')
            return 

        self._watched_messages[channelID] = {}
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
                        fullEmoji = self.bot.get_emoji(int(match.group(1)))
                        if fullEmoji is not None:
                            emoji = discord.PartialEmoji(id=fullEmoji.id, name=fullEmoji.name, animated=fullEmoji.animated)

                if emoji is None:
                    self.log.warning("Non e' stata trovata un emoji corrispondente a: " + role['emoji'])
                    continue

                await msg.add_reaction(emoji)
                reactionRoleAssociation.append({ 
                    'emojiName': emoji.name,
                    'emojiID':  emoji.id,
                    'roleID':  role['roleID']
                })
            self._watched_messages[channelID][msg.id] = reactionRoleAssociation

        # serializzo watchedMessages
        self.log.info('Serializzo watchedMessage')
        try:
            with open(self.WATCHED_MESSAGES_FILE, 'w') as f:
                json.dump(self._watched_messages, f, ensure_ascii=False)
                f.close()
        except Exception as e:
            err = 'Errore: Impossibile serializzare watchedMessages\n' + ' - ' + str(e)
            self.log.error(err)
            await ctx.send(err)
            return
        pass

    # eventi
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # se la reaction e' stata messa dal bot stesso la ignoro
        if payload.member.bot:
            return

        channelID = payload.channel_id
        msgid = payload.message_id
        
        if channelID not in self._watched_messages:
            return
        
        if msgid not in self._watched_messages[channelID]:
            return
        
        for assoc in self._watched_messages[channelID][msgid]:
            if assoc['emojiName'] == payload.emoji.name and assoc['emojiID'] == payload.emoji.id:
                role = discord.utils.get(payload.member.guild.roles, id=assoc['roleID'])
                await payload.member.add_roles(role)    
        pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild = await self.bot.fetch_guild(payload.guild_id)
        member = await guild.fetch_member(payload.user_id)

        channelID = payload.channel_id
        msgid = payload.message_id

        if channelID not in self._watched_messages:
            return
        
        if msgid not in self._watched_messages[channelID]:
            return

        for assoc in self._watched_messages[channelID][msgid]:
            if assoc['emojiName'] == payload.emoji.name and assoc['emojiID'] == payload.emoji.id:
                role = discord.utils.get(guild.roles, id=assoc['roleID'])
                await member.remove_roles(role)
        pass