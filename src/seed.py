import os
import sys

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import json
from pathlib import Path
from db.database import MongoDbClient
from dotenv import load_dotenv, find_dotenv
import pymongo
from datetime import datetime
from pymongo.errors import (
    DuplicateKeyError,
    OperationFailure,
    DocumentTooLarge,
    CollectionInvalid,
)
from bson import ObjectId
from db.model import ProductFamily, Article, Video

load_dotenv(find_dotenv(filename=".env"))

client = MongoDbClient(
    conn_str=os.getenv("MONGO_DB_CONN_STR"),
    username=os.getenv("MONGODB_APP_USER"),
    password=os.getenv("MONGODB_APP_USER_PASSWORD"),
)


############# SEED PRODUCT FAMILY DATA #############
async def seed_product_families():
    index = await client.collections[client.PRODUCT_FAMILIES].create_index(
        [("name", pymongo.ASCENDING)], unique=True
    )
    print(f"Index created: {index}")
    pf = json.load(open(f"{os.getcwd()}/data/schema/product_families.json", "r"))
    print(pf)
    pf_ids = []
    for family in pf:
        try:
            concept = {
                "name": family["family"],
                "admin_guide_url": (
                    family["admin_guide_url"] if family["admin_guide_url"] else None
                ),
                "datasheet_url": (
                    family["datasheet_url"]
                    if isinstance(family["datasheet_url"], list)
                    else [family["datasheet_url"]]
                ),
                "product_support_page_url": family["product_support_page_url"],
                "software_url": (
                    family["software_url"] if family["software_url"] else None
                ),
            }
            product_family = ProductFamily(**concept)
            result = await client.insert_one(
                client.PRODUCT_FAMILIES, product_family.model_dump(by_alias=True)
            )
            if result:
                pf_ids.append(result)
        except DuplicateKeyError as err:
            print(f"A duplicate key error occurred: {err}. Skipping this item.")
            continue
        except OperationFailure as err:
            print(f"An operation failure occurred: {err}")
            continue
        except DocumentTooLarge as err:
            print(f"Document too large: {err}")
            continue
        except CollectionInvalid as err:
            print(f"Validation Error: {err}")
            continue
    return pf_ids


import asyncio

# product_family_ids = asyncio.run(seed_product_families())
# print(product_family_ids)


async def seed_video():
    unique_title_index = await client.collections[client.VIDEOS].create_index(
        [("video_id", pymongo.ASCENDING)],
        unique=True,
        name=client.VIDEOS_YOUTUBE_ID_UNIQUE_INDEX,
    )
    # VIDEOS_SEARCH_INDEX_NAME = "videos_search_index"
    print(f"Index created: {unique_title_index}")
    videos = json.load(open(f"{os.getcwd()}/data/documents/youtube_videos.json", "r"))
    video_ids = []
    for video in videos:
        try:
            pf_name = video["series"]
            pf = await client.get_one_product_family_by_name(pf_name)
            if not pf:
                print(f"Product family {pf_name} not found. Skipping this video.")
                continue
            print(pf)
            video_exists = await client.find_one(
                client.VIDEOS, {"video_id": video["video_id"]}
            )
            if video_exists:
                print(
                    f"Video {video['video_id']} already exists. Adding Product Family ID to series if the Product Family Exists."
                )
                updated_video = await client.update_one(
                    client.VIDEOS,
                    {"_id": video_exists["_id"]},
                    {"$addToSet": {"series": pf["_id"]}},
                )
                video_ids.append(updated_video.upserted_id)
            else:
                video_data = {
                    "series": [pf["_id"]],
                    "title": video["title"],
                    "published_date": datetime.fromisoformat(
                        video["published_date"].replace("Z", "+00:00")
                    ),
                    "description": video["description"],
                    "url": video["url"],
                    "video_id": video["video_id"],
                    "views": int(video["views"]),
                    "likes": int(video["likes"]),
                    "duration": video["duration"],
                    "comments": int(video["comments"]),
                    "kind": "youtube",
                    "tags": video["tags"],
                    "transcript": video["transcript"],
                    "category": video["category"],
                    "type": "Video",
                }
                print(f"Video data: {video_data}")
                created_video_id = await client.insert_one(client.VIDEOS, video_data)

                print(f"New video _id: {created_video_id}")
                video_ids.append(created_video_id)

        except DuplicateKeyError as err:
            print(f"A duplicate key error occurred: {err}. Skipping this item.")
            break
        except OperationFailure as err:
            print(f"An operation failure occurred: {err}")
            continue
        except DocumentTooLarge as err:
            print(f"Document too large: {err}")
            print(f"Video id: {video['id']}")
    return video_ids


# video_ids = asyncio.run(seed_video())
# print(video_ids)


async def seed_articles():
    articles_json = json.load(
        open(f"{os.getcwd()}/data/documents/articles_schema.json", "r")
    )
    # ARTICLES_SEARCH_INDEX_NAME = "articles_search_index"
    # ARTICLES_DOC_ID_UNIQUE_INDEX = "doc_id_unique_index"
    # Create the doc_id index
    doc_id_index = await client.collections[client.ARTICLES].create_index(
        [("document_id", pymongo.ASCENDING)],
        unique=True,
        name=client.ARTICLES_DOC_ID_UNIQUE_INDEX,
    )
    print(f"Index created: {doc_id_index}")
    # We need to do some transformation on the articles data before we can insert it into the database
    for article in articles_json:
        series = article["series"]
        pf = await client.get_one_product_family_by_name(series)
        applicable_devices = article["applicable_devices"]
        for device in article["applicable_devices"]:
            if device["software_link"] is None:
                if pf:
                    device["software_link"] = pf["software_url"]
            if device["datasheet_link"] is None:
                if pf:
                    device["datasheet_link"] = pf["datasheet_url"]
        for step in article["steps"]:
            if "video_src" not in step:
                step["video_src"] = None

    # Now we can insert the articles into the database
    article_ids = []
    for article in articles_json:
        series = article["series"]
        pf = await client.get_one_product_family_by_name(series)
        if not pf:
            print(
                f"Product family {series} not found. Skipping this article {article['title']}."
            )
            continue
        existing_article = await client.find_one(
            client.ARTICLES, {"document_id": article["document_id"]}
        )
        if existing_article:
            print(f"Article {article['document_id']} already exists.")
            updated_article = await client.update_one(
                client.ARTICLES,
                {"_id": existing_article["_id"]},
                {"$addToSet": {"series": pf["_id"]}},
            )
            print(f"Updated article: {updated_article.upserted_id}")
            article_ids.append(updated_article.upserted_id)
        else:
            print(f"Inserting new article: {article['title']}")
            try:
                article_data = {
                    "series": [pf["_id"]],
                    "title": article["title"],
                    "document_id": article["document_id"],
                    "category": article["category"],
                    "url": article["url"],
                    "objective": article["objective"] if article["objective"] else None,
                    "applicable_devices": article["applicable_devices"],
                    "intro": article["intro"] if article["intro"] else None,
                    "steps": article["steps"],
                    "revision_history": (
                        article["revision_history"]
                        if article["revision_history"]
                        else []
                    ),
                    "type": "Article",
                }
                created_article_id = await client.insert_one(
                    client.ARTICLES, article_data
                )
                article_ids.append(created_article_id)
            except DuplicateKeyError as err:
                print(f"A duplicate key error occurred: {err}. Skipping this item.")
                break
            except OperationFailure as err:
                print(f"An operation failure occurred: {err}")
                continue
            except DocumentTooLarge as err:
                print(f"Document too large: {err}")
                continue
            except CollectionInvalid as err:
                print(f"Validation Error: {err}")
                continue

    return article_ids


article_ids = asyncio.run(seed_articles())
print(article_ids)


async def seed_admin_guides():
    # LOOP THROUGH DIRECTORY AND GET ALL FILES
    import os

    topic_text_index = await client.collections[client.ADMIN_GUIDES].create_index(
        [("topic", pymongo.TEXT)], name=client.ADMIN_GUIDES_TOPIC_TEXT_INDEX
    )
    print(f"Index created: {topic_text_index}")
    doc_id_index = await client.collections[client.ADMIN_GUIDES].create_index(
        [("document_id", pymongo.ASCENDING)],
        unique=True,
        name=client.ADMIN_GUIDES_DOC_ID_UNIQUE_INDEX,
    )
    print(f"Index created: {doc_id_index}")
    admin_guides_ids = []
    files = os.listdir(f"{os.getcwd()}/data/admin_guides")
    for file in files:
        print(f"Processing file: {file}")
        admin_guide = json.load(open(f"{os.getcwd()}/data/admin_guides/{file}", "r"))
        for document in admin_guide:
            series = document["metadata"]["concept"]
            pf = await client.get_one_product_family_by_name(series)
            if not pf:
                print(
                    f"Product family {series} not found. Skipping this admin guide {document['metadata']['title']}."
                )
                continue
            try:
                admin_guide = {
                    "series": pf["_id"],
                    "title": document["metadata"]["title"],
                    "topic": document["metadata"]["topic"],
                    "document_id": document["metadata"]["doc_id"],
                    "url": document["metadata"]["source"],
                    "page_content": document["page_content"],
                }
                created_admin_guide_id = await client.insert_one(
                    client.ADMIN_GUIDES, admin_guide
                )
                admin_guides_ids.append((pf["_id"], created_admin_guide_id))

            except Exception as err:
                print(f"{err}. Skipping this item.")
                continue
    return admin_guides_ids


# ag_guides_ids_tuples = asyncio.run(seed_admin_guides())
# print(ag_guides_ids_tuples)
