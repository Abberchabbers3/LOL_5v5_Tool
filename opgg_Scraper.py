import time

import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from collections import defaultdict
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from collections import Counter


def convert_to_name(player_data):
    if isinstance(player_data, tuple):
        return player_data[0]
    elif isinstance(player_data, str):
        return player_data.split("/")[-1].replace("%20", " ").replace("-", "#")


class OpggScraper:
    CURRENT_SEASON = "S2025 S1"

    def __init__(self, server="na", player_name="", link="", player_list=None, auto_scrape=False):
        self.link_map = dict()
        self.player_ranks = defaultdict(dict)
        self.player_game_ranks = defaultdict(list)
        self.player_recent_roles = defaultdict(lambda: Counter(top=0, jungle=0, mid=0, adc=0, supp=0))
        self.player_mastery = defaultdict(list)
        self.player_champs = defaultdict(
            lambda: dict(top=Counter(), jungle=Counter(), mid=Counter(), adc=Counter(), supp=Counter()))
        driver_options = Options()
        driver_options.add_argument('--blink-settings=imagesEnabled=false')
        driver_options.add_argument('--disable-javascript')
        self.driver = webdriver.Chrome(options=driver_options)

        if player_name:
            self.add_player_by_name(server, player_name)
        elif link:
            self.add_player_by_link(link)
        elif player_list:
            self.add_players(player_list)

        if auto_scrape:
            self.scrape_all()

    def scrape_all(self):
        for player in self.link_map:
            self.scrape(player, self.link_map[player])

    def add_player_by_name(self, server: str, player_name: str):
        player_name = player_name.replace(" #", "#")
        link = 'https://www.op.gg/summoners/' + server + '/' + player_name.replace(" ", "%20").replace("#", "-")
        self.link_map[player_name] = link

    def add_player_by_link(self, link: str):
        player_name = link.split("/")[-1].replace("%20", " ").replace("-", "#")
        self.link_map[player_name] = link

    def add_players(self, server_player_list):
        for player in server_player_list:
            if isinstance(player, str):
                self.add_player_by_link(player)
            elif isinstance(player, tuple) or isinstance(player, list):
                self.add_player_by_name(player[0], player[1])

    def __str__(self):
        output = ""
        for player in self.link_map:
            output += player + "\n"
            output += str(self.player_ranks[player]) + "\n"
            output += str(self.player_game_ranks[player]) + "\n"
            output += str(self.player_recent_roles[player]) + "\n"
            output += str(self.player_mastery[player]) + "\n"
            output += str(self.player_champs[player]) + "\n"
        return output

    def scrape(self, player, link):
        self.driver.get(link)
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//button//span[text()='Update']"))
        )

        # Update profile if necessary
        self.update_profile(self.driver)

        # Scrape players current ranks
        self.player_ranks[player] = self.get_current_player_ranks(self.driver)

        # Scrape players past ranks
        self.player_ranks[player].update(self.get_past_player_ranks(self.driver))

        # Scrape champ mastery
        self.player_mastery[player] = self.update_player_mastery(self.driver)

        # Get avg elo of last 20 norm games
        self.player_game_ranks[player] = self.recent_elo(self.driver, "NORMAL", player)
        recent_game_roles = self.update_recent_roles(self.driver, "NORMAL", 1, player)
        recent_champs = self.get_recent_champs(self.driver, "NORMAL")

        # Get avg elo of last 20 ranked games
        self.player_game_ranks[player].extend(self.recent_elo(self.driver, "SOLORANKED", player))
        recent_game_roles.extend(self.update_recent_roles(self.driver, "SOLORANKED", 2,  player))
        recent_champs.extend(self.get_recent_champs(self.driver, "NORMAL"))
        for role, champ in zip(recent_game_roles, recent_champs):
            self.player_champs[player][role][champ] += 1

    def update_profile(self, driver):
        update_button = driver.find_element(By.XPATH, '//button//span[text()="Update"]')
        time_since_update = driver.find_element(by=By.CLASS_NAME, value="last-update").text
        # only click if it has been 1+ day since last update
        if 'Available' not in time_since_update and 'minute' not in time_since_update and 'hour' not in time_since_update:
            update_button.click()
            while 'Available' not in time_since_update:
                driver.implicitly_wait(0.1)
                time_since_update = driver.find_element(by=By.CLASS_NAME, value="last-update").text

    def update_player_mastery(self, driver):
        try:
            mastery = driver.find_elements(by=By.XPATH, value="//div[text() = 'Mastery']/..//strong[@class='champion-name']")
            mastery = [m.get_attribute('textContent') for m in mastery]
            return mastery
        except selenium.common.exceptions.NoSuchElementException:
            return []


    def get_current_player_ranks(self, driver):
        try:
            rank = driver.find_element(by=By.XPATH, value="//span[text()='Ranked Solo/Duo']/..")
            if "Unranked" in rank.text:
                curr_ranks = rank.text.split("\n")
                # print(f"Current rank in {curr_ranks[0]} is {curr_ranks[1]}")
                return {self.CURRENT_SEASON: curr_ranks[1]}
            else:
                curr_rank = rank.find_element(by=By.XPATH, value="..//div[@class='tier']")
                # print(f"Current rank in {i.text} is {curr_rank.text}")
                return {self.CURRENT_SEASON: curr_rank.text}
        except selenium.common.exceptions.NoSuchElementException:
            return dict()

    def get_past_player_ranks(self, driver):
        try:
            rank_list = driver.find_element(by=By.XPATH, value="//div[@id='content-container']//table[1]")

            seasons = rank_list.find_elements(by=By.XPATH, value=".//b[@class='season']")
            past_ranks = rank_list.find_elements(by=By.XPATH, value=".//div[@class='rank-item']")
            ranks_by_season = {season.text: rank.text for season, rank in zip(seasons, past_ranks[1:])}
            return ranks_by_season

        except selenium.common.exceptions.NoSuchElementException:
            return dict()

    def change_game_mode(self, driver, game_mode):
        game_mode = game_mode.upper()
        start_url = driver.current_url
        if game_mode in start_url:
            return True
        # First look for the button
        try:
            rank_button = driver.find_element(by=By.XPATH, value=f"//button[@value='{game_mode}']")
            rank_button.click()
        # if not there, click the "Queue Type button and try again"
        except selenium.common.exceptions.NoSuchElementException:
            try:
                rank_button = driver.find_element(by=By.XPATH, value=f"//select[@id='queueType']/option[@value='{game_mode}']")
                rank_button.click()
            except selenium.common.exceptions.NoSuchElementException:
                return False
        # Wait until new page has loaded
        WebDriverWait(driver, 5).until(
            EC.url_contains(game_mode)
        )
        # TODO Its possible for literally nothing to change during this time but the selected button; however this does not mean the rest has loaded
        time.sleep(1)
        return True

    # def change_game_mode(self, driver, game_mode, player_name):
    #     start_url = driver.current_url
    #     if game_mode in start_url:
    #         return True
    #     try:
    #         link = self.link_map[player_name]
    #         driver.get(link+f"?queue_type={game_mode}")
    #         WebDriverWait(self.driver, 5).until(
    #             EC.presence_of_element_located((By.XPATH, "//button//span[text()='Update']"))
    #         )
    #     except selenium.common.exceptions:
    #         return False
    #     return True

    def update_recent_roles(self, driver, game_mode, mode_weight, curr_player_name):
        if not self.change_game_mode(driver, game_mode):
            return []
        try:
            all_players = driver.find_elements(by=By.XPATH, value="//div[@class='summoner-tooltip']//span")
            player_list = [p.get_attribute('textContent') for p in all_players]
            mod_player_name = curr_player_name.split("#")[0]
            player_locs = [((i+1) % 10) % 5 for i, p in enumerate(player_list) if p == mod_player_name]
            # print(f"num {game_mode} games = {len(player_locs)}, total_players = {len(player_list)}")
            roles = ["supp", "top", "jungle", "mid", "adc"]
            recent_games = []
            for game in player_locs:
                recent_games.append(roles[game])
                self.player_recent_roles[curr_player_name][roles[game]] += mode_weight
            return recent_games
        except selenium.common.exceptions.NoSuchElementException:
            return []
        except selenium.common.exceptions.StaleElementReferenceException:
            return self.update_recent_roles(driver, game_mode, mode_weight, curr_player_name)

    def recent_elo(self, driver, game_mode, player):
        if not self.change_game_mode(driver, game_mode):
            return []
        try:
            elo_list = driver.find_elements(by=By.CLASS_NAME, value="avg-tier")
            return [e.text for e in elo_list]
        except selenium.common.exceptions.NoSuchElementException:
            return []
        except selenium.common.exceptions.StaleElementReferenceException:
            return self.recent_elo(driver, game_mode, player)

    def get_recent_champs(self, driver, game_mode):
        if not self.change_game_mode(driver, game_mode):
            return []
        try:
            champs = driver.find_elements(by=By.XPATH,
                                          value="//div[@class='inner']//div[@class='info']//a[@class='champion']//img")
            champs = [c.get_attribute("alt") for c in champs]
            return champs
        except selenium.common.exceptions.NoSuchElementException:
            return []

    def quit_driver(self):
        self.driver.quit()


if __name__ == '__main__':
    # scraper = OpggScraper("na", "ArCaNeAscension#THICC", auto_scrape=True)  # test for unranked
    scraper = OpggScraper("na", "soren#wolf", auto_scrape=True)  # test for both ranked
    # scraper = OpggScraper("na", "Oreozx#NA1")  # test for just solo ranked
    # scraper = OpggScraper(link="https://www.op.gg/summoners/na/SpaceDust-balls", auto_scrape=True)
    # scraper = OpggScraper(link="https://www.op.gg/summoners/na/Nation%20Of%20Nugs-NA1", auto_scrape=True)
    # p_list = [("na", "ArCaNeAscension#THICC"), ("na", "soren#wolf"), ("na", "Oreozx#NA1"),
    #           "https://www.op.gg/summoners/na/SpaceDust-balls", "https://www.op.gg/summoners/na/Nation%20Of%20Nugs-NA1"]
    # p_list.extend(["https://www.op.gg/summoners/na/Clítorís-42069", "https://www.op.gg/summoners/na/Kelso-69420",
    #                "https://www.op.gg/summoners/na/Hexos926-ADC", "https://www.op.gg/summoners/na/ApolloZSL-NA1",
    #                "https://www.op.gg/summoners/na/CpapaSlice-NA1"])
    # p_list = [("na", "Oreozx#NA1"), "https://www.op.gg/summoners/na/whitehaven-111"]
    # scraper = OpggScraper(link="https://www.op.gg/summoners/na/whitehaven-111", auto_scrape=True)
    # scraper = OpggScraper(player_list=p_list, auto_scrape=True)
    print(scraper)
    scraper.quit_driver()
