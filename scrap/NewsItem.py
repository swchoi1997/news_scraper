from abc import ABC
from datetime import datetime

class NewsItem(ABC):
    def __init__(self, title: str, link: str, description: str):
        """
        뉴스 데이터를 담는 클래스.
        """
        self.title = title
        self.link = link
        self.description = description





