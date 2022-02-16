class TitleNameFormatError(Exception):
    """
    Should be raised when title name given in bad format.
    """
    def __init__(self, title='') -> None:
        self.title = title

    def __str__(self) -> str:
        return f'Title {self.title} has wrong format.'


class TitleNotFoundError(Exception):
    """
    Should be raised when no title found.
    """
    def __init__(self, title=''):
        self.title = title

    def __str__(self):
        return f'Title {self.title} not found.'
