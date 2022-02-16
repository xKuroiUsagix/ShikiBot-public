import requests
import re
import json
from random import randint
from ShikiParser.Manga import Manga
from ShikiParser.Anime import Anime
from ShikiParser.ParserErrors import TitleNameFormatError, TitleNotFoundError
from bs4 import BeautifulSoup


class ShikiParser:
    USER_AGENTS_FILE = 'ShikiParser/user-agents.json'

    def __init__(self) -> None:
        """
        Sets the main url to: https://shikimori.one.
        """
        self.HEADERS = {'User-Agent': ''}
        self.__main_url = 'https://shikimori.one'

    def search_title(self, title: str, is_anime=True):
        """
        Attributes:
            title {str}: Title name, where words splitted with spaces
            is_anime {bool}: if True title_type is 'anime' else 'manga'

        Returns a new Anime object.
        """
        if not self.is_title_valid(title):
            raise TitleNameFormatError(title)

        search_pattern = title.lower().replace(' ', '+')
        search_url = self.get_search_url(search_pattern, is_anime)

        self.change_user_agent() 
        title_html = requests.get(search_url, headers=self.HEADERS).text
        soup = BeautifulSoup(title_html, 'html.parser')
        title_tag_a = soup.find('a', {'class': 'title'})
        
        if (title_tag_a is None) and not (self.is_already_title(soup, title)):
            raise TitleNotFoundError(title)
        elif self.is_already_title(soup, title):
            return Anime(None, title_html) if is_anime else Manga(None, title_html)
        return Anime(title_tag_a['href']) if is_anime else Manga(title_tag_a['href'])

    def change_user_agent(self):
        """
        Choose different user-agent.
        """
        with open(self.USER_AGENTS_FILE) as file:
            user_agents = json.load(file)
            random_max = len(user_agents)-1
            self.HEADERS['User-Agent'] = user_agents[randint(0, random_max)]['user-agent']

    def get_search_url(self, search_pattern, is_anime):
        """
        Attributes:
        - search_pattern {str}: pattern of title name in form like "word+word+word...".
        - is_anime {bool}: if True than 'anime', else 'manga'.

        Get the search url for anime or manga.
        """
        if is_anime:
            return self.__main_url + f'/animes/order-by/aired_on?search={search_pattern}'
        return self.__main_url + f'/mangas?search={search_pattern}'

    @staticmethod
    def is_already_title(soup: BeautifulSoup, title_name: str):
        """
        Attributes:
        - soup {BeatifulSoup}: prepeared soup with title_html
        - title_name {str}: name of the title

        Return True if title_name in 'h1.text' else False
        """
        return soup.find('h1').text.lower().find(title_name.lower()) != -1

    @staticmethod
    def is_title_valid(title: str):
        """
        Valid title format: word1 + *space* + word2 + *space* + word3 + ...
        """
        # Regex pattern means:
        # "Match str with ((0 or 1 word) + (0 or 1 *space*))...
        # repeat this group 0+ times and ends with (word)"
        return re.fullmatch(r'([a-zA-Zа-яА-Я0-9]+\s{0,1})*[a-zA-Zа-яА-Я0-9]+', title)
