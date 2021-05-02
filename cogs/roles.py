import discord
from discord.ext import commands
import json
import emoji as EMOJI
import re
import os
import argparse
import importlib.resources 
import jsonschema
import shutil

class Roles(commands.Cog):
    def __init__(self, bot, log):
        self.bot = bot
        self.log = log

        if not os.path.exists('cache'):
            os.mkdir('cache')
        if not os.path.exists('config'):
            os.mkdir('config')

        with importlib.resources.path('cogs.resources', 'roles_config_schema.json') as schema_path:
            with open(schema_path, 'r') as f:
                self._config_schema = json.load(f)

        self.WATCHED_MESSAGES_FILE = 'cache/watched_messages.cache'
        self.CONFIG_FILE = 'config/roles.json'

        # if the config file doesn't exists copy the default one
        if not os.path.isfile(self.CONFIG_FILE):
            with importlib.resources.path('cogs.resources', 'roles_config_default.json') as default_cfg_path:
                shutil.copy2(default_cfg_path, self.CONFIG_FILE)
                

        # load the dict of messages to check
        self._watched_messages = {}
        if os.path.isfile(self.WATCHED_MESSAGES_FILE):
            try:
                with open(self.WATCHED_MESSAGES_FILE, 'r') as f:
                    self._watched_messages = json.load(f)
                    f.close()
                    self.log.info('Deserializing \'{}\''.format(self.WATCHED_MESSAGES_FILE))
            except Exception:
                self.log.warning('Can\'t deserialize watchedMessages')
    
    @commands.command()
    async def ping(self, ctx):
        """Answers pong! Useful to check if the bot is online"""
        await ctx.send('pong!')
        pass

    @commands.command()
    async def clear(self, ctx):
        """Removes all messages from the text channel"""
        async for message in ctx.channel.history():
            await message.delete()
        pass

    @commands.command()
    async def generate(self, ctx):
        """Generates the role selection messages for the text channel in which is invoked"""

        # delete the command message
        await ctx.message.delete()

        # load the role definitions from the config
        role_definitions = None
        try:
            with open(self.CONFIG_FILE, 'r') as roles_file:
                role_definitions =  json.load(roles_file)
                jsonschema.validate(role_definitions, self._config_schema)

        except Exception as e:
            err = 'Can\'t parse \'{}\': {}'.format(self.CONFIG_FILE, str(e))
            self.log.error(err)
            await ctx.send(err)
            return
        
        # check that there are roles are defined for this channel che siano stati definiti dei ruoli per questo canale
        channelID = ctx.message.channel.id
        channel_role_definitions = None
        for chnRls in role_definitions:
            if chnRls['channelID'] == channelID:
                channel_role_definitions = chnRls
                break
        
        if channel_role_definitions is None:
            await ctx.send('There are no roles defined for this channel. (Channel ID: {})'.format(str(ctx.message.channel.id)))
            return
        
        self._watched_messages[channelID] = {}
        use_embed = 'useEmbed' in channel_role_definitions and channel_role_definitions['useEmbed']
        for section in channel_role_definitions['sections']:
            embed = discord.Embed(title=section['title'], description=section['description'], color=0x08457E)
            msg_content = '----------------------------------\n**{title}**\n{description}'.format_map(section)

            for role in section['roles']:
                reg = r'[^\s]'
                if 'title' in role and role['title'] is not None\
                and re.search(reg, role['title']) is not None\
                and 'description' in role and role['description'] is not None\
                and re.search(reg, role['description']) is not None:
                    # embed version
                    title = role['emoji'] + ' ' + role['title']
                    desc = role['description']
                    embed.add_field(name=title, value=desc, inline=True)

                    # regular message version
                    msg_content += '\n\n***{emoji} {title}:*** `{description}`'.format_map(role)
            msg_content += '\n----------------------------------'

            if use_embed:
                msg = await ctx.send(embed=embed)
            else:
                msg = await ctx.send(content=msg_content)
            
            reaction_role_association = []
            for role in section['roles']:
                emoji = None
                if role['emoji'] in EMOJI.UNICODE_EMOJI:
                    # unicode emoji
                    emoji = discord.PartialEmoji(name=role['emoji'])
                else:
                    # custom emoji
                    match = re.match('^\\<:[^:]+:([0-9]+)\\>$', role['emoji'])

                    if match is not None:
                        # if there is a match use the emoji's id to get it
                        fullEmoji = self.bot.get_emoji(int(match.group(1)))
                        if fullEmoji is not None:
                            emoji = discord.PartialEmoji(id=fullEmoji.id, name=fullEmoji.name, animated=fullEmoji.animated)

                if emoji is None:
                    self.log.warning('Couldn\'t find an emoji that corresponds to \'{}\''.format(role['emoji']))
                    continue

                await msg.add_reaction(emoji)
                reaction_role_association.append({ 
                    'emojiName': emoji.name,
                    'emojiID':  emoji.id,
                    'roleID':  role['roleID']
                })
            self._watched_messages[channelID][msg.id] = reaction_role_association

        # serialize watchedMessages
        self.log.info('Serializing \'{}\''.format(self.WATCHED_MESSAGES_FILE))
        try:
            with open(self.WATCHED_MESSAGES_FILE, 'w') as f:
                json.dump(self._watched_messages, f, ensure_ascii=False)
                f.close()
        except Exception as e:
            err = 'Can\'t serialize \'{}\': {}'.format(self.WATCHED_MESSAGES_FILE, str(e))
            self.log.error(err)
            await ctx.send(err)
            return
        pass


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # if the reaction was added by the bot i return
        if payload.member.bot:
            return

        channelID = payload.channel_id
        channelID_str = str(channelID)
        msgid = payload.message_id
        msgid_str = str(msgid)
        
        if channelID_str not in self._watched_messages:
            return
        
        if msgid_str not in self._watched_messages[channelID_str]:
            return
        
        for assoc in self._watched_messages[channelID_str][msgid_str]:
            if assoc['emojiName'] == payload.emoji.name and assoc['emojiID'] == payload.emoji.id:
                role = discord.utils.get(payload.member.guild.roles, id=assoc['roleID'])
                await payload.member.add_roles(role)    
        pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild = await self.bot.fetch_guild(payload.guild_id)
        member = await guild.fetch_member(payload.user_id)

        channelID = payload.channel_id
        channelID_str = str(channelID)
        msgid = payload.message_id
        msgid_str = str(msgid)

        if channelID_str not in self._watched_messages:
            return
        
        if msgid_str not in self._watched_messages[channelID_str]:
            return

        for assoc in self._watched_messages[channelID_str][msgid_str]:
            if assoc['emojiName'] == payload.emoji.name and assoc['emojiID'] == payload.emoji.id:
                role = discord.utils.get(guild.roles, id=assoc['roleID'])
                await member.remove_roles(role)
        pass