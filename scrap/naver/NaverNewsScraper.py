import http.client
import json
import urllib.request
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from typing import List, Any, Dict

from config.NcpConfig import NcpConfig
from config.NcpNewsParams import NcpNewsParams
from scrap.NewsItemContainer import NewsItemContainer
from scrap.NewsScraper import NewsScraper
from scrap.naver.NaverNewsItem import NaverNewsItem


class NaverNewsScraper(NewsScraper):
    def __init__(self):
        self.ncpConfig: NcpConfig = NcpConfig()
        self.scrap_max_cnt: int = self.ncpConfig.ncp_properties.getMaxScrapCount()

    def fetch_news(
            self,
            query: str,
            scrap_std_time: datetime = datetime.now(tz=timezone.utc) - timedelta(days=1),
    ) -> NewsItemContainer:
        """
        :param query:           검색어
        :param scrap_std_time:  조회 기준 시간 (UTC)
        """
        # 스크랩 결과를 담을 변수
        scrap_result: List[Dict] = list()

        # 스크랩 을 가능할떄 까지 진행
        current_scarp_max_cnt = 0
        # 스크랩 시작 지점 선언
        scrap_start_index = 1
        while current_scarp_max_cnt < self.scrap_max_cnt:
            # request 요청 생성
            request: urllib.request.Request = self.ncpConfig.getNcpRequest(NcpNewsParams(query, scrap_start_index))
            response: http.client.HTTPResponse = urllib.request.urlopen(request)
            if HTTPStatus.OK != response.getcode():
                break

            response_doby = response.read()
            newses = json.loads(response_doby.decode("utf-8"))  # utf-8로 디코딩한 결과 반환
            scrap_result.append(newses)

            # 만약 더이상 진행하지 않아도 된다고 판단된다면, 종료
            if not self.is_scraping_needed(newses, scrap_std_time):
                break

            current_scarp_max_cnt += 1
            scrap_start_index += 100

        return self.parse_response(scrap_result)

    def parse_response(self, responses: List[Any]) -> NewsItemContainer:
        parsed_newses = list()

        for newses in responses:
            scrap_news_infos = newses["items"]
            for scrap_news_info in scrap_news_infos:
                parsed_newses.append(
                    NaverNewsItem.from_dict(scrap_news_info, self.ncpConfig.ncp_properties.getDateFormat()))

        container = NewsItemContainer(parsed_newses)
        return container


    def is_scraping_needed(self, newses: Dict[Any, Any], scrap_std_time: datetime) -> bool:
        """
        조건 1 : 조회 시점으로부터 -24시간 뉴스만 수집
                예시 :
                  기준     : 24.12.02 09:00:00
                  수집 기준 : 24.12.01 09:00:00
                  수집 기준보다 이전 시간이 조회에 포함되어있다면, 더이상 조회하지 않음!
        조건 2 : 조회 시점으로부터, -24 시간 뉴스만 수집했는데, 조회했을때 100개가 안될 경우
                100개가 안된다는 건 뉴스가 별로 없다는걸 의미! -> 더이상 조회하지 않아도 된다.

        :param newses:
        :param response:        NCP response
        :param scrap_std_time:  기준 시간
        :return: 계속 조회를 진행할지 여부
        """

        # 조건 1
        scrap_news_info = newses["items"]
        oldest_news_date_str: str = scrap_news_info[-1]["pubDate"]
        oldest_news_date: datetime = datetime.strptime(oldest_news_date_str, self.ncpConfig.ncp_properties.getDateFormat())
        oldest_news_date_utc: datetime = oldest_news_date.astimezone(tz=timezone.utc)

        # 만약 기준시간보다, 조회해왔을때, 가장 오래된 뉴스의 시간이 이전 시간이면, 그만 조회해도됨
        if oldest_news_date_utc < scrap_std_time:
            return False

        # 조건 2
        if len(scrap_news_info) != 100:
            return False


        return True
