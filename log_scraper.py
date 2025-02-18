import time
from datetime import datetime
import dateparser
import pandas as pd
import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from collections import defaultdict
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from collections import Counter
"""
A scraper for league of graphs
The match history on this site goes back much farther than op.gg, so it is better for long term data
"""


class LogScraper:
    def __init__(self, player_link, auto_scrape=True):
        self.start_time = time.time()
        pd.set_option('display.width', 400)
        pd.set_option('display.max_columns', 20)
        self.player_link = player_link
        self.player_name = player_link.split("/")[-1].replace("-", "#")
        self.role_list = ["Top", "Jungle", "Mid", "Adc", "Support"]
        driver_options = Options()
        driver_options.add_argument('--blink-settings=imagesEnabled=false')
        driver_options.add_argument('--disable-javascript')
        self.driver = webdriver.Chrome(options=driver_options)
        # load link
        self.driver.get(self.player_link)
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class = 'recentGamesTableHeaderTitle']"))
        )
        if auto_scrape:
            self.scrape()
        self.df = None

    def scrape(self):
        self.load_more()
        print(f"button pressing done after {time.time()-self.start_time} seconds")
        win_lose = [wl.text for wl in self.driver.find_elements(by=By.XPATH, value="//a/div[contains(@class,"
                                                                                   "'victoryDefeatText')]")]
        print(f"win-lose done after {time.time() - self.start_time} seconds", len(win_lose))
        game_mode = [gm.text for gm in
                 self.driver.find_elements(by=By.XPATH, value="//table[contains(@class,'recentGamesTable')]//"
                                                              "td[contains(@class,'resultCellLight')]//"
                                                              "div[contains(@class,'gameMode')]")]
        print(f"game mode done after {time.time() - self.start_time} seconds", len(game_mode))

        def parse_relative_date(time_str):
            parsed_date = dateparser.parse(time_str, settings={'RELATIVE_BASE': datetime.now()})
            return parsed_date.date() if parsed_date else None
        game_date = [parse_relative_date(gd.text) for gd in
                     self.driver.find_elements(by=By.XPATH, value="//table[contains(@class,'recentGamesTable')]//"
                                                                  "td[contains(@class,'resultCellLight')]//"
                                                                  "div[contains(@class,'gameDate')]")]
        print(f"game date done after {time.time() - self.start_time} seconds", len(game_date))

        game_duration = [gd.text for gd in
                     self.driver.find_elements(by=By.XPATH, value="//table[contains(@class,'recentGamesTable')]//"
                                                                  "td[contains(@class,'resultCellLight')]//"
                                                                  "div[contains(@class,'gameDuration')]")]
        print(f"game duration done after {time.time() - self.start_time} seconds", len(game_duration))
        kills = [k.text for k in
                 self.driver.find_elements(by=By.XPATH, value="//table[contains(@class,'recentGamesTable')]//"
                                                              "div[@class='kda']/span[@class = 'kills']")]
        deaths = [d.text for d in
                 self.driver.find_elements(by=By.XPATH, value="//table[contains(@class,'recentGamesTable')]//"
                                                              "div[@class='kda']/span[@class = 'deaths']")]
        assists = [a.text for a in
                 self.driver.find_elements(by=By.XPATH, value="//table[contains(@class,'recentGamesTable')]//"
                                                              "div[@class='kda']/span[@class = 'assists']")]
        #KDA is kills, deaths, and assists
        kdas = [f"{k}/{d}/{a}" for k, d, a in zip(kills, deaths, assists)]
        print(f"kda done after {time.time() - self.start_time} seconds", len(kdas))
        champs_per_game = [c.get_attribute("alt") for c in
                 self.driver.find_elements(by=By.XPATH, value="//table[contains(@class,'recentGamesTable')]//"
                                                              "td[@class='championCellLight']//"
                                                              "img[contains(@class,'champion')]")]
        print(f"champs done after {time.time() - self.start_time} seconds", len(champs_per_game))
        role_groups = self.driver.find_elements(by=By.XPATH, value="//table[contains(@class,'recentGamesTable')]//"
                                                              "td[@class='summonersTdLight']")
        roles = []
        for group in role_groups:
            group_roles = [c.text for c in group.find_elements(by=By.XPATH, value=".//div[contains(@class,'txt ')]")]
            try:
                ind = group_roles.index(self.player_name)
                roles.append(self.role_list[ind % 5])
            except:
                roles.append("None")
        print(f"roles done after {time.time() - self.start_time} seconds", len(roles))
        # roles = [c.text for c in
        #          self.driver.find_elements(by=By.XPATH, value="//table[contains(@class,'recentGamesTable')]//"
        #                                                       "td[@class='summonersTdLight']//"
        #                                                       "div[contains(@class,'txt ')]")]
        # convert role from player list to role base on location in list
        # roles = [self.role_list[(i % 10) % 5] for i, p in enumerate(roles) if p == self.player_name]

        tooltips = [v.get_attribute('tooltip') for v in
                 self.driver.find_elements(by=By.XPATH, value="//table[contains(@class,'recentGamesTable')]//"
                                                              "td[contains(@class,'kdaColumn')]/"
                                                              "a[@class='full-cell']/"
                                                              "div[contains(@class,'display-block')]")]
        # read vision score and cs from tool tip
        vision_score = []
        cs = []
        kp = []
        for tooltip in tooltips:
            if tooltip and "Vision Score: " in tooltip:
                vision_score.append(int(tooltip.split("Vision Score: ")[-1].split("<")[0]))
            else:
                vision_score.append(0)
            if tooltip and "Minions: " in tooltip:
                cs.append(int(tooltip.split("Minions: ")[-1].split("<")[0]))
            else:
                cs.append(0)
            if tooltip and "Kill participation: " in tooltip:
                kp.append(tooltip.split("Kill participation: ")[-1].split("<")[0])
            else:
                kp.append("None")
        print(f"tooltips/vs/cs/kp done after {time.time() - self.start_time} seconds", len(tooltips))

        summoner_spell_groups = self.driver.find_elements(by=By.XPATH, value="//table[contains(@class,'recentGamesTable')]//"
                                                                        "td[@class='championCellLight']")
        grouped_summs = []
        for group in summoner_spell_groups:
            summs = [img.get_attribute("alt") for img in group.find_elements(by=By.XPATH,
                                                                             value=".//img[contains(@class,'spell')]")]
            if len(summs) < 2:
                summs.extend(["None"]*(2-len(summs)))
            grouped_summs.append(summs)
        print(f"summs done after {time.time() - self.start_time} seconds", len(grouped_summs))
        item_groups = self.driver.find_elements(by=By.XPATH, value="//table[contains(@class,'recentGamesTable')]//"
                                                          "td[@class='itemsColumnLight']//div[@class='display-block']")
        grouped_items = []
        wards = ["Farsight Alteration", "Stealth Ward", "Oracle Lens", "Arcane Sweeper", "Poro-Snax"]
        for group in item_groups:
            items = [img.get_attribute("alt") for img in group.find_elements(By.XPATH, ".//img[contains(@class,'item')]")]
            if len(items) == 0:
                items = ["None"]*7
            elif len(items) < 7:
                ward = None
                if items[-1] in wards:
                    ward = items[-1]
                    items[-1] = "None"
                # add Nones until length is 7
                items.extend(["None"]*(7-len(items)))
                if ward:
                    items[-1] = ward
            grouped_items.append(items)
        print(f"item groups done after {time.time() - self.start_time} seconds", len(grouped_items))
        self.df = pd.DataFrame(
            list(zip(win_lose, game_mode, game_date, game_duration, champs_per_game, roles, kdas, cs,
                     vision_score, kp)),
            columns=["win/lose", "game_mode", "game_date", "game_duration", "champion", "role", "KDA", "CS",
                     "Vision Score", "KP"])
        if len(grouped_summs) == len(self.df):
            self.df[['Summoner Spell 1', 'Summoner Spell 2']] = grouped_summs
        else:
            self.df[['Summoner Spell 1', 'Summoner Spell 2']] = grouped_summs[:len(self.df)]
        if len(grouped_items) == len(self.df):
            self.df[['Item 1', 'Item 2', 'Item 3', 'Item 4', 'Item 5', 'Item 6', 'Ward']] = grouped_items
        else:
            self.df[['Item 1', 'Item 2', 'Item 3', 'Item 4', 'Item 5', 'Item 6', 'Ward']] = grouped_items[:len(self.df)]
        print(self.df.tail(10))
        print(self.df.info())
        self.df.to_csv("data_to_analyze.csv", index=False)

    def load_more(self):
        """
        presses the show more button until it is no longer able to
        :return:
        """
        i = 0
        while True:
            try:
                # Wait for the button to be clickable
                button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH,
                                                "//table[contains(@class,'recentGamesTable')]//"
                                                "button[contains(@class, 'see_more')]"))
                )
                # Click
                self.driver.execute_script("arguments[0].click();", button)
                # Wait for loading to complete (could be checking for the button to be disabled)
                WebDriverWait(self.driver, 10).until(
                    EC.invisibility_of_element_located((By.XPATH,
                                                        "//table[contains(@class,'recentGamesTable')]//"
                                                        "button[contains(@class, 'see_more') and @disabled]"))
                )
                i += 1
                print(f"Button has been pressed {i} times")
            except:
                # If the button is no longer found, break the loop
                try:
                    # If button take too long to load, double check its gone and not still loading
                    self.driver.find_element(By.XPATH,
                                             "//table[contains(@class,'recentGamesTable')]//"
                                             "button[contains(@class, 'see_more')]")
                except:
                    print("Exiting loop")
                    break