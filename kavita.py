from dataclasses import dataclass
from datetime import datetime
from pprint import pprint

import httpx

from setec_secrets import GetVendorSecret

api_key = GetVendorSecret("kavita", "api_key")

ON_DECK_ENDPOINT = "https://kavita.n8.pub/api/Series/on-deck"
AUTH_ENDPOINT = "https://kavita.n8.pub/api/Plugin/authenticate"
SERIES_VOLUMES_ENDPOINT = "https://kavita.n8.pub/api/Series/volumes"
SERIES_METADATA_ENDPOINT = "https://kavita.n8.pub/api/Series/metadata"
SERIES_DATA_ENDPOINT = "https://kavita.n8.pub/api/Series/"
SERIES_SEARCH_ENDPOINT = "https://kavita.n8.pub/api/Series/v2"
# TODO: update python and use template literal


def GetToken():
    o = {"apiKey": api_key, "pluginName": "sharablesUpdater"}
    resp = httpx.post(AUTH_ENDPOINT, params=o)
    resp = resp.json()
    assert resp["token"], "Unable to fetch token"
    return resp["token"]


@dataclass
class Volume:
    id: int
    name: str
    pages: int
    pages_read: int
    completed: bool
    word_count: int
    last_read_date: datetime


@dataclass
class SeriesMetadata:
    summary: str | None
    tags: list[str]
    link: str | None


@dataclass
class Series:
    id: int
    name: str
    pages: int
    pages_read: int
    metadata: SeriesMetadata | None
    volumes: list[Volume]
    last_read_date: datetime

    def __init__(self, id: int):
        self.id = id
        resp = httpx.get(SERIES_DATA_ENDPOINT + str(id), headers=HEADERS)
        resp = resp.json()
        self.name = resp.get("localizedName") or resp.get("name")
        self.pages = resp.get("pages")
        self.pages_read = resp.get("pagesRead")
        self.metadata = self.GetSeriesMetadata()
        self.volumes = self.GetSeriesVolumes() or []
        self.last_read_date = datetime.fromisoformat(resp.get("latestReadDate"))

    def GetSeriesMetadata(self):
        resp = httpx.get(
            SERIES_METADATA_ENDPOINT, headers=HEADERS, params={"seriesId": self.id}
        )
        metadataResp = resp.json()
        return SeriesMetadata(
            summary=metadataResp.get("summary") or "No summary",
            link=metadataResp.get("webLinks", "about:blank").split(",")[0] or None,
            tags=[tag.get("title") for tag in metadataResp.get("tags")] or [],
        )

    def GetSeriesVolumes(self) -> list[Volume]:
        resp = httpx.get(
            SERIES_VOLUMES_ENDPOINT, headers=HEADERS, params={"seriesId": self.id}
        )
        booksResponse = resp.json()
        volumes = []
        for book in booksResponse:
            bookName = book.get("name")
            if bookName.isdigit():
                if len(booksResponse) > 1:
                    bookName = f"{self.name} - Book {bookName}"
                else:
                    bookName = self.name
            elif bookName[1:].isdigit():
                bookName = self.name
            lrds = [
                datetime.fromisoformat(c.get("lastReadingProgress"))
                for c in book.get("chapters")
            ]
            lrds.sort()
            curVol = Volume(
                id=book["id"],
                name=bookName,
                pages=book["pages"],
                pages_read=book["pagesRead"],
                completed=book["pagesRead"] >= book["pages"],
                word_count=book["wordCount"],
                last_read_date=max(lrds),
            )
            volumes.append(curVol)
        return volumes


def GetSharables():
    series = GetOnDeckSeries()
    retVal = []
    for serie in series:
        o = {
            "name": serie.name,
            "link": serie.GetSeriesMetadata().link,
            "summary": serie.GetSeriesMetadata().summary,
            "completed": int(serie.pages) <= int(serie.pages_read),
            "completion_progress": serie.pages_read / serie.pages,
        }
        retVal.append(o)
    return retVal


def GetReadSeries() -> list[Series]:
    fss = [
        FilterStatement(1, 20, "98"),  # series with 99% progress or greater
        FilterStatement(0, 19, "1"),  ## Series in the "Books" collection
    ]
    return SearchSeries(fss)


def GetReadVolumes() -> list[Volume]:
    series = GetSeriesWithProgress()
    vol = sorted(
        [v for s in series for v in s.volumes if v.completed],
        key=lambda p: p.name,
    )
    return sorted(vol, key=lambda p: p.last_read_date.date(), reverse=True)


def GetSeriesWithProgress() -> list[Series]:
    fss = [
        FilterStatement(1, 20, "0"),  ## Series with >= 1 percent of progress
        FilterStatement(0, 19, "1"),  ## Series in the "Books" collection
    ]
    return SearchSeries(fss)


@dataclass
class FilterStatement:
    comparison: int
    field: int
    value: str


def SearchSeries(sortFields: list[FilterStatement]) -> list[Series]:
    o = {
        "combination": 1,
        "limitTo": 0,
        "sortOptions": {
            "isAscending": False,
            "sortField": 7,
        },  ## Sort by most recently read (with most recent series at the top)
        "statements": [k.__dict__ for k in sortFields],
    }
    resp = httpx.post(SERIES_SEARCH_ENDPOINT, headers=HEADERS, json=o)
    assert resp.status_code == 200
    resp = resp.json()
    return [Series(r.get("id")) for r in resp]


def GetOnDeckSeries() -> list[Series]:
    resp = httpx.post(ON_DECK_ENDPOINT, headers=HEADERS)
    resp = resp.json()
    retVal = []
    for title in resp:
        curSeries = Series(title["id"])
        retVal.append(curSeries)

    return retVal


TOKEN = GetToken()
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

if __name__ == "__main__":
    print("###On Deck###")
    pprint(GetOnDeckSeries())
    print("###Read Volumes###")
    pprint(GetReadVolumes())
