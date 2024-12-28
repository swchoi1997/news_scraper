# 네이버 검색 API 예제 - 블로그 검색
import os
from datetime import datetime
from typing import List

import google.generativeai as genai
from dotenv import load_dotenv
from langchain.docstore.document import Document
from langchain_google_genai import HarmCategory, HarmBlockThreshold
from langchain_text_splitters import RecursiveCharacterTextSplitter

from db.mongo.MongoDBProperty import MongoDBProperty
from db.mongo.MongoDbObj import MongoDbObj
from scrap.NewsItemContainer import NewsItemContainer
from scrap.naver.NaverNewsItem import NaverNewsItem
from scrap.naver.NaverNewsScraper import NaverNewsScraper


def load_api_keys() -> None:
    os.environ["GOOGLE_API_KEY"] = os.getenv("google_gemini_api_key")


def load_db():
    property = MongoDBProperty(
        host='127.0.0.1',
        port=27027,
        user='haru',
        passwd='haru',
        db='haru_stock')
    obj = MongoDbObj(property)
    mongo = obj.connect()

    return mongo


def main() -> ():
    load_dotenv()
    load_api_keys()
    db = load_db()

    scraper = NaverNewsScraper()
    keyword = "삼성전자"
    result: NewsItemContainer = scraper.fetch_news(keyword)

    # mongo db에 저장
    print("mongo db에 저장")
    dbs = db.get_default_database()
    collection = dbs[keyword]

    from pymongo.errors import BulkWriteError
    try:
        print("START")
        items: List[NaverNewsItem] = result.news_item
        collection.insert_many([item.to_dict() for item in items], ordered=False)
        print("END")
    except BulkWriteError as e:
        print(e.details)

    ## Vector DB에 저장
    print("Vector DB에 저장")
    try:
        i = 0
        for news in result.news_item:
            print("Vector DB에 저장 : " + str(i))
            _id = news.getId()
            text = news.getDescription()
            pub_date = news.getPubDate()
            save_vector_db2(_id, text, pub_date, keyword)
            i += 1

            db.close()

    except Exception as e:
        db.close()
        print(e)

    print("END")
    print("END")
    print("END")
    print("END")


def save_vector_db2(_id: str, text: str, pub_date: datetime, keyword: str):
    load_dotenv()
    load_api_keys()

    import chromadb
    # 1. Chroma 클라이언트/컬렉션 생성 (DB 설정)
    client = chromadb.HttpClient(
        host="localhost",  # 도커 내부에서 포트 매핑했으므로 localhost로 통신
        port=8000
    )

    from slugify import slugify
    slugify_keyword = slugify(keyword, lowercase=True)

    collection = client.get_or_create_collection(name=slugify_keyword)

    recursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100)

    doc = [Document(page_content=text, metadata={"id": _id, "date": pub_date})]

    chunks = recursiveCharacterTextSplitter.split_documents(doc)

    genai.configure(api_key=os.getenv("google_gemini_api_key"))

    for i, row in enumerate(chunks):
        doc_id = f"{row.metadata['id']}_{i}"
        print(doc_id, end="")
        existing_docs = collection.get(ids=[doc_id])

        if existing_docs and len(existing_docs["ids"]) > 0:
            print(" : " + str(existing_docs["ids"]))
            continue
        print()
        if len(row.page_content) <= 0:
            continue
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=row.page_content)

        embedding_vector = result["embedding"]

        collection.upsert(
            documents=[row.page_content],
            embeddings=[embedding_vector],
            # 고유 ID를 위해 uuid 사용 (원하시면 다른 방식을 써도 됨)
            ids=[doc_id],
            # 메타데이터에 원본 뉴스 ID 등을 넣어둠
            metadatas=[{
                "original_id": row.metadata["id"],
                "pub_date": row.metadata["date"].isoformat()
            }]
        )

    ## TODO DB저장( 몽고 예상 )
    ## 여기서 랭체인으로 우선, 불필요한 뉴스를 빼달라고 요청하기


def langchain_test(keyword: str, result: NewsItemContainer) -> None:
    os.environ["GOOGLE_API_KEY"] = os.getenv("google_gemini_api_key")

    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.prompts import ChatPromptTemplate

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a financial news analysis assistant.
    Company Name: {keyword}
    You will be given a list of news articles, each article having 'title' and 'description'.
    Your task is to identify which articles are related to {keyword}'s stock performance.
    An article is considered related if it mentions {keyword} and provides
    context about its stock price, market position, or competitive landscape influencing its valuation.

    Return the results as a Python list of dictionaries, where each dictionary contains two keys:
     - 'index': the index of the article in the given list
     - 'title': the title of the article

    If no articles are related, return an empty list.

    Do not include code fences, explanations, or any text other than the Python list.
    
    Example:
    If the articles given are:
    [{{"title": "삼성전자 주가 상승", "description": "삼성전자의 주가가 오늘 2% 상승했다."}},
     {{"title": "애플 신제품 출시", "description": "애플이 최신 아이폰을 공개했다."}}]
    
    A correct response would be:
    [{{"index": 0, "title": "삼성전자 주가 상승"}}]
    
    Because the first article directly relates to 삼성전자의 stock performance,
    while the second does not.
    """
            ),
            (
                "human",
                """Here is the list of articles (only 'index' and 'title' provided):

{articles}

Please return only the articles that are clearly related to "{keyword}"'s stock.  
**Strict Instructions**:  
1. Only return articles that are directly related to the keyword: "{keyword}".  
2. Use the articles **EXACTLY as provided**. Do not create, invent, or duplicate any articles.  
3. Return the data strictly in this JSON format:  
[
    {{"index": 1, "title": "Article title 1"}},
    {{"index": 2, "title": "Article title 2"}}
]  
4. If no articles match the keyword, return an empty list: `[]`.  
5. Do must not repeat or duplicate any article.  
6. You must not add explanations, comments, or additional text outside of the JSON list.
7. Do must NOT change the provided index. Return the index **exactly as it appears** in the input list.  


**Important**:  
If you violate any of these rules, the response will be invalid.
"""
            ),
        ]
    )

    llm = ChatGoogleGenerativeAI(
        # model="gemini-1.5-flash",
        model="gemini-1.5-flash-8b",
        temperature=0,
        max_retries=2,
        safety_settings={
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        },
    )

    chain = prompt | llm

    articles = [{"title": item.title, "description": item.description} for item in result.news_item]

    # 100개씩 잘라 이중 리스트 만들기
    chunk_size = 100
    chunked_articles = [articles[i:i + chunk_size] for i in range(0, len(articles), chunk_size)]
    response_all = list()
    for chunked_article in chunked_articles:
        response = chain.invoke({"articles": chunked_article, "keyword": keyword})
        response_all.append(response)

    print(response_all)


if __name__ == '__main__':
    main()
    # test()
