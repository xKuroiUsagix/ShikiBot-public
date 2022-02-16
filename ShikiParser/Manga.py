import requests
import json
from random import randint
from bs4 import BeautifulSoup


class Manga:
    USER_AGENTS_FILE = 'ShikiParser/user-agents.json'

    def __init__(self, title_url: str, title_html=None) -> None:
        self.HEADERS = {'User-Agent': ''}
        self.change_user_agent()
        if title_html is None:
            self.url = title_url
            self.__html = requests.get(title_url, headers=self.HEADERS).text
        else:
            self.__html = title_html

        self.__soup = BeautifulSoup(self.__html, 'html.parser')
        self.__name = self.__soup.find('h1').text
        self.image_url = self.__soup.find('img')
        self.score = self.__soup.find('div', {'class': 'score-value'})
        self.genres = self.__soup.find_all('span', class_='genre-ru')
        
    @property
    def name(self):
        return self.__name

    @property
    def image_url(self):
        return self.__image_url

    @property
    def score(self):
        return self.__score

    @property
    def genres(self):
        return self.__genres

    @score.setter
    def score(self, score_html):
        self.__score = 0
        if score_html:
            self.__score = score_html.text

    @genres.setter
    def genres(self, genres):
        """
        Set the genres from soup if not None
        Else set the empty list
        """
        self.__genres = []
        if genres:
            for genre in genres:
                self.__genres.append(genre.text)


    @image_url.setter
    def image_url(self, image_html):
        """
        Set the image by given <img> tag
        If givent html is None set to default img
        """
        self.__image_url = r'https://www.google.com/url?sa=i&url=https%3A%2F%2F4pda.ru%2Fforum%2Findex.php%3Fshowtopic%3D903970&psig=AOvVaw2K6hTbV197cQPE07_kcg3_&ust=1615993649391000&source=images&cd=vfe&ved=0CAIQjRxqFwoTCICu0M2Lte8CFQAAAAAdAAAAABAI'
        if image_html:
            self.__image_url = image_html['src']


    def synopsis(self):
        """
        Search title synopsis.
        If not found returns an empty string
        """
        synopsis = self.__soup.find('div', {'class': 'b-text_with_paragraphs'})
        if synopsis:
            return synopsis.text
        return ''


    def change_user_agent(self):
        """
        Choose different user-agent.
        """
        with open(self.USER_AGENTS_FILE) as file:
            user_agents = json.load(file)
            random_max = len(user_agents)-1
            self.HEADERS['User-Agent'] = user_agents[randint(0, random_max)]['user-agent']
