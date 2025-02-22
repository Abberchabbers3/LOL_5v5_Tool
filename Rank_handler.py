from collections import defaultdict

rank_to_points = {'Iron': 0, 'Bronze': 4, 'Silver': 8, 'Gold': 12, 'Platinum': 16, 'Emerald': 20,
                      'Diamond': 24, 'Master': 28, 'Grandmaster': 32, 'Challenger': 36}
points_to_rank = {0: 'Iron', 4: 'Bronze', 8: 'Silver', 12: 'Gold', 16: 'Platinum', 20: 'Emerald',
                      24: 'Diamond', 28: 'Master', 32: 'Grandmaster', 36: 'Challenger'}


def score_to_str(score):
    """
    Converts an integer from 0-36 into corresponding rank str
    :param score: int from 0-36
    :return: Rank string resulting from encoded number
    """
    tier = score // 4 * 4
    division = 4 - int(score % 4)
    return f"{points_to_rank[tier]} {division}" if division else points_to_rank[tier]


def rank_to_num(rank: str):
    """
    Encodes rank str into number representing relative skill level of a player in a role
    :param rank: Rank str to be encoded
    :return: encoded int value from 0-36
    """
    rank = rank.split(" ")
    if len(rank) > 1:
        return rank_to_points[rank[0]] + (4-int(rank[1]))
    return rank_to_points[rank[0]]


class RankHandler:

    def __init__(self, player_ranks, player_game_ranks):
        """
        Creates a rank handler object; this object is intended to parse player rank information
        When creating a rank handler, the entered ranks and game ranks will be combined on a weighted average
        This calculates a very rough average of a players rank based on recent games
        Please Note: This number is meant to simply represent a basic idea of whom a player often players against
        This is not necessarily indicative of their skill or hidden MMR; players who play ranked more often are
        likely to be the most accurate
        :param player_ranks: Dictionary of seasons linked to player ranks in the form of season : rank
        :param player_game_ranks: List of recent average ranks of games
        """
        self.player_scores = defaultdict(float)
        self.player_ranks = player_ranks
        self.player_game_ranks = player_game_ranks
        self.calculate_avg_ranks()

    def calculate_avg_ranks(self):
        """
        Computes a weighted avg of recent player game ranks and official in game rank
        :return:
        """
        for player in self.player_ranks:
            # Gather current and past season ranks and weight them
            season_avg = self.rank_list_to_avg(player)
            # Gather ranks from past 20 games and weight them
            game_avg = self.game_list_to_avg(player)
            # Based on above scores get avg rank and add it to player scores
            final_avg = 0.65 * season_avg + 0.35 * game_avg
            self.player_scores[player] = round(final_avg, 5)

    def rank_list_to_avg(self, player):
        """
        :param player: Name of a player, their ranks over time will be average with weight applied based on recency
        :return:Average of player ranks from recent seasons in encoded int form
        """
        total_score = 0
        total_weight = 0
        for season, rank in self.player_ranks[player].items():
            if rank == 'Unranked':
                continue
            weight = self.season_to_weight(season)
            total_score += rank_to_num(rank) * weight
            total_weight += weight
        return total_score / total_weight if total_weight > 0 else -1

    def game_list_to_avg(self, player):
        """
        :param player: Name of a player, their games in self.player_game_ranks wil be averaged
        :return: Average of player ranks from recent games in encoded int form
        """
        total_score = 0
        for rank in self.player_game_ranks[player]:
            total_score += rank_to_num(rank)
        return total_score/len(self.player_game_ranks[player]) if len(self.player_game_ranks[player]) > 0 else -1

    def season_to_weight(self, season: str):
        """
        Calculates the correct weight based on how recent a seaosn was
        Assumes current season is 2025.S1
        :param season: the str respresent the current season, i.e. S2024 S2
        :return: a float frm 0.05 to 1, larger means the date is more recent
        """
        # Assume seasons are in the format "SYYYY S#", e.g., "S2025 S1"
        current_season = "S2025 S1"
        current_year, current_split = map(int, current_season[1:].split(" S"))
        if " " in season:
            season_year, season_split = map(int, season[1:].split(" S"))
        elif "20" in season:
            season_year = int(season[1:])
            season_split = 3
        else:
            season_year = 2010 + int(season[1:])
            season_split = 3
        # Calculate difference in splits (3 splits per year)
        split_diff = (current_year - season_year) * 3 + (current_split - season_split)
        # Weight decays exponentially with the split difference
        return max(0.05, 1.0 - 0.2 * split_diff)

    def __str__(self):
        """
        Returns players average rank score in string form
        :return:
        """
        output = ""
        for player, score in self.player_scores.items():
            output += f"{player}: \n"
            output += f"{score} which is about {score_to_str(score)} \n"
        return output



if __name__ == '__main__':
    # Simple rank handler example
    rh = RankHandler({'me': {'S2024 S3': 'Gold 4', 'S2024 S2': 'Platinum 4', 'S2024 S1': 'Platinum 4', 'S2023 S2': 'Gold 4', 'S2022': 'Silver 1'}},
                     {'me': ['Platinum 4', 'Silver 3', 'Silver 2', 'Gold 2', 'Gold 3', 'Gold 3', 'Gold 4', 'Gold 3', 'Gold 2', 'Silver 2', 'Gold 3', 'Silver 1']})
    print(rh)

