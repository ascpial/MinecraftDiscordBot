"""This file provides helpers for the configuration managment."""

import json
from typing import List

class Configuration:
    BOT_TOKEN: str
    LOG_CHANNEL_ID: int
    SERVER_CHANNEL_ID: int

    MINECRAFT_SERVER_IP: str
    PORT: int

    MINECRAFT_OFFLINE_VERSIONS: List[str]
    MINECRAFT_STARTING_VERSIONS: List[str]

    EMBED_ICON_URL: str
    POLLING_INTERVAL: float

    def __init__(self, filename: str) -> None:
        with open(filename) as config_file:
            self.raw_json = json.load(config_file)
        
        assert "discord" in self.raw_json, "the discord field is required"
        self.BOT_TOKEN = self.raw_json["discord"]["bot_token"]
        self.LOG_CHANNEL_ID = self.raw_json["discord"].get("log_channel")
        self.SERVER_CHANNEL_ID = self.raw_json["discord"].get("server_channel")

        assert "minecraft" in self.raw_json, "the minecraft field is required"
        self.MINECRAFT_SERVER_IP = self.raw_json["minecraft"]["ip_adress"]
        self.MINECRAFT_SERVER_PORT = self.raw_json["minecraft"].get("port", 25565)

        self.MINECRAFT_OFFLINE_VERSIONS = self.raw_json["minecraft"].get("offline", [])
        self.MINECRAFT_STARTING_VERSIONS = self.raw_json["minecraft"].get("starting", [])

        if "other" in self.raw_json:
            self.POLLING_INTERVAL = self.raw_json["other"].get("polling_interval", 15.0)
            self.EMBED_ICON_URL = self.raw_json["other"].get("icon_url")
        else:
            self.EMBED_ICON_URL = None
            self.POLLING_INTERVAL = 15.0