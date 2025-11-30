import json
from typing import Dict, Any

class Config:
    """Manages bot configuration from config.json"""

    def __init__(self, config_path: str = "config.json"):
        with open(config_path) as f:
            self._config = json.load(f)

        # Core settings
        self.token = self._config["token"]
        self.guild_id = self._config["public_guild_id"]
        self.status_text = self._config.get("status", "Watching Vilyx Network")

        # Channels
        self.channels = self._config["channels"]

        # Roles
        self.roles = self._config["public_roles"]

        # Ticket categories
        self.ticket_categories = self._config["ticket_categories"]

        self.role_hierarchy = [
            self.roles["member"],
            self.roles["mod"],
            self.roles["sr_mod"],
            self.roles["admin"],
            self.roles["sr_admin"],
            self.roles["manager"],
            self.roles["owner"],
        ]

    def get_role_id(self, role_key: str) -> int:
        """Get role ID by key"""
        return self.roles.get(role_key)
    
    def get_channel_id(self, channel_key: str) -> int:
        """Get channel ID by key"""
        return self.channels.get(channel_key)
    
    def has_role(self, user_roles: list, role_keys: list) -> bool:
        """Check if user has any of the specified roles"""
        user_role_ids = [r.id for r in user_roles]
        for key in role_keys:
            if self.get_role_id(key) in user_role_ids:
                return True
        return False