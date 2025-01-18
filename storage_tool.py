import json
from datetime import datetime, timedelta
from collections import Counter
from player import Player


def format_time_difference(time_difference):
    days = time_difference.days
    seconds = time_difference.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    formatted = []
    if days > 0:
        formatted.append(f"{days} day{'s' if days > 1 else ''}")
    if hours > 0:
        formatted.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes > 0:
        formatted.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    return ", ".join(formatted) or "less than 1 minute"


class StorageTool:
    def __init__(self, file_name="known_players.json"):
        self.file_name = file_name
        # Initialize the file if it doesn't exist
        try:
            with open(self.file_name, 'r') as file:
                json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            with open(self.file_name, 'w') as file:
                json.dump({}, file)

    def add_player(self, player, overwrite_time=True):
        data = self._load_data()
        if player.name in data and not overwrite_time:
            date = data[player.name].get("added_date")
        else:
            date = datetime.now().isoformat()

        # Add the player data
        data[player.name] = {
            "rank_score": player.rank_score,
            "champs": {role: dict(player.champs[role]) for role in player.champs},
            "mastery": player.mastery,
            "role_ranks": player.role_ranks,
            "role_chances": player.role_chances,
            "preferred_roles": player.preferred_roles,
            "added_date": date
        }
        self._save_data(data)

    def get_player(self, name):
        data = self._load_data()
        player_data = data.get(name)
        if not player_data:
            print(f"No data found for {name}, now scraping")
            return None

        # Checks if the data is too old
        added_date = datetime.fromisoformat(player_data["added_date"])
        if datetime.now() - added_date > timedelta(weeks=1):
            print(f"Data for {name} is too old, re-scraping")
            return None
        print(f"Data for {name} was found, data is {format_time_difference(datetime.now() - added_date)} old")
        player_object = Player(name, player_data['rank_score'],
                               {r: Counter(data) for r, data in player_data['champs'].items()}, player_data['mastery'],
                               player_data["role_ranks"], player_data["role_chances"])
        player_object.set_preferred_roles(player_data['preferred_roles'])
        return player_object

    def _load_data(self):
        with open(self.file_name, 'r') as file:
            return json.load(file)

    def _save_data(self, data):
        with open(self.file_name, 'w') as file:
            json.dump(data, file, indent=4)

# Example Usage
if __name__ == '__main__':
    p = Player(
        "Totally_not_Marco", 8.35,
        {'top': Counter({'Rengar': 1}), 'jungle': Counter({'Rengar': 14, 'Shaco': 1, 'Udyr': 1}), 'mid': Counter(), 'adc': Counter({'Twitch': 3, "Kai'Sa": 1}), 'supp': Counter()},
        ['Rengar', 'Shaco', 'Twitch', 'Udyr']
    )
    storage = StorageTool()
    # storage.add_player(p)
    print(storage.get_player("IversusSkaidon#NA1"))
