import json
from datetime import datetime, timedelta
from collections import Counter
from player import Player


def format_time_difference(time_difference):
    """
    given a time difference, pretty format a result
    :param time_difference: time difference in the form of datetime.datetime
    :return:
    """
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
        """
        Creates a storage tool meant to store scraped dat in json format
        :param file_name: Any json file name to store player data, default is known_players.json
        """
        self.file_name = file_name
        # Initialize the file if it doesn't exist
        try:
            with open(self.file_name, 'r') as file:
                json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            with open(self.file_name, 'w') as file:
                json.dump({}, file)

    def add_player(self, player, overwrite_time=True):
        """
        Attempts to add a PLayer object to the json file
        :param player: player object with wanted information to store
        :param overwrite_time: True if want to reset scrape timer, false if not
        :return:
        """
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
        """
        Attempts to retrieve a stored player;
        If it has been more than one week since data was last scraper or player was not found, returns None
        :param name: name of stored player information to retrieve in form of name#tag
        :return: a created player object from stored data, returns None on failure
        """
        data = self._load_data()
        player_data = data.get(name)
        if not player_data:
            print(f"No data found for {name}, now scraping")
            return None

        # Checks if the data is too old
        added_date = datetime.fromisoformat(player_data["added_date"])
        # Disabled in .exe version for dist simplicity
        if datetime.now() - added_date > timedelta(weeks=1):
            print(f"Data for {name} is too old, re-scraping")
            return None
        print(f"Data for {name} was found, data is {format_time_difference(datetime.now() - added_date)} old")
        player_object = Player(name, player_data['rank_score'],
                               {r: Counter(data) for r, data in player_data['champs'].items()}, player_data['mastery'],
                               player_data["role_ranks"], role_chances=player_data["role_chances"], preferred_roles=player_data["preferred_roles"])
        return player_object

    def _load_data(self):
        """
        Opens json file to read
        :return:
        """
        with open(self.file_name, 'r') as file:
            return json.load(file)

    def _save_data(self, data):
        """
        Opens json file to dump new data
        :param data: data to be added to the file
        :return:
        """
        with open(self.file_name, 'w') as file:
            json.dump(data, file, indent=4)

# Example Usage
if __name__ == '__main__':
    # Simple example of player information being added and retrieved
    p = Player(
        "Totally_not_Marco", 8.35,
        {'top': Counter({'Rengar': 1}), 'jungle': Counter({'Rengar': 14, 'Shaco': 1, 'Udyr': 1}), 'mid': Counter(), 'adc': Counter({'Twitch': 3, "Kai'Sa": 1}), 'supp': Counter()},
        ['Rengar', 'Shaco', 'Twitch', 'Udyr']
    )
    storage = StorageTool()
    storage.add_player(p, overwrite_time=False)
    print(storage.get_player("IversusSkaidon#NA1"))
