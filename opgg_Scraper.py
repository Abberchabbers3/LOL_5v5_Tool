from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import pandas as pd
from collections import defaultdict


class OpggScraper:
    CURRENT_SEASON = "S2025 S1"

    def __init__(self, server="na", player_name="", link="", player_list=None, auto_scrape=False):
        self.driver = webdriver.Chrome()
        self.link_map = dict()
        self.player_ranks = defaultdict(dict)
        self.player_game_ranks = defaultdict(list)
        if player_name:
            self.add_player_by_name(server, player_name)
        elif link:
            self.add_player_by_link(link)
        elif player_list:
            self.add_players(player_list)
        if auto_scrape:
            for player in self.link_map:
                # maybe implement threading?
                self.scrape(player, self.link_map[player])

    def add_player_by_name(self, server: str, player_name: str):
        player_name = player_name.replace(" #", "#")
        link = 'https://' + server + '.op.gg/summoner/userName=' + player_name.replace(" ", "%20").replace("#", "-")
        self.link_map[player_name] = link

    def add_player_by_link(self, link: str):
        player_name = link.split("/")[-1].replace("%20", " ").replace("-", "#")
        self.link_map[player_name] = link

    def add_players(self, server_player_list):
        for player in server_player_list:
            if isinstance(player,str):
                self.add_player_by_link(player)
            elif isinstance(player, tuple) or isinstance(player, list):
                self.add_player_by_name(player[0], player[1])

    def __str__(self):
        output = ""
        for player in self.link_map:
            output += player + "\n"
            output += str(self.player_ranks[player]) + "\n"
            output += str(self.player_game_ranks[player]) + "\n"
        return output

    def scrape(self, player, link):
        self.driver.get(link)
        self.driver.implicitly_wait(1)
        # Update profile if necessary
        self.update_profile()

        # Scrape players current ranks
        self.player_ranks[player] = self.get_current_player_ranks()

        # Scrape players past ranks
        self.player_ranks[player].update(self.get_past_player_ranks())

        # Get avg elo of last 20 games
        self.player_game_ranks[player] = self.recent_elo()

    def update_profile(self):
        update_button = self.driver.find_element(By.XPATH, '//button//span[text()="Update"]')
        time_since_update = self.driver.find_element(by=By.CLASS_NAME, value="last-update").text
        # only click if it has been 1+ hour since last update
        if 'Available' not in time_since_update and 'minute' not in time_since_update:
            update_button.click()
            while 'Available' not in time_since_update:
                # relinquish lock here
                self.driver.implicitly_wait(0.1)
                time_since_update = self.driver.find_element(by=By.CLASS_NAME, value="last-update").text

    def get_current_player_ranks(self):
        ranks = self.driver.find_elements(by=By.XPATH, value="//div[@id='content-container']/div[2]//div[@class='header']")
        for idx, i in enumerate(ranks[:1]):  # Maybe change to :2 to include flex?
            if "Unranked" in i.text:
                curr_ranks = i.text.split("\n")
                # print(f"Current rank in {curr_ranks[0]} is {curr_ranks[1]}")
                return {self.CURRENT_SEASON: curr_ranks[1]}
            else:
                curr_rank = i.find_element(by=By.XPATH, value="..//div[@class='tier']")
                # print(f"Current rank in {i.text} is {curr_rank.text}")
                return {self.CURRENT_SEASON: curr_rank.text}

    def get_past_player_ranks(self):
        rank_list = self.driver.find_element(by=By.XPATH, value="//div[@id='content-container']/div[2]//table[1]")

        seasons = rank_list.find_elements(by=By.XPATH, value=".//b[@class='season']")
        past_ranks = rank_list.find_elements(by=By.XPATH, value=".//div[@class='rank-item']")
        ranks_by_season = {season.text: rank.text for season, rank in zip(seasons, past_ranks[1:])}
        return ranks_by_season

    def recent_elo(self):
        elo_list = self.driver.find_elements(by=By.CLASS_NAME, value="avg-tier")
        return [e.text for e in elo_list]

    def quit(self):
        print(self)
        self.driver.quit()


if __name__ == '__main__':
    # scraper = OpggScraper("na", "ArCaNeAscension#THICC")  # test for unranked
    # scraper = OpggScraper("na", "soren#wolf")  # test for both ranked
    # scraper = OpggScraper("na", "Oreozx#NA1")  # test for just solo ranked
    # scraper = OpggScraper(link="https://www.op.gg/summoners/na/SpaceDust-balls", auto_scrape=True)
    # scraper = OpggScraper(link="https://www.op.gg/summoners/na/Nation%20Of%20Nugs-NA1", auto_scrape=True)
    player_list = [("na", "ArCaNeAscension#THICC"), ("na", "soren#wolf"), ("na", "Oreozx#NA1"), "https://www.op.gg/summoners/na/SpaceDust-balls", "https://www.op.gg/summoners/na/Nation%20Of%20Nugs-NA1"]
    scraper = OpggScraper(player_list=player_list, auto_scrape=True)
    scraper.quit()
