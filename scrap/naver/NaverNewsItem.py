from datetime import datetime
from enum import Enum
from typing import Dict

from scrap.NewsItem import NewsItem


class NewsKeys(Enum):
    TITLE = "title"
    LINK = "link"
    DESCRIPTION = "description"
    ORIGINAL_LINK = "originallink"
    PUB_DATE = "pubDate"


class NaverNewsItem(NewsItem):
    def __init__(
            self,
            title: str,
            link: str,
            description: str,
            original_link: str,
            pub_date: datetime
    ):
        super().__init__(title, link, description)
        self.original_link = original_link
        self.pub_date = pub_date

    @classmethod
    def from_dict(cls, data: Dict[str, str], date_format: str):
        """
        딕셔너리를 받아 NaverNewsItem 객체를 생성하는 클래스 메서드
        """
        return cls(
            title=data.get(NewsKeys.TITLE.value),
            link=data.get(NewsKeys.LINK.value),
            description=data.get(NewsKeys.DESCRIPTION.value),
            original_link=data.get(NewsKeys.ORIGINAL_LINK.value),
            pub_date=datetime.strptime(data.get(NewsKeys.PUB_DATE.value), date_format) if data.get(NewsKeys.PUB_DATE.value) else None
        )
