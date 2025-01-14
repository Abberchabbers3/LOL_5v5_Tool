import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from collections import defaultdict
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class OpggScraper:
    CURRENT_SEASON = "S2025 S1"
    # TODO Add scraping of players highest mastery champs
    # TODO Add scraping of players most recent champs
    # TODO Add scraping of role preferences
    # TODO specialize role preferences into rank per role???
    def __init__(self, server="na", player_name="", link="", player_list=None, auto_scrape=False):
        self.link_map = dict()
        self.player_ranks = defaultdict(dict)
        self.player_game_ranks = defaultdict(list)
        self.driver_options = Options()
        self.driver_options.add_argument('--blink-settings=imagesEnabled=false')
        self.driver_options.add_argument('--disable-javascript')
        self.driver = webdriver.Chrome(options=self.driver_options)

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
        return output

    def scrape(self, player, link):
        self.driver.get(link)
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//button//span[text()='Update']"))
        )

        # Update profile if necessary
        self.update_profile(self.driver)

        # Scrape players current ranks
        player_ranks = self.get_current_player_ranks(self.driver)

        # Scrape players past ranks
        player_ranks.update(self.get_past_player_ranks(self.driver))

        # Get avg elo of last 20 games
        game_ranks = self.recent_elo(self.driver)

        self.player_ranks[player] = player_ranks
        self.player_game_ranks[player] = game_ranks

    def update_profile(self, driver):
        update_button = driver.find_element(By.XPATH, '//button//span[text()="Update"]')
        time_since_update = driver.find_element(by=By.CLASS_NAME, value="last-update").text
        # only click if it has been 1+ hour since last update
        if 'Available' not in time_since_update and 'minute' not in time_since_update:
            update_button.click()
            while 'Available' not in time_since_update:
                driver.implicitly_wait(0.1)
                time_since_update = driver.find_element(by=By.CLASS_NAME, value="last-update").text

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

    def recent_elo(self, driver):
        # TODO click normal and/or ranked and get those games
        try:
            elo_list = driver.find_elements(by=By.CLASS_NAME, value="avg-tier")
            return [e.text for e in elo_list]
        except selenium.common.exceptions.NoSuchElementException:
            return []

    def quit_driver(self):
        self.driver.quit()


if __name__ == '__main__':
    # scraper = OpggScraper("na", "ArCaNeAscension#THICC")  # test for unranked
    # scraper = OpggScraper("na", "soren#wolf", auto_scrape=True)  # test for both ranked
    # scraper = OpggScraper("na", "Oreozx#NA1")  # test for just solo ranked
    # scraper = OpggScraper(link="https://www.op.gg/summoners/na/SpaceDust-balls", auto_scrape=True)
    scraper = OpggScraper(link="https://www.op.gg/summoners/na/Nation%20Of%20Nugs-NA1", auto_scrape=True)
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
