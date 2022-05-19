# Minecraft discord logger

Mincraft discord logger is a discord bot which allows you to see your minecraft server status and players directly in discord.
The bot can send you join message without the need of a plugin.

The bot is supposed to work with a vanilla and a modded server.

The configuration allows you to support servers hoster like aternos.

# Installation


# Setup

First, you need a discord bot token. If you don't know how to do it, look on the internet, there is a lot of great tutorials for that.

When you have your token, you can create a file name `configuration.json` with the following pattern :
```json
{
    "$schema": "./configuration-scheme.json"
}
```

If your text editor does not support scheme checking, use the following pattern:
```json
{
    "$schema": "./configuration-scheme.json",
    "discord": {
        "bot_token": "BOT_TOKEN",
        "log_channel": LOG_CHANNEL_ID,
        "server_channel": SERVER_CHANNEL_ID
    },
    "minecraft": {
        "ip_adress": "SERVER_IP",
        "port": SERVER_PORT
    },
    "other": {
        "polling_interval": POLLING_INTERVAL,
        "icon_url": "ICON_URL"
    }
}
```
Replace the values with the correct ones. Here is the reference:
* `BOT_TOKEN`: the discord token of the bot. Should looks like this: `OIAJDjdazoijd76Azdazd32d.X2OITw.azdiojoij87zadlkj78zad-y6nc` **REQUIRED**
* `LOG_CHANNEl_ID`: The ID of the channel where join message will be sent. Should look like this: 870607520958382131
* `SERVER_CHANNEL_ID`: The ID of the channel where status message will be sent. Should look like this: 870607520958382131

* `SERVER_IP`: The IP or the domain name of the server. Should look like this `mc.example.com` or like this `192.168.0.1` **REQUIRED**
*  `SERVER_PORT`: The port used by the minecraft server. By default, 25565

* `POLLING_INTERVAL`: The interval between pings to the server in seconds. By default, 15.0 seconds
* `ICON_URL`: The url of the icon used in the embed for server status. Should looks like this: `https://example.com/img/img1892.png`