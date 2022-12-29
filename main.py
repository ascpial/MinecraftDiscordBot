import json

import discord
from discord.ext import tasks

import server

client = discord.Client(intents=discord.Intents.default())

with open('configuration.json') as file:
    config = json.load(file)

token = config.get('token')

trackers_data = config.get('servers')

trackers: list[server.Tracker] = []

for tracker in trackers_data:
    trackers.append(server.Tracker.from_data(tracker))

@tasks.loop(seconds=5)
async def update():
    for tracker in trackers:
        await tracker.update(client)

launched = False

@client.event
async def on_ready():
    global launched
    if not launched:
        update.start()
        launched = True
    print(f"Ready! Connected as {client.user.name}!")

client.run(token)