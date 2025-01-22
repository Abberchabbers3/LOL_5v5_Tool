from opgg_Scraper import OpggScraper
from Rank_handler import RankHandler, rank_to_points
from player import Player, convert_to_name
from storage_tool import StorageTool
from match_maker import MatchMaker
from flask import Flask, render_template, request, redirect, url_for, jsonify
import os, signal

app = Flask(__name__)


def create_players_from_link_doc(link_doc, force_reset=False) -> list[Player]:
    """
    Creates Player objects for each valid op.gg link found in link_doc
    :param link_doc: The document to scrape op.gg links
    :param force_reset: Forces scraping regardless of date
    :return: The list of created player objects list[Player]
    """
    p_list = []
    with open(link_doc) as player_file:
        for line in player_file:
            p_list.append(line.replace('\n', ''))
    players = []
    to_scrape = []
    if force_reset:
        for p in p_list:
            to_scrape.append(p)
            print(f"Force resetting info for: {convert_to_name(p)}")
    else:
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
    """
    The main page of the website, displays player data and allows for manipulation of data through index.html
    :return: renders html template
    """
    max_roles = max(len(player.preferred_roles) for player in match_algo.players)
    return render_template("index.html", players=players, roles=dropdown_roles,
                           ranks=dropdown_ranks, divisions=divisions, max_roles=max_roles)


@app.route("/update_player", methods=["POST"])
def update_player():
    """
    A function which reads the dropdown options on index.html and edits corresponding global player data
    :return: redirects to index
    """
    for i, player in enumerate(players):
        total_chance = 100
        # Fetch data for the current player
        role_ranks = []
        roles = []
        for k, _ in enumerate(player.preferred_roles):
            new_role = request.form.get(f"role{i}{k}")
            new_rank = request.form.get(f"rank{i}{k}")
            new_division = ""
            if new_rank not in ["Master", "Grandmaster", "Challenger"]:
                # TODO make more robust solution to this bug?
                new_division = request.form.get(f"division{i}{k}")
                if new_division == "N/A":
                    new_division = "4"
            if new_role in roles:
                continue
            if new_role != "flex":
                roles.append(new_role)
                new_chance = int(request.form.get(f"chance{i}{k}"))
                total_chance -= new_chance
            else:
                new_chance = total_chance
            role_ranks.append((f"{new_role}", f"{new_rank}{" "+new_division if new_division else new_division}", new_chance))
            if new_role == "flex":
                break
        # Update player's attributes
        if "flex" not in [role_rank[0] for role_rank in role_ranks] and len(role_ranks) < 5:
            role_ranks.append(("flex", role_ranks[-1][1], total_chance))
        # sort by new_chance, keep flex at the end
        role_ranks = sorted(role_ranks[:-1], key=lambda x: x[2], reverse=True) + [role_ranks[-1]]
        player.update_roles(role_ranks)
        storage.add_player(player, overwrite_time=False)
    return redirect(url_for("index"))


def index_to_location(player_index):
    """
    Converts location of dropdown within the grid found on display players from and int to role, index tuple
    :param player_index: The int of the  dropdown menu 0-9
    :return: Corresponding role i.e. 0-1 is top, 4-5 is mid, and 0 or 1 for left or right team
    """
    roles = ["top", "jungle", "mid", "adc", "supp"]
    role = roles[player_index // 2]
    return role, player_index % 2


@app.route('/swap_players', methods=['POST'])
def swap_players():
    """
    Receives button info from display_teams.html; makes appropriate swaps
    :return: Returns an error if failed and success message if succeed
    """
    data = request.get_json()
    if not data or 'players' not in data or len(data['players']) != 2:
        return jsonify({"error": "Invalid input"}), 400

    player_indexes = data['players']
    try:
        player_1 = index_to_location(player_indexes[0])
        player_2 = index_to_location(player_indexes[1])
        temp = match_algo.assignments[player_1[0]][player_1[1]]
        match_algo.assignments[player_1[0]][player_1[1]] = match_algo.assignments[player_2[0]][player_2[1]]
        match_algo.assignments[player_2[0]][player_2[1]] = temp
        match_algo.lane_diffs = match_algo.calc_lane_diffs()
        match_algo.best_match_diff = match_algo.calc_match_diff()
        return jsonify({"success": "Players swapped"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/make_teams", methods=["POST"])
def make_team():
    """
    Result of pressing the make_team button, done here to not recreate teams each reload of display_teams
    :return: Redirects to display_teams
    """
    global match_algo
    match_algo = MatchMaker(players)
    return redirect(url_for("display_teams"))


@app.route("/display_teams")
def display_teams():
    """
    Displays created team
    :return: Renders display_teams.html
    """
    # TODO currently, display teams only accepts 1 team, allow it to display multiple
    return render_template("display_teams.html", match_data=match_algo)


@app.route('/stopServer', methods=['GET'])
def stop_server():
    """
    Instantly kills the app
    :return: Kills the app
    """
    os.kill(os.getpid(), signal.SIGINT)
    return jsonify({ "success": True, "message": "Server is shutting down..." })


if __name__ == '__main__':
    # Initiate storage tool, scrape players, initialize the match algorithm, and start the app
    storage = StorageTool()
    # TODO instead of scraping have players enter info to google sheet and take from there?
    players = create_players_from_link_doc("links.txt", force_reset=False)
    players = sorted(players, key=lambda p: p.name)
    dropdown_roles = ["top", "jungle", "mid", "adc", "supp", "flex"]
    dropdown_ranks = rank_to_points.keys()
    divisions = ["N/A", "1", "2", "3", "4"]
    match_algo = MatchMaker(players)
    app.run(debug=True)


