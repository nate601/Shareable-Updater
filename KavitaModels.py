from dataclasses import dataclass
from typing import Any
import httpx
from functools import cached_property
from datetime import datetime
from pydantic import (
    BaseModel,
    Field,
    AliasChoices,
    computed_field,
    field_validator,
    ValidationInfo,
)
from setec_secrets import GetVendorSecret

API_KEY = GetVendorSecret("kavita", "api_key")

# TODO: update python and use template literal?
# TODO: move base url to getvendorsecret call so I can change it later
ON_DECK_ENDPOINT = "https://kavita.n8.pub/api/Series/on-deck"
AUTH_ENDPOINT = "https://kavita.n8.pub/api/Plugin/authenticate"
SERIES_VOLUMES_ENDPOINT = "https://kavita.n8.pub/api/Series/volumes"
SERIES_METADATA_ENDPOINT = "https://kavita.n8.pub/api/Series/metadata"
SERIES_DATA_ENDPOINT = "https://kavita.n8.pub/api/Series/"
SERIES_SEARCH_ENDPOINT = "https://kavita.n8.pub/api/Series/v2"


def GetToken():
    o = {"apiKey": API_KEY, "pluginName": "sharablesUpdater"}
    resp = httpx.post(AUTH_ENDPOINT, params=o)
    resp = resp.json()
    assert resp["token"], "Unable to fetch token"
    return resp["token"]


TOKEN = GetToken()
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
client = httpx.Client(headers=HEADERS)


class Chapter(BaseModel):
    id: int
    titleName: str
    sortOrder: int
    lastReadingProgressUtc: datetime | None

    @computed_field
    @cached_property
    def lastReadingProgressLocal(self) -> datetime | None:
        if self.lastReadingProgressUtc:
            return datetime.astimezone(self.lastReadingProgressUtc)
        return None

    @field_validator("lastReadingProgressUtc", mode="after")
    @classmethod
    def validate_dttm(cls, input: datetime | None) -> datetime | None:
        if input is None:
            return None
        if input == datetime(1, 1, 1, 0, 0):
            return None
        return input


class Volume(BaseModel):
    id: int
    name: str | None
    pages: int
    pagesRead: int
    wordCount: int
    chapters: list[Chapter]

    @computed_field
    @cached_property
    def completed(self) -> bool:
        return self.pagesRead >= self.pages

    @computed_field
    @cached_property
    def lastReadingProgressUtc(self) -> datetime | None:
        return max(
            [
                chapter.lastReadingProgressUtc
                for chapter in self.chapters
                if chapter.lastReadingProgressUtc is not None
            ],
            default=None,
        )

    @computed_field
    @cached_property
    def lastReadingProgressLocal(self) -> datetime | None:
        return max(
            [
                chapter.lastReadingProgressLocal
                for chapter in self.chapters
                if chapter.lastReadingProgressLocal is not None
            ],
            default=None,
        )

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, input: Any, info: ValidationInfo) -> str:
        if not isinstance(info.context, dict):
            raise ValueError("Volume context is passed as null!")
        seriesName = info.context.get("seriesName")
        if isinstance(input, str):
            if input.isdigit():
                if (
                    int(input) >= 1
                ):  # series has multiple volumes, but are numbered not named
                    return f"{seriesName} - Book {input}"
            elif input[1:].isdigit():  # single title series book has name of -100000
                return seriesName
            else:
                return input
        raise ValueError(input)


class Tag(BaseModel):
    id: int
    title: str | None


class SeriesMetadata(BaseModel):
    summary: str = "No summary!"
    tags: list[Tag]
    webLinks: list[str]

    @field_validator("webLinks", mode="before")
    @classmethod
    def validate_webLinks(cls, input: Any) -> list[str]:
        if input is None:
            return ["about:blank"]
        if isinstance(input, str) and input != "":
            return input.split(";")
        return ["about:blank"]


class Series(BaseModel):
    id: int
    name: str = Field(validation_alias=AliasChoices("localizedName", "name"))
    pages: int
    pagesRead: int
    latestReadDate: datetime

    @computed_field
    @cached_property
    def metadata(self) -> SeriesMetadata:
        resp = client.get(SERIES_METADATA_ENDPOINT, params={"seriesId": self.id})
        return SeriesMetadata.model_validate_json(resp.content)

    @computed_field
    @cached_property
    def volumes(self) -> list[Volume]:
        resp = client.get(SERIES_VOLUMES_ENDPOINT, params={"seriesId": self.id})
        resp = resp.json()
        return [
            Volume.model_validate(k, context={"seriesName": self.name}) for k in resp
        ]

    @computed_field
    @cached_property
    def completed(self) -> bool:
        return self.pagesRead >= self.pages

    @computed_field
    @cached_property
    def completion_progress(self) -> float:
        return self.pagesRead / self.pages


def GetSeries(id: int) -> Series:
    resp = client.get(SERIES_DATA_ENDPOINT + str(id))
    return Series.model_validate_json(resp.content, by_alias=True)


@dataclass
class KavitaFilterStatement:
    comparison: int
    field: int
    value: str

    def GetAsFilterStatement(self) -> dict[str, Any]:
        return self.__dict__


def SearchSeries(sortFields: list[KavitaFilterStatement]) -> list[Series]:
    o = {
        "combination": 1,
        "limitTo": 0,
        "sortOptions": {
            "isAscending": False,
            "sortField": 7,
        },  ## Sort by most recently read (with most recent series at the top)
        "statements": [k.__dict__ for k in sortFields],
    }
    resp = client.post(SERIES_SEARCH_ENDPOINT, json=o)
    assert resp.status_code == 200
    resp = resp.json()
    return [GetSeries(r.get("id")) for r in resp]


def GetOnDeckSeries() -> list[Series]:
    resp = client.post(ON_DECK_ENDPOINT)
    resp = resp.json()
    retVal = []
    for title in resp:
        curSeries = GetSeries(title["id"])
        retVal.append(curSeries)
    return retVal
