import http.client
from abc import ABC, abstractmethod
from typing import List, Any

from scrap.NewsItemContainer import NewsItemContainer


class NewsScraper(ABC):

    @abstractmethod
    def fetch_news(self, query: str) -> NewsItemContainer:
        pass

    @abstractmethod
    def parse_response(self, response: List[Any]) -> NewsItemContainer:
        pass
