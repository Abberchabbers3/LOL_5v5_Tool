from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import pandas as pd

class OpggScraper:
    CURRENT_SEASON = "S2025 S1"

    def __init__(self, server: str, player_name: str, link=None):
        self.driver = webdriver.Chrome()
        if link:
            self.player_name = link.split("=")[-1].replace("+", " ").replace("-", "#")
            self.driver.get(link)
        else:
            self.player_name = player_name.replace(" #", "#").replace(" ", "+").replace("#", "-")
            self.driver.get('https://' + server + '.op.gg/summoner/userName=' + self.player_name)
        self.driver.implicitly_wait(1)
        self.player_ranks = {}

    def __str__(self):
        print(self.player_name)
        print(self.player_ranks)

    def scrape(self):
        # Update profile if necessary
        # update_button = driver.find_element(By.XPATH, '//button[text()="Update"]')
        # print(update_button, update_button.text)

        # Scrape players current ranks
        self.player_ranks = self.get_current_player_ranks()

        # Scrape players past ranks
        self.player_ranks.update(self.get_past_player_ranks())
        print(self)

        # Get avg elo of last 20 games
        self.recent_elo()

        self.driver.quit()

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
        pass

if __name__ == '__main__':
    # scraper = OpggScraper("na", "ArCaNeAscension#THICC")  # test for unranked
    # scraper = OpggScraper("na", "soren#wolf")  # test for both ranked
    scraper = OpggScraper("na", "Oreozx#NA1")  # test for just solo ranked
    scraper.scrape()
