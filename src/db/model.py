from typing import List, Optional, Literal, Annotated, Dict, Any
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    BeforeValidator,
    field_serializer,
    AfterValidator,
)
from pydantic_core import CoreSchema
from pydantic_core.core_schema import (
    no_info_wrap_validator_function,
    str_schema,
    to_string_ser_schema,
)
from pydantic.annotated_handlers import GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from bson import ObjectId
from datetime import datetime

from pydantic.json_schema import JsonSchemaValue


# PyObjectId = Annotated[str, AfterValidator(lambda x: str(x))]
# PyObjectId = Annotated[str, BeforeValidator(str)]


class PyObjectId:
    @classmethod
    def validate_object_id(cls, v: Any, handler) -> ObjectId:
        if isinstance(v, ObjectId):
            return v
        s = handler(v)
        if ObjectId.is_valid(s):
            return ObjectId(s)
        else:
            raise ValueError("Invalid ObjectId")

    @classmethod
    def __get_pydantic_core_schema__(cls, source, _handler) -> CoreSchema:
        return no_info_wrap_validator_function(
            function=cls.validate_object_id,
            schema=str_schema(),
            serialization=to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return handler(str_schema())


MongoObjectId = Annotated[str, BeforeValidator(str)]

# class PyObjectId(ObjectId):
#     @classmethod
#     def __get_validators__(cls):
#         yield cls.validate

#     @classmethod
#     def validate(cls, v, *args):
#         print(f"Args: {args}")
#         if not ObjectId.is_valid(v):
#             raise ValueError("Invalid ObjectId")
#         return ObjectId(v)

#     @classmethod
#     def __get_pydantic_json_schema__(
#         cls, core: CoreSchema, handler: GetJsonSchemaHandler
#     ) -> Dict[str, Any]:
#         json_schema = super().__get_pydantic_json_schema__(core, handler)
#         json_schema = handler.resolve_ref_schema(json_schema)
#         json_schema.update(_id=str)
#         return json_schema


class ProductFamily(BaseModel):
    id: Annotated[ObjectId, PyObjectId] = Field(alias="_id")
    name: str = Field(...)
    product_support_page_url: str = Field(...)
    admin_guide_url: Optional[str] = Field(None)
    datasheet_url: Optional[str] = Field(None)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "name": "Catalyst 1200",
                "product_support_page_url": "https://www.cisco.com/c/en/us/support/smb/product-support/small-business/Catalyst-1200.html",
                "admin_guide_url": "https://www.cisco.com/c/en/us/support/smb/product-support/small-business/Catalyst-1200/administration.html",
                "datasheet_url": "https://www.cisco.com/c/en/us/support/smb/product-support/small-business/Catalyst-1200/datasheet.html",
            }
        }


class Article(BaseModel):
    id: Optional[MongoObjectId] = Field(alias="_id", default=None)
    series: List[Annotated[ObjectId, PyObjectId]] = Field(default_factory=list)
    title: str = Field(...)
    document_id: str = Field(...)
    category: Literal[
        "Configuration",
        "Troubleshooting",
        "Install & Upgrade",
        "Maintain & Operate",
        "Design",
    ] = Field(default="Configuration")
    url: str = Field(...)
    objective: Optional[str] = Field(default=None)
    applicable_devices: Optional[List[dict]] = Field(default_factory=list)
    intro: Optional[str] = Field(default=None)
    steps: List[dict] = Field(default_factory=list)
    revision_history: Optional[List[dict]] = Field(default_factory=list)
    type: Literal["Article"] = Field(default="Article")

    class Config:
        arbitrary_types_allowed = True
        populate_by_name = True
        json_encoders = {ObjectId: str}

    @field_serializer("series", when_used="json")
    def serialize_series(self, v: List[MongoObjectId]):
        return [str(ser) for ser in v]


class Video(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        json_encoders={ObjectId: str},
    )

    id: Optional[MongoObjectId] = Field(alias="_id", default=None)
    series: List[MongoObjectId] = Field(default_factory=list)
    title: str = Field(...)
    published_date: datetime = Field(...)
    description: Optional[str] = Field(default=None)
    url: str = Field(...)
    video_id: str = Field(...)
    views: int = Field(default=0)
    likes: int = Field(default=0)
    duration: str = Field(...)
    comments: int = Field(default=0)
    kind: Literal["youtube", "ciscoovp"] = Field(default="youtube")
    tags: List[str] = Field(default_factory=list)
    transcript: Optional[str] = Field(default=None)
    category: str = Field(default="Configuration")
    type: Literal["Video"] = Field(default="Video")
