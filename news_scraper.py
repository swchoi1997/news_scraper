import os
from datetime import datetime
from typing import List

import google.generativeai as genai
from langchain.docstore.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from db.AbstractDBObj import AbstractDBObj
from scrap.NewsItemContainer import NewsItemContainer
from scrap.NewsScraper import NewsScraper
from scrap.naver.NaverNewsItem import NaverNewsItem


class NewsScrap:
    def __init__(
            self,
            keyword: str,
            save_db: AbstractDBObj,
            vector_db: AbstractDBObj,
            scraper: NewsScraper
    ):
        self.keyword = keyword
        self.save_db = save_db
        self.vector_db = vector_db
        self.scraper = scraper

    def run(self):
        result: NewsItemContainer = self.scraper.fetch_news(self.keyword)
        self.save_origin(result)
        self.save_vector_db(result)


    def save_origin(self, result: NewsItemContainer):
        # mongo db에 저장
        if not self.save_db.IsConnect():
            self.save_db.connect()

        db = self.save_db.connection

        dbs = db.get_default_database()
        collection = dbs[self.keyword]

        from pymongo.errors import BulkWriteError

        try:
            items: List[NaverNewsItem] = result.news_item
            collection.insert_many([item.to_dict() for item in items], ordered=False)

            db.close()
        except BulkWriteError as e:
            print(e.details)
            db.close()
            return


    def save_vector_db(self, result: NewsItemContainer):
        if not self.vector_db.IsConnect():
            self.vector_db.connect()

        ## Vector DB에 저장
        try:
            i = 0
            for news in result.news_item:
                print("Vector DB에 저장 : " + str(i))
                _id = news.getId()
                text = news.getDescription()
                pub_date = news.getPubDate()
                self.save_vector(_id, text, pub_date)
                i += 1
        except Exception as e:
            print(e)

    def save_vector(self, _id: str, text: str, pub_date: datetime):
        client = self.vector_db.connection

        from slugify import slugify
        slugify_keyword = slugify(self.keyword, lowercase=True)

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
                    "pub_date": row.metadata["date"].isoformat(),
                    "ref_count": 0
                }]
            )
