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

    def __init__(self, name, rank_score, champs_played, mastery, role_ranks=None):
        '''
        :param name: Name of the player
        :param rank_score: rank_score, typically calculated by rank handler, int from 0-36
        :param champs_played: dict of all champs played in each role
        :param mastery: list of 4 highest mastery champions
        :param role_ranks: dict of each role (and flex) and the associated rank; *passing in a value for this will cause the init to ignore rank_score*
        '''
        self.name = name
        self.champs = champs_played
        self.mastery = mastery
        total = max(1, sum([self.champs[role].total() for role in self.champs]))
        sorted_roles = sorted(self.champs, key=lambda role: self.champs[role].total(), reverse=True)
        self.role_chance = [(role, round(self.champs[role].total() / total, 2)) for role in sorted_roles]
        self.role_chance = shuffle_ties(self.role_chance)
        self.preferred_roles = [role for role in sorted_roles if self.champs[role].total() > total * 0.1]
        self.preferred_roles.append("flex")
        if role_ranks:
            self.role_ranks = role_ranks
            self.rank_str_by_role = {role: Rank_handler.score_to_str(rank) for role, rank in self.role_ranks.items()}
            self.rank_score = self.role_ranks[self.preferred_roles[0]]
            self.rank_str = self.rank_str_by_role[self.preferred_roles[0]]
        else:
            self.rank_score = rank_score
            self.rank_str = Rank_handler.score_to_str(rank_score)
            self.role_ranks = dict(top=rank_score, jungle=rank_score, mid=rank_score,
                               adc=rank_score, supp=rank_score, flex=rank_score)
            self.rank_str_by_role = dict(top=self.rank_str, jungle=self.rank_str, mid=self.rank_str,
                               adc=self.rank_str, supp=self.rank_str, flex=self.rank_str)
        self.elo = 0

    def __str__(self):
        output = ""
        output += f"{self.name}: "
        output += f"{self.rank_str} ({self.rank_score})\n"
        output += f"Highest mastery champs: {", ".join(self.mastery)}\n"
        output += f"Preferred Roles: {self.preferred_roles}\n"
        output += f"Role_ranks (testing only): {self.rank_str_by_role}\n"
        return output

    def update_roles(self, role_ranks):
        self.preferred_roles = [role_rank[0] for role_rank in role_ranks]
        self.rank_str_by_role.update({role_rank[0]: role_rank[1] for role_rank in role_ranks})
        # Update everything after flex to be the same as flex
        self.rank_str_by_role.update({role: self.rank_str_by_role['flex']
                                      for role in ["supp", "top", "jungle", "mid", "adc"] if role not in self.preferred_roles})
        for role, rank_str in self.rank_str_by_role.items():
            rank = Rank_handler.rank_to_num(rank_str)
            if round(self.role_ranks[role]) != rank:
                self.role_ranks[role] = rank
        self.rank_score = self.role_ranks[self.preferred_roles[0]]
        self.rank_str = self.rank_str_by_role[self.preferred_roles[0]]
        # TODO Updates role chance based on preferred_roles

    def set_preferred_roles(self, pref_roles):
        self.preferred_roles = pref_roles


if __name__ == '__main__':
    p = Player("test_man", 20, {'top': Counter({'Warwick': 1}), 'jungle': Counter({'Udyr': 1}), 'mid': Counter({'Lux': 2, "Kai'Sa": 2, 'Aurelion Sol': 1, 'Aurora': 1, 'Jhin': 1}), 'adc': Counter({"Kai'Sa": 5, 'Jhin': 1, 'Vayne': 1, 'Swain': 1, 'Miss Fortune': 1, 'Ezreal': 1, 'Aurelion Sol': 1, 'Zoe': 1}), 'supp': Counter({'Zoe': 3, "Kai'Sa": 1})},['Ezreal', "Kai'Sa", 'Yasuo', 'Lux'])
    print(p)

