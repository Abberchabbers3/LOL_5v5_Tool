import time

import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from collections import defaultdict
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from collections import Counter


class OpggScraper:
    CURRENT_SEASON = "S2025 S1"

    def __init__(self, server="na", player_name="", link="", player_list=None, auto_scrape=False):
        """
        Creates a scraper object that will open op.gg links and collect player information
        Only one of player_name, link, and player_list is required to add players to the scraper queue upon creation
        :param server: The server a player plays on, default is north america server
        :param player_name: The name of the player ot be added
        :param link: The direct op.gg link of the player to add
        :param player_list: A list of players in tuple (server,player_name) or link form
        :param auto_scrape: Whether the scraper will start as soon as its made
        """
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
        """
        Scrapes each player one at a time
        :return:
        """
        for player in self.link_map:
            self.scrape(player, self.link_map[player])

    def add_player_by_name(self, server: str, player_name: str):
        """
        Adds player to link_map by server and player_name
        :param server: the server the player uses i.e. "na" or "euw"
        :param player_name: The name and tag of the play in the form name#tag
        :return:
        """
        player_name = player_name.replace(" #", "#")
        link = 'https://www.op.gg/summoners/' + server + '/' + player_name.replace(" ", "%20").replace("#", "-")
        self.link_map[player_name] = link

    def add_player_by_link(self, link: str):
        """
        Adds player to link_map directly using the link; also parses the player's name from the link
        :param link: valid op.gg link of form: https://www.op.gg/summoners/server/name-tag
        :return:
        """
        player_name = link.split("/")[-1].replace("%20", " ").replace("-", "#")
        self.link_map[player_name] = link

    def add_players(self, server_player_list):
        """
        Adds a list of players parsing if they are a tuple or link
        :param server_player_list: A list of player information in the form of rank,name tuples or valid link strs
        :return:
        """
        for player in server_player_list:
            if isinstance(player, str):
                self.add_player_by_link(player)
            elif isinstance(player, tuple) or isinstance(player, list):
                self.add_player_by_name(player[0], player[1])

    def __str__(self):
        """
        Outputs list of scraped players and information in str form
        :return:
        """
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
        """
        Scrapes op.gg link using selenium web scraping
        :param player: name of the player to be scraped
        :param link: link to the player's op.gg
        :return:
        """
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
        """
        Presses the update button on a users profile if it has been more than one hour since the last update
        :param driver: The currently in use selenium driver
        :return:
        """
        update_button = driver.find_element(By.XPATH, '//button//span[text()="Update"]')
        time_since_update = driver.find_element(by=By.CLASS_NAME, value="last-update").text
        # only click if it has been 1+ day since last update
        if 'Available' not in time_since_update and 'minute' not in time_since_update and 'hour' not in time_since_update:
            update_button.click()
            while 'Available' not in time_since_update:
                driver.implicitly_wait(0.1)
                time_since_update = driver.find_element(by=By.CLASS_NAME, value="last-update").text

    def update_player_mastery(self, driver):
        """
        Gathers champion mastery for a players most played champions
        :param driver: The currently in use selenium driver
        :return: returns list of most mastered champions
        """
        try:
            mastery = driver.find_elements(by=By.XPATH, value="//div[text() = 'Mastery']/..//strong[@class='champion-name']")
            mastery = [m.get_attribute('textContent') for m in mastery]
            return mastery
        except selenium.common.exceptions.NoSuchElementException:
            return []


    def get_current_player_ranks(self, driver):
        """
        Scrapes data regarding most recent player rank
        :param driver: The currently in use selenium driver
        :return: dict representing each players season mapped to their rank that season
        """
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
        """
        Scrapes data regarding player ranks over time
        :param driver: The currently in use selenium driver
        :return: dict representing each players season mapped to their rank that season
        """
        try:
            rank_list = driver.find_element(by=By.XPATH, value="//div[@id='content-container']//table[1]")

            seasons = rank_list.find_elements(by=By.XPATH, value=".//b[@class='season']")
            past_ranks = rank_list.find_elements(by=By.XPATH, value=".//div[@class='rank-item']")
            ranks_by_season = {season.text: rank.text for season, rank in zip(seasons, past_ranks[1:])}
            return ranks_by_season

        except selenium.common.exceptions.NoSuchElementException:
            return dict()

    def change_game_mode(self, driver, game_mode):
        """
        Changes the game mode to selected game_mode name
        :param driver: The currently in use selenium driver
        :param game_mode: str Name of the game mode to swap to
        :return: False if game_mode not found, True if successful tab switch
        """
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
        # Based on the design of the website it is theoretically possible for nothing to change besides the url
        # However a url change does not mean the page is fully loaded so need to manually sleep
        # Tab shouldn't take this long to load but sleep for full second for safety
        time.sleep(1)
        return True


    def update_recent_roles(self, driver, game_mode, mode_weight, curr_player_name):
        """
        Updates the amount of time a player has played a champion over the past twenty games within a game_mode
        This function will re-run itself if the tab takes too long to update causing an error
        :param driver: The currently in use selenium driver
        :param game_mode: The game_mode tab to try and scrape
        :param mode_weight: The amount of weight the games in this mode have, My code uses 1 for norm and 2 for ranked
        i.e. are ranked or norm games more important?
        :param curr_player_name: Name of the current player we are scraping
        :return: Updates dict of player name to role and champions in place; returns empty list if failed
        """
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
        """
        Scrapes average elo from the past twenty games
        This function will re-run itself if the tab takes too long to update causing an error
        :param driver: The currently in use selenium driver
        :param game_mode: target game_mode name to scrape
        :param player: The name of the current player
        :return: List of elo values i.e. Gold 3, Bronze 1, etc.
        """
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
        """
        Scrapes and returns a list of the 20 most recent champs a player has played in a given game mode
        :param driver: The currently in use selenium driver
        :param game_mode: target game_mode name to scrape
        :return:
        """
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
        """
        Quits the driver to save resources
        :return:
        """
        self.driver.quit()


if __name__ == '__main__':
    # Short scraper test for demonstration purposes
    scraper = OpggScraper("na", "ArCaNeAscension#THICC", auto_scrape=True)  # test for unranked
    print(scraper)
    scraper.quit_driver()
