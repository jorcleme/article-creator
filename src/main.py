import uvicorn
from fastapi import (
    FastAPI,
    BackgroundTasks,
    Request,
    status,
    HTTPException,
    Header,
    Depends,
)
from fastapi.security.oauth2 import OAuth2PasswordBearer
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from bson import ObjectId
from typing import List, Optional, Union
import time
import json
import os
import sys
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta, timezone
from urllib3.util import parse_url
import logging
import logging.config
from dotenv import find_dotenv, load_dotenv
from src.db.database import MongoDbClient
from src.db.model import ProductFamily, Article, Video
from pydantic import BaseModel, Field


load_dotenv(find_dotenv(filename=".env"))


app = FastAPI(title="Cisco SMB Devs Document API", version="1.0.0", docs_url="/docs")

bearer_scheme = HTTPBearer()
SECRET_KEY = "46519bef7670c9132cbe58125d09066eced61feb856cdfa817503d98ded8929b"
ALGORITHM = "HS256"
TIME_TO_LIVE_MINUTES = 60 * 24
REFRESH_TOKEN_EXPIRE_DAYS = 30
origins = [
    "http://localhost:*",
    "https://*.cisco.com",
    "http://*.cisco.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # allow_origin_regex="https://.*\.cisco\.com",
)

logging.basicConfig(
    stream=sys.stdout,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    encoding="utf-8",
    level=logging.DEBUG,
    datefmt="%m/%d/%Y %I:%M:%S %p",
    force=True,
)
logging.debug("Server Started")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)


@app.on_event("startup")
async def startup_db_client():
    app.state.mongodb_client = MongoDbClient(
        conn_str=os.getenv("MONGO_DB_CONN_STR"),
        username=os.getenv("MONGODB_APP_USER"),
        password=os.getenv("MONGODB_APP_USER_PASSWORD"),
    )


@app.on_event("shutdown")
async def shutdown_db_client():
    if app.state.mongodb_client is not None:
        await app.state.mongodb_client.close()


@app.get("/")
async def index():
    return {"message": "Hello Codeshift!"}


def authenticate_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Access Token"
        )
    return payload


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt


class Secrets(BaseModel):
    secret_key: str


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None


@app.post("/api/v1/token/create")
async def create_token(secrets: Secrets, response_model=Token):
    if secrets.secret_key == SECRET_KEY:
        access_token_expires = timedelta(minutes=TIME_TO_LIVE_MINUTES)
        access_token = create_access_token(
            data={"sub": "access_token"}, expires_delta=access_token_expires
        )
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = create_access_token(
            data={"sub": "refresh_token"}, expires_delta=refresh_token_expires
        )
        return Token(
            access_token=access_token, token_type="bearer", refresh_token=refresh_token
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Secret Key"
        )


@app.post("/api/v1/token/refresh")
async def refresh_token(secrets: Secrets, response_model=Token):
    if secrets.secret_key == SECRET_KEY:
        access_token_expires = timedelta(minutes=TIME_TO_LIVE_MINUTES)
        access_token = create_access_token(
            data={"sub": "access_token"}, expires_delta=access_token_expires
        )
        rt_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        rt = create_access_token(
            data={"sub": "refresh_token"}, expires_delta=rt_expires
        )
        return Token(access_token=access_token, token_type="bearer", refresh_token=rt)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Secret Key"
        )


@app.middleware("http")
async def process_time(request, call_next):
    start_time = int(time.time())
    response = await call_next(request)
    process_time = int(time.time()) - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


######### PRODUCT FAMILY NAME API #########
class FamilyName(BaseModel):
    family_name: str


class GetArticleResponse(BaseModel):
    articles: List[Article]


@app.post(
    "/api/v1/articles/by-family", response_model=GetArticleResponse, tags=["articles"]
)
async def get_articles_by_product_family(
    family: FamilyName, has_access: dict = Depends(authenticate_user)
):
    pf = family.family_name
    articles = await app.state.mongodb_client.get_articles_by_product_family(pf)

    return {"articles": articles}


class GetVideoResponse(BaseModel):
    videos: List[Video]


@app.post("/api/v1/videos/by-family", response_model=GetVideoResponse, tags=["videos"])
async def get_videos_by_product_family(family: FamilyName):
    pf = family.family_name
    videos = await app.state.mongodb_client.get_videos_by_product_family(pf)
    return {"videos": videos}


class GetArticlesVideosResponse(BaseModel):
    articles: List[Article]
    videos: List[Video]


@app.post(
    "/api/v1/all-content/by-family",
    tags=["all-content-by-family", "articles", "videos"],
    response_model=GetArticlesVideosResponse,
)
async def get_all_content(
    family: FamilyName, has_access: dict = Depends(authenticate_user)
):
    pf = family.family_name
    print(f"Product Family: {pf}")
    articles = await app.state.mongodb_client.get_articles_by_product_family(pf)
    videos = await app.state.mongodb_client.get_videos_by_product_family(pf)
    return {"articles": articles, "videos": videos}


class ContentIds(BaseModel):
    article_ids: List[str] = Field(default_factory=list)
    video_ids: List[str] = Field(default_factory=list)


@app.post("/api/v1/update-content/by-family/{family_name}")
async def update_content_by_family(
    family_name: str, content_ids: List[ContentIds] = []
):
    pass


def handle_objectid(data):
    if isinstance(data, list):
        return [handle_objectid(item) for item in data]
    elif isinstance(data, dict):
        return {key: handle_objectid(value) for key, value in data.items()}
    elif isinstance(data, ObjectId):
        return str(data)
    else:
        return data


@app.get("/api/v1/search/{collection_type}")
async def search_collection(collection_type: str, query: str):
    pipelines_to_execute_tuples = []
    if collection_type == "article":
        pipeline = [
            {
                "$search": {
                    "index": "articles_search_index",
                    "compound": {
                        "must": [
                            {
                                "in": {
                                    "path": "series",
                                    "value": [ObjectId("664fb6852fc158b8f2ee1f62")],
                                }
                            }
                        ],
                        "should": [
                            {"text": {"query": f"{query}", "path": {"wildcard": "*"}}}
                        ],
                    },
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "title": 1,
                    "objective": 1,
                    "intro": 1,
                    "steps": 1,
                    "applicable_devices": 1,
                    "document_id": 1,
                    "url": 1,
                    "type": 1,  # "Article"
                    "score": {"$meta": "searchScore"},
                }
            },
            {
                "$limit": 7,
            },
        ]
        pipelines_to_execute_tuples.append(("articles", pipeline))
    elif collection_type == "video":
        pipeline = [
            {
                "$search": {
                    "index": "videos_search_index",
                    "compound": {
                        "must": [
                            {
                                "in": {
                                    "path": "series",
                                    "value": [ObjectId("664fb6852fc158b8f2ee1f62")],
                                }
                            }
                        ],
                        "should": [
                            {"text": {"query": f"{query}", "path": {"wildcard": "*"}}}
                        ],
                    },
                }
            },
            {
                "$project": {
                    "score": {"$meta": "searchScore"},
                }
            },
            {
                "$limit": 7,
            },
        ]
        pipelines_to_execute_tuples.append(("videos", pipeline))
    else:
        # Collection is all and we need to search both articles and videos
        articles_pipeline = [
            {
                "$search": {
                    "index": "articles_search_index",
                    "compound": {
                        "must": [
                            {
                                "in": {
                                    "path": "series",
                                    "value": [ObjectId("664fb6852fc158b8f2ee1f62")],
                                }
                            }
                        ],
                        "should": [
                            {"text": {"query": f"{query}", "path": {"wildcard": "*"}}}
                        ],
                    },
                }
            },
            {
                "$project": {
                    "score": {"$meta": "searchScore"},
                }
            },
            {
                "$limit": 7,
            },
        ]
        videos_pipeline = [
            {
                "$search": {
                    "index": "videos_search_index",
                    "compound": {
                        "must": [
                            {
                                "in": {
                                    "path": "series",
                                    "value": [ObjectId("664fb6852fc158b8f2ee1f62")],
                                }
                            }
                        ],
                        "should": [
                            {"text": {"query": f"{query}", "path": {"wildcard": "*"}}}
                        ],
                    },
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "title": 1,
                    "description": 1,
                    "score": {"$meta": "searchScore"},
                }
            },
            {
                "$limit": 7,
            },
        ]
        pipelines_to_execute_tuples.append(("articles", articles_pipeline))
        pipelines_to_execute_tuples.append(("videos", videos_pipeline))

    results = []
    for name, pipeline in pipelines_to_execute_tuples:
        aggregation = await app.state.mongodb_client.aggregate(name, pipeline)
        aggregation = handle_objectid(aggregation)
        results.extend(aggregation)

    return {"results": results}

    # pipeline = (
    #     [
    #         {
    #             "$search": {
    #                 "index": "articles_search_index",
    #                 "text": {"query": f"{query}", "path": "title"},
    #             }
    #         },
    #         {
    #             "$project": {
    #                 "_id": 1,
    #                 "title": 1,
    #                 "objective": 1,
    #                 "intro": 1,
    #                 "steps": 1,
    #             }
    #         },
    #     ],
    # )


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
