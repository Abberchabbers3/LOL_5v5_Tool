import Rank_handler
from collections import Counter


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
        self.preferred_roles = [role for role in sorted_roles if self.champs[role].total() > self.minimum_game_threshold]

    def __str__(self):
        output = ""
        output += f"{self.name}: "
        output += f"{self.rank_str} ({self.rank_score})\n"
        output += f"Highest mastery champs: {", ".join(self.mastery)}\n"
        output += f"Preferred Roles: {self.preferred_roles}\n"
        output += f"Role_chances (testing only): {self.role_chance}\n"
        return output


if __name__ == '__main__':
    p = Player("test_man", 20, {'top': Counter({'Warwick': 1}), 'jungle': Counter({'Udyr': 1}), 'mid': Counter({'Lux': 2, "Kai'Sa": 2, 'Aurelion Sol': 1, 'Aurora': 1, 'Jhin': 1}), 'adc': Counter({"Kai'Sa": 5, 'Jhin': 1, 'Vayne': 1, 'Swain': 1, 'Miss Fortune': 1, 'Ezreal': 1, 'Aurelion Sol': 1, 'Zoe': 1}), 'supp': Counter({'Zoe': 3, "Kai'Sa": 1})},['Ezreal', "Kai'Sa", 'Yasuo', 'Lux'])
    print(p)

