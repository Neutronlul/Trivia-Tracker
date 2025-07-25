from .base_scraper import BaseScraper
import re
from datetime import datetime


class TriviaScraper(BaseScraper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.doneScraping = False

    def _extractData(self, soup, page_data=None):
        if page_data is None:
            page_data = {}

        # check if page has no instances
        if not soup.find("div", class_="venue_recap"):
            print("No instances found on this page; stopping scrape.")
            self.doneScraping = True
            return page_data

        for instance in soup.find_all("div", class_="venue_recap"):
            # get date
            rawDate = (
                instance.find("div", class_="recap_meta")
                .find(string=re.compile(r"(?:[A-Z][a-z]{2} ){2}\d{1,2} \d{4}"))
                .strip()
            )

            # format date
            formattedDate = datetime.strptime(rawDate, "%a %b %d %Y")

            print(f"Scraping data for {formattedDate.strftime('%Y-%m-%d')}")

            # if this week's data is already in the db, return
            if formattedDate.date() <= self.break_flag:
                print(
                    f"Stopping scrape at {formattedDate.strftime('%Y-%m-%d')}, already in database."
                )
                self.doneScraping = True
                break

            # get quizmaster
            qm = (
                instance.find("div", class_="recap_meta")
                .find(string=re.compile(r"by Quizmaster"))
                .replace("by Quizmaster", "")
                .strip()
            )

            # create teams from table
            teams = []
            for team in (
                instance.find("table", class_="recap_table")
                .find("tbody")
                .find_all("tr")
            ):
                # get team name
                teamName = team.find_all("td")[2].text.strip()

                # get team id; sometimes absent
                try:
                    teamID = int(team.find_all("td")[1].text.strip())
                except:
                    teamID = None

                # get team score
                teamScore = int(team.find_all("td")[3].text.strip())

                # construct team list
                teams.append(
                    {
                        "name": teamName,
                        "team_id": teamID,
                        "score": teamScore,
                    }
                )

            # append data from instance to page_data
            page_data[formattedDate] = {
                "quizmaster": qm,
                "teams": teams,
            }

        return page_data

    def scrape(self):
        pageCounter = 0
        page_data = {}
        while True:
            pageCounter += 1
            soup = self._fetchPage(self.base_url + "?pg=" + str(pageCounter))
            page_data = self._extractData(soup, page_data)
            print(f"Scraped page {pageCounter} with {len(page_data)} total weeks")
            if self.doneScraping:
                break
        return page_data
