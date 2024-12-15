# 네이버 검색 API 예제 - 블로그 검색

from dotenv import load_dotenv

from scrap.naver.NaverNewsScraper import NaverNewsScraper


def main() -> ():
    load_dotenv()
    scraper = NaverNewsScraper()
    result = scraper.fetch_news("삼성전자")
    print(result)

    ## TODO DB저장( 몽고 예상 )
    ## 여기서 랭체인으로 우선, 불필요한 뉴스를 빼달라고 요청하기


if __name__ == '__main__':
    main()
