from __future__ import annotations

from typing import List, TYPE_CHECKING

import nextcord
from nextcord.ext import commands, tasks

import minecraft

if TYPE_CHECKING:
    from configuration import Configuration

SERVER_STATUS = [
    "Offline",
    "Online",
    "Starting"
]

SERVER_STATUS_EMOJIS = ["⚫", "🟢", "🔴"]

BOT_STATUS = [
    nextcord.Status.invisible,
    nextcord.Status.online,
    nextcord.Status.do_not_disturb,
]

class MinecraftPingerCog(commands.Cog):
    def __init__(self, bot: commands.Bot, config: Configuration) -> None:
        self.bot = bot
        self.ready = False

        self.config = config

        self.status = 0
        self.refresh_needed = True
        self.players: List[str] = []

        self.refresh.change_interval(seconds=self.config.POLLING_INTERVAL)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if self.config.LOG_CHANNEL_ID is not None:
            self.log_channel = self.bot.get_channel(self.config.LOG_CHANNEL_ID)
        if self.config.SERVER_CHANNEL_ID is not None:
            self.server_channel = self.bot.get_channel(self.config.SERVER_CHANNEL_ID)
        
        if not self.ready:
            self.refresh.start()
        
        self.ready = True

    @tasks.loop()
    async def refresh(self):
        try:
            server_status = minecraft.ping(
                self.config.MINECRAFT_SERVER_IP,
                port=self.config.MINECRAFT_SERVER_PORT
            )
            await self.update_players(server_status)
            self.update_status(server_status=server_status)

        except TimeoutError:
            self.update_status(status=0)
        except ConnectionRefusedError:
            self.update_status(status=0)
        except AttributeError:
            self.update_status(status=2)
        
        if self.refresh_needed:
            await self.refresh_status()
            if self.config.SERVER_CHANNEL_ID is not None:
                await self.refresh_server()
            self.refresh_needed = False
    
    async def update_players(self, server_status: minecraft.Server):
        players = [player.name for player in server_status.players]

        login_players = []
        logout_players = []

        for player in players:
            if not player in self.players:
                login_players.append(player)
        
        for player in self.players:
            if not player in players:
                logout_players.append(player)
        
        if len(login_players) > 0 or len(logout_players) > 0:
            self.refresh_needed = True
        
        message_list = [f"{player} a rejoint la partie\n" for player in login_players]
        message_list.extend((f"{player} a quitté la partie\n" for player in logout_players))
        message = "```fix\n"

        for act_message in message_list:
            if len(message) + len(act_message) + 3 <= 2000:
                message += act_message
            else:
                await self.log_channel.send(content=message+"```")
                message = "```fix\n"
        
        if message != "```fix\n":
            await self.log_channel.send(content=message+"```")
        
        self.players = players
    
    def update_status(
        self,
        status: int = None,
        server_status: minecraft.Server = None
    ) -> None:
        if status is not None:
            if status != self.status:
                self.status = status
                self.refresh_needed = True
        else:
            self.version = server_status.version
            self.max_players = server_status.players.max

            if self.version in self.config.MINECRAFT_OFFLINE_VERSIONS:
                self.update_status(status=0)
                return
            elif self.version in self.config.MINECRAFT_STARTING_VERSIONS:
                self.update_status(status=2)
                return
            else:
                self.update_status(status=1)
    
    def get_embed(self):
        embed = nextcord.Embed(title=f"Minecraft Server {self.config.MINECRAFT_SERVER_IP}", colour=0xb99213)

        status_string = SERVER_STATUS_EMOJIS[self.status] + SERVER_STATUS[self.status]

        embed.add_field(name="Status", value=f"`{status_string}`", inline=True)

        if self.status == 1:
            embed.add_field(name="Version", value=f"`{self.version}`", inline=True)
            if len(self.players) > 0:
                players_string = "\n".join(self.players)
            else:
                players_string = "Aucun joueur"
            embed.add_field(
                name=f"Joueurs {len(self.players)}/{self.max_players}", value=f"```fix\n{players_string}```", inline=False
            )
        
        embed.set_footer(text=self.config.MINECRAFT_SERVER_IP, icon_url=self.config.EMBED_ICON_URL)
        return embed
        
    async def refresh_server(self):
        embed = self.get_embed()
        
        try:
            last_message = await self.server_channel.fetch_message(self.server_channel.last_message_id)
            if last_message is None or last_message.author != self.bot.user:
                await self.server_channel.send(embed=embed)
            await last_message.edit(embed=embed)
        except nextcord.errors.NotFound:
            await self.server_channel.send(embed=embed)
        except ValueError:
            await self.server_channel.send(embed=embed)

    async def refresh_status(self):
        status = BOT_STATUS[self.status]

        if self.status == 1:
            if len(self.players) != 1:
                activity = nextcord.Game(
                    f"Minecraft with {len(self.players)} players"
                )
            else:
                activity = nextcord.Game(
                    f"Minecraft with 1 player"
                )
        else:
            activity = None
        
        await self.bot.change_presence(status=status, activity=activity)

def setup(bot: commands.Bot, config: Configuration):
    bot.add_cog(MinecraftPingerCog(bot, config))