from opgg_Scraper import OpggScraper, convert_to_name
from Rank_handler import RankHandler, rank_to_points
from player import Player
from storage_tool import StorageTool
from match_maker import MatchMaker
from flask import Flask, render_template, request, redirect, url_for, jsonify

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
    return render_template("index.html", players=players, roles=dropdown_roles,
                           ranks=dropdown_ranks, divisions=divisions)


@app.route("/update_player", methods=["POST"])
def update_player():
    for i, player in enumerate(players):
        total_chance = 100
        # Fetch data for the current player
        role_ranks = []
        for k, _ in enumerate(player.preferred_roles):
            new_role = request.form.get(f"role{i}{k}")
            new_rank = request.form.get(f"rank{i}{k}")
            new_division = request.form.get(f"division{i}{k}")
            if new_role != "flex":
                new_chance = int(request.form.get(f"chance{i}{k}"))
                total_chance -= new_chance
            else:
                new_chance = total_chance
            role_ranks.append((f"{new_role}", f"{new_rank}{" "+new_division if new_division != "N/A" else ""}", new_chance))
            if new_role == "flex":
                break
        # Update player's attributes
        if "flex" not in [role_rank[0] for role_rank in role_ranks] and len(role_ranks) < 5:
            role_ranks.append(("flex", role_ranks[-1][1], total_chance))

        player.update_roles(role_ranks)
        # TODO (after testing) Save changes to known_players_json (set overwrite_time to False?)

    return redirect(url_for("index"))


@app.route('/swap_players', methods=['POST'])
def swap_players():
    data = request.get_json()
    if not data or 'players' not in data or len(data['players']) != 2:
        return jsonify({"error": "Invalid input"}), 400

    player_indexes = data['players']
    try:
        # swap players here
        print(player_indexes)


        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/make_teams", methods=["POST"])
def make_team():
    match_algo = MatchMaker(players)
    # print(match_algo)
    return render_template("make_teams.html", match_data=match_algo)

if __name__ == '__main__':
    players = create_players_from_link_doc("links.txt")
    players = sorted(players, key=lambda p: p.name)
    dropdown_roles = ["supp", "top", "jungle", "mid", "adc", "flex"]
    dropdown_ranks = rank_to_points.keys()
    divisions = ["N/A", "1", "2", "3", "4"]

    app.run(debug=True)


