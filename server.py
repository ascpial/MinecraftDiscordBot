from __future__ import annotations

import discord
import minecraft
from enum import IntEnum
import aiohttp

class SenderType(IntEnum):
    textchannel=1
    webhook=2

class Sender:
    """Class used to store a channel or a webhook and send messages easily"""
    def __init__(
        self,
        textchannel_id: int = None,
        webhook_url: str = None,
        thread_id: int = None,
    ):
        if textchannel_id is None and webhook_url is None:
            raise ValueError(
                "Cannot create sender class without textchannel_id and webhook_url"
            )
        
        if textchannel_id is not None and webhook_url is not None:
            raise ValueError(
                "You cannot specify both textchannel_id and webhook_url"
            )
        
        if textchannel_id is not None:
            self.type = SenderType.textchannel
            self.textchannel_id = textchannel_id
        
        if webhook_url is not None:
            self.type = SenderType.webhook
            self.webhook_url = webhook_url
        
        self.thread_id = thread_id
        
    async def send(self, client:discord.Client, *args, **kwargs):
        if self.type == SenderType.textchannel:
            channel = client.get_channel(self.textchannel_id)

            if channel is None:
                raise ValueError(f'The channel id `{self.textchannel_id}` is invalid or the bot can\'t see the channel')
            
            if self.thread_id is not None:
                channel = channel.get_thread(self.thread_id)

            await channel.send(*args, **kwargs)
        
        if self.type == SenderType.webhook:
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(self.webhook_url, session=session)
                if self.thread_id is None:
                    print(await webhook.send(*args, **kwargs, wait=True))
                else:
                    thread = discord.Object(self.thread_id)
                    print(await webhook.send(*args, thread=thread, **kwargs, wait=True))

    @classmethod
    def from_data(cls, data: dict) -> Sender:
        return cls(
            textchannel_id=data.get('channel'),
            webhook_url=data.get('webhook'),
            thread_id=data.get('thread')
        )

class ServerState(IntEnum):
    offline = 0
    sleeping = 1
    starting = 2
    online = 3

class State:
    def __init__(
        self,
        ip: str,
        port: int = 25565,
        sleeping: list[str] = [],
        starting: list[str] = ['Old'],
        offline: list[str] = [],
    ):
        self.ip = ip
        self.port = port

        self.sleeping_versions = sleeping
        self.starting_versions = starting
        self.offline_versions = offline

        self.previous_state = None
        self.state= None

        self.players = set()
        self.players_login = set()
        self.players_logout = set()

    def update(self):
        self.previous_state = self.state

        try:
            server = minecraft.ping(self.ip, self.port)
        except (TimeoutError, ConnectionRefusedError): # server not reachable
            self.state = ServerState.offline
        except AttributeError: # the result cannot be parsed
            self.state = ServerState.starting
        else:
            if server.version in self.offline_versions:
                self.state = ServerState.offline
            elif server.version in self.starting_versions:
                self.state = ServerState.starting
            elif server.version in self.sleeping_versions:
                self.state = ServerState.sleeping
            else:
                self.state = ServerState.online

        if self.state != ServerState.online:
            self.players_logout = set()
            self.players_login = self.players
            self.players = set()
        elif self.state == ServerState.online:
            players = [player.name for player in server.players]
            for player in players:
                if player not in self.players:
                    self.players_login.add(player)
            
            for player in self.players:
                if player not in players:
                    self.players_logout.add(player)
            
            self.players = set(players)

        print(self.state, self.players)

        self.refreshed = True

    def new_players_login(self) -> list[str]:
        players = self.players_login
        self.players_login = set()
        return list(players)
    
    def new_players_logout(self) -> list[str]:
        players = self.players_logout
        self.players_logout = set()
        return list(players)
    
    def state_changed(self) -> bool:
        if self.refreshed:
            self.refreshed = False
            return len(self.new_players_logout()) > 0 or len(self.new_players_login()) > 0 or not (self.previous_state == self.state)
        else: # didn't updated since last call
            return False
        
    @classmethod
    def from_data(cls, data: dict) -> State:
        return cls(
            ip=data.get('ip'),
            port=data.get('port', 25565),
            sleeping=data.get('sleeping', []),
            starting=data.get('starting', ['Old']),
            offline=data.get('offline', [])
        )

class Tracker:
    def __init__(
        self,
        state: State,
        login_target: Sender = None,
        server_state: Sender = None,
        show_state_in_status: bool = False,
    ):
        self.login_target = login_target
        self.server_state = server_state
        self.show_state_in_status = show_state_in_status
        self.state = state
    
    async def update(self, client: discord.Client):
        self.state.update()

        if self.login_target is not None:
            messages = []

            new_players_login = self.state.new_players_login()
            if new_players_login != []:
                for player in new_players_login:
                    messages.append(f'{player} a rejoint la partie')
            new_players_logout = self.state.new_players_logout()
            if new_players_logout != []:
                for player in new_players_logout:
                    messages.append(f'{player} a quitté la partie')
            
            if len(messages) > 0:
                join_messages = '\n'.join(messages)
                message = f"```fix\n{join_messages}\n```"
                await self.login_target.send(client, message)
        
        update_state = self.state.state_changed()

        if self.show_state_in_status and update_state:
            if self.state.state == ServerState.online:
                if len(self.state.players) != 1:
                    game = discord.Game(f'Joue à minecraft avec {len(self.state.players)} joueurs')
                else:
                    game = discord.Game(f'Joue à minecraft avec 1 joueur')
                
                await client.change_presence(
                    activity=game,
                    status=discord.Status.online,
                )
            elif self.state.state == ServerState.starting:
                await client.change_presence(
                    status=discord.Status.dnd,
                )
            elif self.state.state == ServerState.offline:
                await client.change_presence(
                    status=discord.Status.offline,
                )
            elif self.state.state == ServerState.sleeping:
                await client.change_presence(
                    status=discord.Status.idle,
                )

    @classmethod
    def from_data(cls, data: dict) -> Tracker:
        state = State.from_data(data)

        if 'login_message' in data:
            login_target = Sender.from_data(data.get('login_message'))
        else:
            login_target = None
        if 'server_state' in data:
            server_state = Sender.from_data(data.get('server_notifs'))
        else:
            server_state = None
        
        return cls(
            state,
            login_target=login_target,
            server_state=server_state, # TODO
            show_state_in_status=data.get('show_in_status', False),
        )
