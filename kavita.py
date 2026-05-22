from KavitaModels import (
    Series,
    Volume,
    KavitaFilterStatement,
    SearchSeries,
    GetOnDeckSeries,
)


def GetSharables():
    series = GetOnDeckSeries()
    retVal = []
    for serie in series:
        o = {
            "name": serie.name,
            "link": serie.metadata.webLinks[0],
            "summary": serie.metadata.summary,
            "completed": serie.completed,
            "completion_progress": serie.completion_progress,
        }
        retVal.append(o)
    return retVal


def GetReadSeries() -> list[Series]:
    return SearchSeries(
        [
            KavitaFilterStatement(1, 20, "98"),  # series with 99% progress or greater
            KavitaFilterStatement(0, 19, "1"),  ## Series in the "Books" collection
        ]
    )


def GetReadVolumes() -> list[dict[str, Volume | Series]]:
    series = GetSeriesWithProgress()
    vol = [{"volume": v, "series": s} for s in series for v in s.volumes if v.completed]
    return vol


def GetSeriesWithProgress() -> list[Series]:
    return SearchSeries(
        [KavitaFilterStatement(1, 20, "0"), KavitaFilterStatement(0, 19, "1")]
    )


if __name__ == "__main__":
    from rich import print

    print("###On Deck###")
    print(GetOnDeckSeries())
    print("###Read Volumes###")
    print(GetReadVolumes())
