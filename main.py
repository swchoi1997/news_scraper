# 네이버 검색 API 예제 - 블로그 검색
import os

from dotenv import load_dotenv

from db.chroma.ChromaDBProperty import ChromaDBProperty
from db.chroma.ChromaDbObj import ChromaDbObj
from db.mongo.MongoDBProperty import MongoDBProperty
from db.mongo.MongoDbObj import MongoDbObj
from news_scraper import NewsScrap
from scrap.naver.NaverNewsScraper import NaverNewsScraper


def load_api_keys() -> None:
    os.environ["GOOGLE_API_KEY"] = os.getenv("google_gemini_api_key")


def load_db():
    return MongoDbObj(MongoDBProperty(
        host='127.0.0.1',
        port=27027,
        user='haru',
        passwd='haru',
        db='haru_stock'))


def load_vector():
    return ChromaDbObj(ChromaDBProperty(
        host='127.0.0.1',
        port=8000,
    ))


def setup():
    load_dotenv()
    os.environ["GOOGLE_API_KEY"] = os.getenv("google_gemini_api_key")


def main() -> ():
    keyword = "삼성전자"

    scrap = NewsScrap(keyword=keyword,
                      save_db=load_db(),
                      vector_db=load_vector(),
                      scraper=NaverNewsScraper())

    scrap.run()


if __name__ == '__main__':
    setup()
    main()
