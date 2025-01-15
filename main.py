from opgg_Scraper import OpggScraper, convert_to_name
from Rank_handler import RankHandler
from player import Player
from storage_tool import StorageTool


if __name__ == '__main__':
    p_list = []
    with open("links.txt") as player_file:
        for line in player_file:
            p_list.append(line.replace('\n', ''))
    # p_list = ["https://www.op.gg/summoners/na/IversusSkaidon-NA1"]
    players = []
    to_scrape = []
    storage = StorageTool()
    for player in p_list:
        player_data = storage.get_player(convert_to_name(player))
        if player_data:
            players.append(player_data)
        else:
            to_scrape.append(player)

    if to_scrape:
        scraper = OpggScraper(player_list=to_scrape, auto_scrape=True)
        # print(scraper)
        scraper.quit_driver()
        rank_handler = RankHandler(scraper.player_ranks, scraper.player_game_ranks)
        # print(rank_handler)
        for player in rank_handler.player_scores:
            p = Player(player, rank_handler.player_scores[player], scraper.player_champs[player], scraper.player_mastery[player])
            storage.add_player(p)
            players.append(p)

    for p in players:
        print(p)
