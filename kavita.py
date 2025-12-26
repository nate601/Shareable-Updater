import os

import httpx
from dotenv import load_dotenv

envFile = "./ENV/kavita"
load_dotenv(envFile)
api_key = os.getenv("KAVITA_API_KEY")
assert api_key, "No API key.   Check ENV files"

def GetToken():
    auth_url = "https://kavita.n8.pub/api/Plugin/authenticate"
    o = {"apiKey": api_key, "pluginName" : "sharablesUpdater"}
    resp = httpx.post(auth_url, params=o)
    resp = resp.json()
    assert resp["token"], "Unable to fetch token"
    return resp["token"]

def GetSharables():
    token = GetToken()
    # baseurl = "https://kavita.n8.pub/api/Series/currently-reading"
    baseurl = "https://kavita.n8.pub/api/Series/on-deck"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    resp = httpx.post(baseurl, headers=headers)
    resp = resp.json()
    retVal = []
    for title in resp:
        retVal.append({"name":title["name"], "link": "about:blank"})
    return retVal


if __name__ == "__main__":
   print(GetSharables())
