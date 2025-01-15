from opgg_Scraper import OpggScraper, convert_to_name
from Rank_handler import RankHandler, rank_to_points
from player import Player
from storage_tool import StorageTool
from match_maker import MatchMaker
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

def create_players_from_link_doc(link_doc):
    p_list = []
    with open(link_doc) as player_file:
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
            p = Player(player, rank_handler.player_scores[player], scraper.player_champs[player],
                       scraper.player_mastery[player])
            storage.add_player(p)
            players.append(p)
    return players

@app.route("/")
def index():
    return render_template("index.html", players=players, roles=dropdown_roles, ranks=dropdown_ranks)

if __name__ == '__main__':
    players = create_players_from_link_doc("links.txt")
    # TODO implement simple Flask hosting
    dropdown_roles = ["Top", "Jungle", "Mid", "ADC", "Support"]
    dropdown_ranks = rank_to_points.keys()
    app.run(debug=True)
    # TODO Display all players on Flask, add dropdowns for changes

    # TODO Update player information based on dropdown changes

    # TODO (after testing) Save changes to known_players_json (set overwrite_time to False)

    match_algo = MatchMaker(players)
    print(match_algo)
