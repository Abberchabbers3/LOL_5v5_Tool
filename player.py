import random
from itertools import groupby

import Rank_handler
from collections import Counter
def shuffle_ties(role_chance):
    result = []
    for key, group in groupby(role_chance, key=lambda x: x[1]):
        group = list(group)  # Convert the group to a list
        if len(group) > 1:  # Shuffle if there's a tie
            random.shuffle(group)
        result.extend(group)
    return result


class Player:
    minimum_game_threshold = 5

    def __init__(self, name, rank_score, champs_played, mastery):
        self.name = name
        self.rank_score = rank_score
        self.rank_str = Rank_handler.score_to_str(self.rank_score)
        self.champs = champs_played
        self.mastery = mastery
        total = max(1, sum([self.champs[role].total() for role in self.champs]))
        sorted_roles = sorted(self.champs, key=lambda role: self.champs[role].total(), reverse=True)
        self.role_chance = [(role, round(self.champs[role].total() / total, 2)) for role in sorted_roles]
        self.role_chance = shuffle_ties(self.role_chance)
        self.preferred_roles = [role for role in sorted_roles if self.champs[role].total() > self.minimum_game_threshold]
        self.preferred_roles.append("flex")
        # TODO make dict that links each role to a rank_score

    def __str__(self):
        output = ""
        output += f"{self.name}: "
        output += f"{self.rank_str} ({self.rank_score})\n"
        output += f"Highest mastery champs: {", ".join(self.mastery)}\n"
        output += f"Preferred Roles: {self.preferred_roles}\n"
        output += f"Role_chances (testing only): {self.role_chance}\n"
        return output

    def update_roles(self):
        # TODO update how rank/role is handled; need to update match_maker too
        pass


if __name__ == '__main__':
    p = Player("test_man", 20, {'top': Counter({'Warwick': 1}), 'jungle': Counter({'Udyr': 1}), 'mid': Counter({'Lux': 2, "Kai'Sa": 2, 'Aurelion Sol': 1, 'Aurora': 1, 'Jhin': 1}), 'adc': Counter({"Kai'Sa": 5, 'Jhin': 1, 'Vayne': 1, 'Swain': 1, 'Miss Fortune': 1, 'Ezreal': 1, 'Aurelion Sol': 1, 'Zoe': 1}), 'supp': Counter({'Zoe': 3, "Kai'Sa": 1})},['Ezreal', "Kai'Sa", 'Yasuo', 'Lux'])
    print(p)

