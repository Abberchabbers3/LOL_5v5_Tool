import random
from collections import deque, Counter

from player import Player


class MatchMaker:
    # TODO currently match_maker assumes exactly 10 players, fix this and let it create multiple teams
    def __init__(self, player_list):
        """
        Creates a set of 'balanced' teams from given set of players
        :param player_list: List of player objects (currently accepts exactly 10 only)
        """
        self.pair_cache = dict()
        self.players = player_list
        self.assignments = dict(top=[], jungle=[], mid=[], adc=[], supp=[])
        self.balance_roles()
        self.lane_diffs = self.calc_lane_diffs()
        self.best_match_diff = self.calc_match_diff()
        self.balance_teams()
        self.lane_diffs = self.calc_lane_diffs()
        self.best_match_diff = self.calc_match_diff()

    def __str__(self):
        """
        Displays match_algorithm in string format
        :return:
        """
        output = ""
        # for player in self.players:
        #     output += f"{player}"
        output += f"Match roles: \n"
        for role, players in self.assignments.items():
            output += f"{role}:\t{[f"{p.name}({p.rank_str}){"(auto)" if role not in p.preferred_roles and p.preferred_roles[0] != "flex" else ""}"
                                   for p in players]}, Lane diff: "
            output += f"{self.lane_diffs[role]}\n"
        output += f"Bot diff: {self.lane_diffs["bot"]}\n"
        output += f"Total Match Diff: {self.best_match_diff}"
        return output

    def balance_roles(self):
        """
        Determines roles for each player using a semi-randomized customizable algorithm
        :return:
        """
        loser_count = Counter()
        # Random shuffle players for fairness as final tie-break is who was placed first
        queue = deque(random.sample([p for p in self.players], len(self.players)))
        while queue:
            player = queue.popleft()
            role_choices = list(player.role_chances.keys())
            role_weights = list(player.role_chances.values())
            role = random.choices(role_choices, role_weights, k=1)[0]
            if len(self.assignments[role]) >= 2:
                player_group = self.get_best_pair(role, [self.assignments[role][0], self.assignments[role][1], player])
                self.assignments[role] = list(player_group[:2])
                # TODO modify loser? based on loser count?
                loser_count[player_group[2].name] += 1
                queue.append(player_group[2])
            else:
                self.assignments[role].append(player)
        print(loser_count.most_common())

    def balance_teams(self):
        """
        This function assumes self.assignments is full, and uses the lane values to swap players
        within each role to get the total match diff as close to 0 as possible
        :return:
        """
        # This problem is recorded as np-complete, so I will just use exhaustive search as there are only 5 roles
        optimize_swaps = [role for role in ["top", "jungle", "mid", "adc", "supp"]]
        swap_sequences = [[[role] for role in optimize_swaps]]
        for gen in range(3):
            new_list = []
            for seq in swap_sequences[gen]:
                for role in optimize_swaps:
                    if role not in seq:
                        new_seq = sorted(seq+[role])
                        if new_seq not in new_list:
                            new_list.append(new_seq)
            swap_sequences.append(new_list)
        best_swaps = []
        best_sum = self.best_match_diff
        for gen in swap_sequences:
            for swap_list in gen:
                swap_value = sum([-1*self.lane_diffs[lane] if lane in swap_list else self.lane_diffs[lane]
                                  for lane in ['top', 'mid', 'jungle']])
                # values for bot and supp need to be averaged
                bot_swap_value = sum([-1*self.lane_diffs[lane] if lane in swap_list else self.lane_diffs[lane]
                                  for lane in ['adc', 'supp']]) / 2
                swap_value += bot_swap_value
                # want to find if target + swap_value closest to 0
                if abs(swap_value) < abs(best_sum):
                    best_sum = swap_value
                    best_swaps = swap_list
        for swap in best_swaps:
            self.assignments[swap] = self.assignments[swap][::-1]

    def calc_lane_diffs(self):
        """
        Calculates the difference in scores for each lane, combines bot lane for more accurate measure of impact
        :return: The calculated differences in the form of a dictionary
        """
        lane_diffs = dict(top=0, jungle=0, mid=0, adc=0, supp=0, bot=0)
        for lane in lane_diffs:
            if lane != "bot":
                lane_diffs[lane] = round(self.assignments[lane][1].role_ranks[lane] - self.assignments[lane][0].role_ranks[lane], 2)
            else:
                team2 = (self.assignments["adc"][1].role_ranks["adc"] + self.assignments["supp"][1].role_ranks["supp"])/2
                team1 = (self.assignments["adc"][0].role_ranks["adc"] + self.assignments["supp"][0].role_ranks["supp"])/2
                lane_diffs["bot"] = round(team2 - team1, 2)
        return lane_diffs

    def calc_match_diff(self):
        """
        Assumes calc_lane_diffs has been called
        :return: Returns a rounded sum of all the lane differences
        """
        return round(sum(self.lane_diffs[lane] for lane in self.lane_diffs if lane != "adc" and lane != "supp"), 2)

    def get_best_pair(self, role: str, players: list[Player]) -> list[Player]:
        """
        Upon input of three of more players, returns in order the most optimal player for the given role
        Takes into account lane preferences and player skill, but heavily prefers lane preferences
        Stores deterministic calls into memory to save time
        :param role: Must be a valid role in self.role_ranks
        :param players: List of three or more players
        :return: List of all original inputted players in order of fit for the role. The last player is always worst
        """
        # Players will be cached only if get_best_pair ends in a deterministic outcome, i.e. based on score
        if tuple(sorted(players, key=lambda x: x.name)) in self.pair_cache:
            return self.pair_cache[tuple(sorted(players, key=lambda x: x.name))]
        shuffled = random.sample(players, len(players))
        # Find the player who has the role at lowest priority, if ties sort by scores
        for i in range(5):
            roles = []
            for idx, player in enumerate(shuffled):
                if i >= len(player.preferred_roles):
                    return shuffled[:idx] + shuffled[idx + 1:] + [shuffled[idx]]
                roles.append(player.preferred_roles[i])
            roles = [player.preferred_roles[i] for player in shuffled]
            if role in roles:
                for idx, player_role in enumerate(roles):
                    if role != player_role:
                        return shuffled[:idx] + shuffled[idx+1:] + [shuffled[idx]]
        score_map = {player: dict() for player in players}
        for player in score_map:
            for other_player in [p for p in players if p != player]:
                score_map[player][other_player] = abs(player.role_ranks[role] - other_player.role_ranks[role])
        # find best
        best_pairs = []
        for player, others in score_map.items():
            best = 1000
            best_player = None
            for other_player, score in others.items():
                if score < best:
                    best = score
                    best_player = other_player
            best_pairs.append((best, player, best_player))
        best_pairs.sort(key=lambda x: x[0])
        best_players = Counter()
        for pair in best_pairs:
            best_players[pair[1]] += 1
            best_players[pair[2]] += 1
        self.pair_cache[tuple(sorted(players, key=lambda x: x.name))] = [counts[0] for counts in best_players.most_common()]
        return [counts[0] for counts in best_players.most_common()]


if __name__ == '__main__':
    pass