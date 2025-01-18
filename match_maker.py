import random
from collections import deque

class MatchMaker:
    def __init__(self, player_list):
        self.players = player_list
        self.assignments = dict(top=[], jungle=[], mid=[], adc=[], supp=[])
        # self.greedy_start()
        self.balance_roles()
        self.lane_diffs = self.calc_lane_diffs()
        self.best_match_diff = self.calc_match_diff()
        self.balance_teams()
        self.lane_diffs = self.calc_lane_diffs()
        self.best_match_diff = self.calc_match_diff()
        print(self)

    def __str__(self):
        output = ""
        # for player in self.players:
        #     output += f"{player}"
        output += f"Match roles: \n"
        for role, players in self.assignments.items():
            output += f"{role}:\t{[f"{p.name}({p.rank_str}){"(auto)" if role not in p.preferred_roles and p.preferred_roles[0] != "flex" else ""}"
                                   for p in players]}, Lane diff: "
            # if role in ["adc", "supp"]:
            #     output += f"{self.lane_diffs["bot"]}\n"
            # else:
            output += f"{self.lane_diffs[role]}\n"
        output += f"Total Match Diff: {self.best_match_diff}"
        return output

    def greedy_start(self):
        low_to_high = sorted(self.players, key=lambda p: p.rank_score)
        for player in low_to_high:
            # Need to rework this
            for role, chance in player.role_chances.items():
                if len(self.assignments[role]) < 2:  # Check if role is available
                    self.assignments[role].append(player)
                    break
            # Idea for algorithm: for each player randomly assign a role based on self.role_chance; if full
            # keep two closest together (by rank) players and kick the other
            # player out, then roll for their new role; repeat until somewhat balanced?

    def balance_roles(self):
        queue = deque([p for p in self.players])
        while queue:
            player = queue.popleft()
            role_choices = list(player.role_chances.keys())
            role_weights = list(player.role_chances.values())
            role = random.choices(role_choices, role_weights, k=1)[0]
            print(player.name, role)
            if len(self.assignments[role]) > 1:
                player_group = self.get_best_pair(role, self.assignments[role][0], self.assignments[role][1], player)
                self.assignments[role] = list(player_group[:2])
                # TODO modify loser?
                queue.append(player_group[2])
            else:
                self.assignments[role].append(player)

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
        print(swap_sequences)
        for gen in swap_sequences:
            for swap_list in gen:
                swap_value = sum([-1*self.lane_diffs[lane] if lane in swap_list else self.lane_diffs[lane]
                                  for lane in ['top', 'mid', 'jungle']])
                # values for bot and supp need to be averaged
                bot_swap_value = sum([-1*self.lane_diffs[lane] if lane in swap_list else self.lane_diffs[lane]
                                  for lane in ['adc', 'supp']]) / 2
                swap_value += bot_swap_value
                print(swap_value, swap_list)
                # want to find if target + swap_value closest to 0
                if abs(swap_value) < abs(best_sum):
                    print(f"{best_sum} worse than {swap_value}", swap_list)
                    best_sum = swap_value
                    best_swaps = swap_list
        for swap in best_swaps:
            print(f"swapped: {swap}")
            self.assignments[swap] = self.assignments[swap][::-1]




    def calc_lane_diffs(self):
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
        return round(sum(self.lane_diffs[lane] for lane in self.lane_diffs if lane != "adc" and lane != "supp"), 2)

    def get_best_pair(self, role, player1, player2, player3):
        # TODO prioritize non-off roles
        # TODO prioritize closeness in rank
        # TODO ties broken by person with higher chance score
        # TODO further ties broken by ???
        return player1, player2, player3


if __name__ == '__main__':
    role_chances = {
        "top": 53,
        "supp": 24,
        "jungle": 14,
        "mid": 3,
        "adc": 3
    }