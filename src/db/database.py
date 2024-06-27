from typing import Union, List, Dict, Any
from pymongo.errors import ConfigurationError
from pymongo.typings import _Pipeline, _DocumentType
from bson.raw_bson import RawBSONDocument
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient


class MongoDbClient:

    # Database Name
    DB_NAME = "smb_documents"

    # Database Collections
    ARTICLES = "articles"
    ADMIN_GUIDES = "admin_guides"
    CLI_GUIDES = "cli_guides"
    PRODUCT_FAMILIES = "product_families"
    VIDEOS = "videos"

    COLLECTION_NAMES = [
        ARTICLES,
        ADMIN_GUIDES,
        CLI_GUIDES,
        PRODUCT_FAMILIES,
        VIDEOS,
    ]

    # Database Search and Vector Indexes
    ATLAS_VECTOR_SEARCH_INDEX_NAME = "admin_guide_vector_search"
    ARTICLES_SEARCH_INDEX_NAME = "articles_search_index"
    ARTICLES_DOC_ID_UNIQUE_INDEX = "document_id_unique_index"

    VIDEOS_SEARCH_INDEX_NAME = "videos_search_index"
    VIDEOS_YOUTUBE_ID_UNIQUE_INDEX = "youtube_id_unique_index"

    ADMIN_GUIDES_TOPIC_TEXT_INDEX = "topic_text_index"
    ADMIN_GUIDES_DOC_ID_UNIQUE_INDEX = "document_id_unique_index"

    CLI_GUIDES_COMMAND_NAME_UNIQUE_INDEX = "command_name_unique_index"
    CLI_GUIDES_SPARSE_DESCRIPTION_TEXT_INDEX = "description_text_index"

    PRODUCT_FAMILIES_NAME_UNIQUE_INDEX = "name_1"

    def __init__(self, conn_str: str, username: str, password: str):
        try:
            self.client = AsyncIOMotorClient(
                conn_str.replace("<username>", username).replace("<password>", password)
            )
        except ConfigurationError as err:
            raise ConfigurationError(
                f"Invalid connection string. Got {conn_str.replace('<username>', username).replace('<password>', password)}"
            ) from err

        self.db = self.client[self.DB_NAME]
        self.collections = {name: self.db[name] for name in self.COLLECTION_NAMES}

        self.atlas_vector_search_index_name = "admin_guide_vector_search"
        self.articles_search_index_name = "articles_search_index"

    def _prepare_query(self, query: dict) -> dict:
        if "_id" in query and isinstance(query["_id"], str):
            query["_id"] = ObjectId(query["_id"])
        return query

    async def aggregate(self, collection_name: str, pipeline: _Pipeline) -> List[dict]:
        collection = self.collections[collection_name]
        return await collection.aggregate(pipeline).to_list(None)

    async def insert_one(
        self, collection_name: str, document: Union[_DocumentType, RawBSONDocument]
    ):
        collection = self.collections[collection_name]
        result = await collection.insert_one(document)
        return str(result.inserted_id)

    async def find(self, collection_name: str, query: dict) -> List[Dict[str, Any]]:
        query = self._prepare_query(query)
        collection = self.collections[collection_name]
        return await collection.find(query).to_list(None)

    async def find_one(
        self, collection_name: str, query: dict
    ) -> Union[Dict[str, Any], None]:
        query = self._prepare_query(query)
        collection = self.collections[collection_name]
        return await collection.find_one(query)

    async def update_one(self, collection_name: str, query: dict, update: dict):
        query = self._prepare_query(query)
        collection = self.collections[collection_name]
        result = await collection.update_one(query, update)
        return result

    async def delete_one(self, collection_name: str, query: dict):
        query = self._prepare_query(query)
        collection = self.collections[collection_name]
        result = await collection.delete_one(query)
        return result.deleted_count > 0

    async def get_one_product_family_by_name(self, product_family_name: str):
        query = {"name": product_family_name}
        return await self.find_one(self.PRODUCT_FAMILIES, query)

    async def get_all_product_families(self):
        return await self.find(self.PRODUCT_FAMILIES, {})

    async def get_articles_by_product_family(self, product_family_name: str):
        product_family = await self.get_one_product_family_by_name(product_family_name)
        if not product_family:
            raise ValueError(f"Product Family {product_family_name} not found")
        product_family_id = product_family["_id"]

        query = {"series": {"$in": [product_family_id]}}
        articles = await self.find(self.ARTICLES, query)
        return articles

    async def get_videos_by_product_family(self, product_family_name: str):
        product_family = await self.get_one_product_family_by_name(product_family_name)
        if not product_family:
            raise ValueError(f"Product Family {product_family_name} not found")
        product_family_id = product_family["_id"]

        query = {"series": {"$in": [product_family_id]}}
        videos = await self.find(self.VIDEOS, query)
        return videos

    async def close(self):
        if self.client is not None:
            self.client.close()

    async def get_databases(self):
        return await self.client.list_database_names()
