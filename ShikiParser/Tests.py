import pytest
from ShikiParser import ShikiParser
from ShikiParser import TitleNotFoundError, TitleNameFormatError


class TestShikiParser:
    @pytest.fixture(autouse=True)
    def parser(self):
        self.parser = ShikiParser()

    def test_title_validation(self):
        """
        Test if TitleNameFormatError raises when title name not valid.
        """
        with pytest.raises(TitleNameFormatError):
            self.parser.search_title(title='Not;.valid-title')

    def test_title_not_found(self):
        """
        Test if TitleNotFoundError raises when there is no title with given name.
        """
        with pytest.raises(TitleNotFoundError):
            self.parser.search_title(title='asfjkdgalr')

    def test_only_one_title_exists(self):
        """
        Test if works correct when only one title exists.

        There is a little bug when only one title exists with name like given.
        In this situation shikimori redirect user directly to the title page
        not the search page.
        """
        title_name = 'Claymore'
        anime = self.parser.search_title(title_name)
        expected_title_name = 'Клеймор / Claymore'
        assert anime.name == expected_title_name

    def test_user_agent_change(self):
        """
        Test if User-Agent changes for each title.
        """
        title_names = ['Claymore', 'Made in Abyss', 'Attack on Titan']
        headers = []

        for name in title_names:
            headers.append(self.parser.search_title(name).HEADERS)
        
        assert (headers[0] != headers[1]) or (headers[0] != headers[2])


class TestTitle:
    @pytest.fixture(autouse=True)
    def title(self):
        self.parser = ShikiParser()
        self.title = self.parser.search_title('Made in Abyss')

    def test_title_image(self):
        """
        Test is image url works.
        """
        assert self.title.image_url.find('png') or \
               self.title.image_url.find('jpg')

    def test_title_name(self):
        """
        Test is title name correct.
        """
        assert self.title.name == 'Созданный в Бездне / Made in Abyss'

    def test_title_score_found(self):
        """
        Test is title score correct.
        If this test fails, firstly check this link score:
        https://shikimori.one/animes/z34599-made-in-abyss

        If the score on the page same as title.score
        Change the test expected score.
        """
        assert self.title.score == '8.74'

    def test_title_synopsis(self):
        """
        Test is synopsis correct.
        """
        title_synopsis = self.title.synopsis()
        expected_start = 'Человечество всегда тяготело к изучению неизведанного'
        expected_end = 'Бездну, Бездна в ответ пристально глядит на тебя?'
        assert title_synopsis.startswith(expected_start) and \
               title_synopsis.endswith(expected_end)

    def test_title_genres(self):
        """
        Test is genres correct.
        """
        expected = ['Фантастика', 'Приключения', 'Детектив', 'Драма', 'Фэнтези']
        assert self.title.genres == expected
