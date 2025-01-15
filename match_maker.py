
class MatchMaker:
    def __init__(self, player_list):
        self.players = player_list
        self.assignments = dict(top=[], jungle=[], mid=[], adc=[], supp=[])
        self.greedy_start()
        self.lane_diffs = self.calc_lane_diffs()
        self.best_match_diff = self.calc_match_diff()

    def __str__(self):
        output = ""
        for player in self.players:
            output += f"{player}"
        output += f"Match roles: \n"
        for role, players in self.assignments.items():
            output += f"{role}:\t{[f"{p.name}({p.rank_str})" for p in players]}, Lane diff: "
            if role in ["adc","supp"]:
                output += f"{self.lane_diffs["bot"]}\n"
            else:
                output += f"{self.lane_diffs[role]}\n"
        output += f"Total Match Diff: {self.best_match_diff}"
        return output

    def greedy_start(self):
        low_to_high = sorted(self.players, key=lambda p: p.rank_score)
        for player in low_to_high:
            for role, chance in player.role_chance:
                if len(self.assignments[role]) < 2:  # Check if role is available
                    self.assignments[role].append(player)
                    break
        print([(p.name, p.rank_score) for p in low_to_high])

    def calc_lane_diffs(self):
        lane_diffs = dict(top=0,jungle=0,mid=0,bot=0)
        for lane in lane_diffs:
            if lane != "bot":
                lane_diffs[lane] = round(self.assignments[lane][1].rank_score - self.assignments[lane][0].rank_score,2)
            else:
                team2 = (self.assignments["adc"][1].rank_score + self.assignments["adc"][1].rank_score)/2
                team1 = (self.assignments["adc"][0].rank_score + self.assignments["adc"][0].rank_score)/2
                lane_diffs["bot"] = round(team2 - team1,2)
        return lane_diffs

    def calc_match_diff(self):
        return sum(self.lane_diffs[lane] for lane in self.lane_diffs)


if __name__ == '__main__':
    pass