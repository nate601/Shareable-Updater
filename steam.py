import httpx

from setec_secrets import GetVendorSecret

api_key = GetVendorSecret("steam", "steam_web_api_key")
steamid = GetVendorSecret("steam", "steamid")
assert api_key
assert steamid


def GetLinkFromAppId(appId: int):
    return f"https://store.steampowered.com/app/{appId}"


# Gets sharables, but this time using the last played time instead of using Steam's last played.  This means we can go back further than 2 wks.
def GetSharables():
    baseurl = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
    o = {"key": api_key, "steamid": steamid, "include_appinfo": True}
    resp = httpx.get(baseurl, params=o)
    resp = resp.json()
    games = resp["response"]["games"]
    k = sorted(games, key=lambda game: game["rtime_last_played"], reverse=True)[:3]
    retVal = []
    for game in k:
        retVal.append({"name": game["name"], "link": GetLinkFromAppId(game["appid"])})

    return retVal


if __name__ == "__main__":
    print(GetSharables())
