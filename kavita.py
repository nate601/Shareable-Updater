import os
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv

envFile = "./ENV/kavita"
load_dotenv(envFile)
api_key = os.getenv("KAVITA_API_KEY")
assert api_key, "No API key.   Check ENV files"

ON_DECK_ENDPOINT = "https://kavita.n8.pub/api/Series/on-deck"
AUTH_ENDPOINT = "https://kavita.n8.pub/api/Plugin/authenticate"
SERIES_VOLUMES_ENDPOINT = "https://kavita.n8.pub/api/Series/volumes"
SERIES_METADATA_ENDPOINT = "https://kavita.n8.pub/api/Series/metadata"


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

    def GetSeriesMetadata(self):
        resp = httpx.get(
            SERIES_METADATA_ENDPOINT, headers=HEADERS, params={"seriesId": self.id}
        )
        metadataResp = resp.json()
        return SeriesMetadata(
            summary=metadataResp.get("summary"),
            link=metadataResp.get("webLinks", "about:blank").split(",")[0],
            tags=[tag.get("title") for tag in metadataResp.get("tags")],
        )

    def GetSeriesVolumes(self) -> list[Volume]:
        resp = httpx.get(
            SERIES_VOLUMES_ENDPOINT, headers=HEADERS, params={"seriesId": self.id}
        )
        booksResponse = resp.json()
        volumes = []
        for book in booksResponse:
            curVol = Volume(
                id=book["id"],
                name=book["name"],
                pages=book["pages"],
                pages_read=book["pagesRead"],
                completed=book["pagesRead"] >= book["pages"],
                word_count=book["wordCount"],
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
            # "volumes": serie.GetSeriesVolumes(),
            "completed": serie.pages <= serie.pages_read,
            "completion_progress": serie.pages_read / serie.pages,
        }
        retVal.append(o)
    return retVal


def GetOnDeckSeries() -> list[Series]:
    resp = httpx.post(ON_DECK_ENDPOINT, headers=HEADERS)
    resp = resp.json()
    retVal = []
    for title in resp:
        # o = {
        #
        # }
        curSeries = Series(
            id=title["id"],
            name=title["name"],
            pages=title.get("pages"),
            pages_read=title.get("pagesRead"),
        )
        retVal.append(curSeries)
        # o["link"] = curSeries.GetSeriesMetadata().link
        # o["name"] = curSeries.name
        # o["volumes"] = curSeries.GetSeriesVolumes()

    return retVal


TOKEN = GetToken()
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

if __name__ == "__main__":
    print(GetSharables())
