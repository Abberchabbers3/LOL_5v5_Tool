import random
from itertools import groupby
import Rank_handler
from collections import Counter


def convert_to_name(player_data):
    """
    Converts an op.gg link into a player name
    :param player_data: valid op.gg link with player name
    :return: str player_name
    """
    if isinstance(player_data, tuple):
        return player_data[0]
    elif isinstance(player_data, str):
        return player_data.split("/")[-1].replace("%20", " ").replace("-", "#")


def name_to_link(name: str, server="na"):
    """
    Parses a player name into a valid op.gg link
    :param name: str name to parse in form name#tag
    :param server: server of player, default 'na'
    :return: str created link
    """
    player_name = name.replace(" #", "#")
    link = 'https://www.op.gg/summoners/' + server + '/' + player_name.replace(" ", "%20").replace("#", "-")
    return link


class Player:
    # Minimum percentage of someone's game for it to be considered as a preferred_role
    minimum_game_percentage_threshold = 0.25

    def __init__(self, name, rank_score, champs_played, mastery, role_ranks=None, role_chances=None, preferred_roles=None):
        """
        :param name: Name of the player
        :param rank_score: rank_score, typically calculated by rank handler, int from 0-36
        :param champs_played: dict of all champs played in each role
        :param mastery: list of 4 highest mastery champions
        :param role_ranks: dict of each role (and flex) and the associated rank; *passing in a value for this will cause the init to ignore rank_score*
        """
        self.name = name
        self.link = name_to_link(self.name)
        self.champs = champs_played
        self.mastery = mastery
        total = max(1, sum([self.champs[role].total() for role in self.champs]))
        sorted_roles = sorted(self.champs, key=lambda role: self.champs[role].total(), reverse=True)
        # loads roles from storage or by minimum game threshold, i.e. as long as 25% of a players games are a role
        # it is assumed to be preferred
        if preferred_roles:
            self.preferred_roles = preferred_roles
        else:
            self.preferred_roles = [role for role in sorted_roles if self.champs[role].total() > total * self.minimum_game_percentage_threshold]
            self.preferred_roles.append("flex")
        # loads dict representing rank for each role; allows players to decide what they feel their rank is
        if role_ranks:
            self.role_ranks = role_ranks
            self.rank_str_by_role = {role: Rank_handler.score_to_str(rank) for role, rank in self.role_ranks.items()}
            self.rank_score = self.role_ranks[self.preferred_roles[0]]
            self.rank_str = self.rank_str_by_role[self.preferred_roles[0]]
        # if this data is not stored simply populate calculated rank into all roles as League does not store
        # individual role ranks
        else:
            self.rank_score = rank_score
            self.rank_str = Rank_handler.score_to_str(rank_score)
            self.role_ranks = dict(top=rank_score, jungle=rank_score, mid=rank_score,
                               adc=rank_score, supp=rank_score, flex=rank_score)
            self.rank_str_by_role = dict(top=self.rank_str, jungle=self.rank_str, mid=self.rank_str,
                               adc=self.rank_str, supp=self.rank_str, flex=self.rank_str)
        # Load stored role chances
        if role_chances:
            self.role_chances = role_chances
        # or calculate based on how many times they play each role in their last 40 games
        else:
            self.role_chances = {role: round((100 * self.champs[role].total() / total) - 0.5) for role in sorted_roles}
        self.validate_chances()
        self.elo = 0

    def __str__(self):
        """
        :return: Str value representing a player object
        """
        output = ""
        output += f"{self.name}: "
        output += f"{self.rank_str} ({self.rank_score})\n"
        output += f"Highest mastery champs: {", ".join(self.mastery)}\n"
        output += f"Preferred Roles: {self.preferred_roles}\n"
        output += f"Role_ranks (testing only): {self.rank_str_by_role}\n"
        return output

    def update_roles(self, role_ranks):
        """
        Updates a players roles and ranks based on player enetered information
        :param role_ranks: a list of tuples of the form (new_role, new_rank, new_chance) for each role;
        # Should always contain either all five roles or end in 'flex'
        :return:
        """
        pref_roles = []
        self.role_chances = {role: 0 for role in self.role_chances}
        for role, rank, chance in role_ranks:
            pref_roles.append(role)
            self.rank_str_by_role[role] = rank
            if role != "flex":
                self.role_chances[role] = chance
        self.preferred_roles = pref_roles
        # Update everything after flex to be the same as flex
        self.rank_str_by_role.update({role: self.rank_str_by_role['flex']
                                      for role in ["supp", "top", "jungle", "mid", "adc"] if role not in self.preferred_roles})
        for role, rank_str in self.rank_str_by_role.items():
            rank = Rank_handler.rank_to_num(rank_str)
            if int(self.role_ranks[role]) != rank:
                self.role_ranks[role] = rank
        self.rank_score = self.role_ranks[self.preferred_roles[0]]
        self.rank_str = self.rank_str_by_role[self.preferred_roles[0]]
        self.validate_chances()

    def validate_chances(self, max_chance=90):
        """
        This function will redistribute role_chances so that for each role min = 1% and max = max, default 90%
        :param max_chance: the max percentage for a role, and int between 20 and 96, default 90
        :return:
        """
        # anything before flex must be an int, flex and after doesn't matter
        total = 100
        for i, role in enumerate(self.preferred_roles):
            # Flex will always be last, so role chances are split evenly among those not selected
            if role == "flex":
                roles_left = {"supp", "top", "jungle", "mid", "adc", "flex"} ^ set(self.preferred_roles)
                chance_split = total / len(roles_left)
                self.role_chances.update({role: chance_split for role in roles_left})
                total = 0
            else:
                new_val = max(1, min(max_chance, self.role_chances[role]))
                total -= new_val
                if total < 4-i:
                    new_val -= (4-i)-total
                    total = 4-i
                self.role_chances[role] = new_val
        # if all roles were selected and not enough percentage was selected, distribute all remaining evenly
        # add any remainder to the first selected
        while total > 0:
            for role in self.preferred_roles:
                if total == 0:
                    break
                # Add 1 to the role if it doesn't exceed max_chance
                if self.role_chances[role] < max_chance:
                    self.role_chances[role] += 1
                    total -= 1

    def display_champs(self, role):
        """
        Displays the champions a player plays in the order:
        most recent,
        highest mastery if ever played in that role over the past 40 games
        :param role: str role must be a key in self.champs
        :return:
        """
        mastered = set()
        for champ in self.mastery:
            if champ in self.champs[role]:
                mastered.add(champ)
        recent_played = {champ[0] for champ in self.champs[role].most_common(3)}
        recent_played.update(mastered)
        if not recent_played:
            return ""
        return ", ".join(recent_played)


if __name__ == '__main__':
    # Simple test displaying a player with no stored information
    p = Player("test_man", 20, {'top': Counter({'Warwick': 1}), 'jungle': Counter({'Udyr': 1}), 'mid': Counter({'Lux': 2, "Kai'Sa": 2, 'Aurelion Sol': 1, 'Aurora': 1, 'Jhin': 1}), 'adc': Counter({"Kai'Sa": 5, 'Jhin': 1, 'Vayne': 1, 'Swain': 1, 'Miss Fortune': 1, 'Ezreal': 1, 'Aurelion Sol': 1, 'Zoe': 1}), 'supp': Counter({'Zoe': 3, "Kai'Sa": 1})},['Ezreal', "Kai'Sa", 'Yasuo', 'Lux'])
    print(p)

