from ShikiParser.Manga import Manga


class Anime(Manga):

    def __init__(self, title_url: str, title_html=None) -> None:
        super().__init__(title_url, title_html)

    def screenshots(self):
        pass
