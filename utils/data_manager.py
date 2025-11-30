import json
import os
from typing import Dict, Any, Optional

class DataManager:
    """Manages persistent ticket data storage"""

    def __init__(self, data_file: str = "data.json"):
        self.data_file = data_file
        self._data = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        """Load data from file or create new file"""
        if not os.path.exists(self.data_file):
            with open(self.data_file, "w") as f:
                json.dump({}, f)
            return {}
        
        with open(self.data_file) as f:
            return json.load(f)
        
    def save(self):
        """Save data to file"""
        with open(self.data_file, "w") as f:
            json.dump(self._data, f, indent=2)

    def get_ticket(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Get ticket data by channel ID"""
        return self._data.get(channel_id)
    
    def create_ticket(self, channel_id: str, user_id: int, category: str):
        """Create new ticket entry"""
        self._data[channel_id] = {
            "user": user_id,
            "category": category,
            "claimed": False,
            "archived": False
        }
        self.save()

    def update_ticket(self, channel_id: str, **kwargs):
        """Update ticket properties"""
        if channel_id in self._data:
            self._data[channel_id].update(kwargs)
            self.save()

    def delete_ticket(self, channel_id: str):
        """Remove ticket from data"""
        self._data.pop(channel_id, None)
        self.save()

    def is_archived(self, channel_id: str) -> bool:
        """Check if ticket is archived"""
        ticket = self.get_ticket(channel_id)
        return ticket.get("archived", False) if ticket else False