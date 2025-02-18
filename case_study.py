import time

import log_scraper
"""
The purpose of this file is to centralize analysis and data gathering for a case study regarding my performance in League within the current season
This will be done dynamically such that the two editable global variables represent whose data and for how long this analysis will be done.
If you are using this program you agree only to analyze a players data with their express permission
"""
# The league of graphs link of the player to be analyzed
player_link = "https://www.leagueofgraphs.com/summoner/na/ArCaNeAscension-THICC"


class CaseStudy:
    def __init__(self, log_link):
        self.player_link = log_link
        # self.queue_type = "Normal"

    def gather_data(self):
        scraper = log_scraper.LogScraper(self.player_link, auto_scrape=True)
        # scraper.load_more()
        # time.sleep(10)

    def create_database(self):
        pass


if __name__ == '__main__':
    cs = CaseStudy(player_link)
    cs.gather_data()
