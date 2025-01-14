from opgg_Scraper import OpggScraper
from Rank_handler import RankHandler


if __name__ == '__main__':
    p_list = [("na", "ArCaNeAscension#THICC"), ("na", "soren#wolf"), ("na", "Oreozx#NA1"),
              "https://www.op.gg/summoners/na/SpaceDust-balls", "https://www.op.gg/summoners/na/Nation%20Of%20Nugs-NA1"]
    p_list.extend(["https://www.op.gg/summoners/na/Clítorís-42069", "https://www.op.gg/summoners/na/Kelso-69420",
                   "https://www.op.gg/summoners/na/Hexos926-ADC", "https://www.op.gg/summoners/na/ApolloZSL-NA1",
                   "https://www.op.gg/summoners/na/CpapaSlice-NA1"])
    # p_list = [("na", "ArCaNeAscension#THICC")]
    scraper = OpggScraper(player_list=p_list, auto_scrape=True)
    print(scraper)
    scraper.quit_driver()
    rank_handler = RankHandler(scraper.player_ranks, scraper.player_game_ranks)
    print(rank_handler)
