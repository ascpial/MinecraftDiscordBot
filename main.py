"""Discord bot to show minecraft server status in discord"""


import discord
from discord.ext import tasks

import minecraft
import configuration

client = discord.Client()

LOG_CHANNEL: discord.TextChannel = None
SERVER_CHANNEL: discord.TextChannel = None

status = None
players = None
player_names = None

refresh_embed = False

@client.event
async def on_ready():
    global LOG_CHANNEL, SERVER_CHANNEL
    print(f"Ready ! Logged in as {client.user.name}#{client.user.discriminator}")
    LOG_CHANNEL = client.get_channel(configuration.LOG_CHANNEL)
    SERVER_CHANNEL = client.get_channel(configuration.SERVER_CHANNEL)
    refresh.start()
    print("Started refresh loop")

@tasks.loop(seconds=configuration.INTERVAL)
async def refresh():
    """Main refresh loop"""
    global refresh_embed, player_names
    refresh_embed = False
    try:
        server_status = minecraft.ping(configuration.MINECRAFT_IP, port=configuration.MINECRAFT_PORT)
        if server_status.version == "Old":
            await change_status(2, None)
        elif server_status.version == "§4● Offline":
            await change_status(0, None)
        else:
            await change_status(1, len(server_status.players))
            if player_names is None:
                player_names = [player.name for player in server_status.players]
            else:
                await update_players(server_status.players)

        if refresh_embed:
            await resend_embed(server_status)
        
    except TimeoutError:
        await change_status(0, None)
    except ConnectionRefusedError:
        await change_status(0, None)
    except AttributeError:
        await change_status(2, None)

async def resend_embed(server_status:minecraft.Server):
    """Refresh the embed for the server channel"""
    embed = get_embed(server_status)
    # check if the last message is bot's one
    try:
        last_message = await SERVER_CHANNEL.fetch_message(SERVER_CHANNEL.last_message_id)
        if last_message is None or last_message.author != client.user:
            raise discord.NotFound
        await last_message.edit(embed=embed)
    except discord.errors.NotFound:
        await SERVER_CHANNEL.send(embed=embed)
    except ValueError:
        await SERVER_CHANNEL.send(embed=embed)

def get_embed(server_status: minecraft.Server):
    """return a discord.Embed containing the informations about the server"""
    embed = discord.Embed(title=f"Serveur minecraft {configuration.MINECRAFT_IP}", colour=0xb99213)
    status_list = ["⚫ Hors ligne", "🟢 En ligne", "🔴 Chargement du monde"]
    embed.add_field(name="Status", value=f"`{status_list[status]}`", inline=True)
    if status == 1:
        embed.add_field(name="Version", value=f"`{server_status.version}`", inline=True)
        if len(server_status > 0):
            players_string = "\n".join([player.name for player in server_status.players])
        else:
            players_string = "Aucun joueur"
        embed.add_field(name=f"Joueurs {players}/{server_status.players.max}", value=f"```fix\n{players_string}```", inline=False)
    embed.set_footer(text=configuration.MINECRAFT_IP, icon_url=configuration.ICON_URL)
    return embed

async def update_players(new_players):
    """"Refresh the needed parts for the player list, such as login messages"""
    global player_names
    new_players = [player.name for player in new_players]
    login_players = []
    logout_players = []
    for player in new_players:
        if not player in player_names:
            login_players.append(player)
    for player in player_names:
        if not player in new_players:
            logout_players.append(player)
    message_list = [f"{player} a rejoint la partie\n" for player in login_players]
    message_list.extend((f"{player} a quitté la partie\n" for player in logout_players))
    message = "```fix\n"
    for act_message in message_list:
        if len(message) + len(act_message) + 3 <= 2000:
            message += act_message
        else:
            await LOG_CHANNEL.send(content=message+"```")
            message = "```fix\n"
    if message != "```fix\n":
        await LOG_CHANNEL.send(content=message+"```")
    player_names = new_players

async def change_status(new_status, new_players):
    """Change the status to the specified value. 0 is offline, 1 is online and 2 is starting (Old, loading world)"""
    global status, players, refresh_embed
    statuss = [discord.Status.invisible, discord.Status.online, discord.Status.do_not_disturb]
    kwargs = {}
    if new_status != status:
        status = new_status
        kwargs["status"] = statuss[status]
    if new_players != players:
        players = new_players
        if players is not None:
            if players != 1:
                kwargs["activity"] = discord.Game(f"Minecraft avec {players} joueurs")
            else:
                kwargs["activity"] = discord.Game(f"Minecraft avec 1 joueur")
        else: kwargs["activity"] = None
    if len(kwargs) > 0:
        await client.change_presence(**kwargs)
        refresh_embed = True

client.run(configuration.TOKEN)