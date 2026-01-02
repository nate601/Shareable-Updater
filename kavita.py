from dataclasses import dataclass

import httpx

from setec_secrets import GetVendorSecret

api_key = GetVendorSecret("kavita", "api_key")

ON_DECK_ENDPOINT = "https://kavita.n8.pub/api/Series/on-deck"
AUTH_ENDPOINT = "https://kavita.n8.pub/api/Plugin/authenticate"
SERIES_VOLUMES_ENDPOINT = "https://kavita.n8.pub/api/Series/volumes"
SERIES_METADATA_ENDPOINT = "https://kavita.n8.pub/api/Series/metadata"
SERIES_DATA_ENDPOINT = "https://kavita.n8.pub/api/Series/"
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

    def __init__(self, id: int):
        self.id = id
        resp = httpx.get(SERIES_DATA_ENDPOINT + str(id), headers=HEADERS)
        resp = resp.json()
        self.name = resp.get("name")
        self.pages = resp.get("pages")
        self.pages_read = resp.get("pagesRead")
        self.metadata = self.GetSeriesMetadata()
        self.volumes = self.GetSeriesVolumes() or []

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
            "completed": int(serie.pages) <= int(serie.pages_read),
            "completion_progress": serie.pages_read / serie.pages,
        }
        retVal.append(o)
    return retVal


def GetReadSeries() -> list[Series]: ...


def GetInProgressSeries() -> list[Series]: ...


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
    print(GetOnDeckSeries())
    print("###In Progress###")
    print(GetInProgressSeries())
    print("###Read Series###")
    print(GetReadSeries())
