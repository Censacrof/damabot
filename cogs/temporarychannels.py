import discord
from discord.ext import commands
import json
import threading

class TemporaryChannels(commands.Cog):
    def __init__(self, bot, log):
        self.bot = bot
        self.log = log

        self.temporary_channels = self.TemporaryChannelsList('temporary_channels.json', log)

    # events
    @commands.Cog.listener()
    async def on_ready(self):
        with self.temporary_channels.lock:
            for channelID in self.temporary_channels.get_list():
                channel = await self.bot.fetch_channel(channelID)
                try:
                    await channel.delete()
                except Exception:
                    pass
            self.temporary_channels._channels = []
            self.temporary_channels._save()
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        with self.temporary_channels.lock:
            # eliminazione canale temporaneo
            if before.channel and before.channel.id in self.temporary_channels.get_list():
                members = (await self.bot.fetch_channel(before.channel.id)).members
                if len(members) == 0:
                    self.temporary_channels.remove_channel(before.channel.id)
                    try:
                        await before.channel.delete()
                    except Exception:
                        pass

            # creazione canale temporaneo
            # ignoro gli eventi generati da canalai che non ci interessano
            if not after.channel or after.channel.id != 835167835353120789:
                return

            # creo un canale
            guild = after.channel.guild
            newChannel = await guild.create_voice_channel(name="Nuova Stanza", category=after.channel.category)
            self.temporary_channels.add_channel(newChannel.id)
            await member.move_to(newChannel)
    
    # inner classes
    class TemporaryChannelsList:
        def __init__(self, filePath, log):
            self.filePath = filePath
            self.log = log

            self.lock = threading.RLock()
            self._channels = []

            self._load()

        def _load(self):
            try:
                with open(self.filePath, 'r') as f, self.lock:
                    self._channels = json.load(f)
            except Exception as e:
                self.log.warning('Impossibile caricare la lista dei canali temporanei da \'{}\': {}'.format(self.filePath, str(e)))
                self._channels = []

        def _save(self):
            try:
                with open(self.filePath, 'w') as f, self.lock:
                    json.dump(self._channels, f)
            except Exception as e:
                self.log.warning('Impossibile salvare la lista dei canali temporanei in \'{}\': {}'.format(self.filePath, str(e)))
        
        def get_list(self):
            return self._channels.copy()
        
        def add_channel(self, channelID):
            self._channels.append(channelID)
            self._save()

        def remove_channel(self, channelID):
            self._channels.remove(channelID)
            self._save()