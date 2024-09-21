import os
from typing import Literal
import urllib.parse
import base64
from dotenv import load_dotenv, dotenv_values, set_key
import httpx


def GetUserAuthSecret():
    if not env_user_auth_secret:
        o = {
            "client_id": env_client_id,
            "response_type": "code",
            "scope": "user-top-read",
            "redirect_uri": "http://localhost:3000",
        }
        baseurl = "https://accounts.spotify.com/authorize?"
        print("Please go to the below URL to obtain user-top-read scope grant.")
        print(baseurl + urllib.parse.urlencode(o))
        assert False
    return env_user_auth_secret


def RequestAccessToken(client_id: str, client_secret: str, auth_code: str) -> str:
    if os.getenv("refresh_token"):
        return RefreshAccessToken(
            os.getenv("refresh_token") or "", client_id, client_secret
        )
    baseurl = "https://accounts.spotify.com/api/token"
    o = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": "http://localhost:3000",
    }
    head = {
        "content-type": "application/x-www-form-urlencoded",
        "Authorization": "Basic "
        + base64.b64encode(bytes(f"{client_id}:{client_secret}", "utf-8")).decode(),
    }
    resp = httpx.post(baseurl, data=o, headers=head)
    # print(resp.status_code)
    # print(resp.content)
    resp = resp.json()
    assert resp["access_token"]
    refresh_token = resp["refresh_token"]
    SetRefreshToken(refresh_token)
    return resp["access_token"]


def RefreshAccessToken(rfsh_token: str, client_id: str, client_secret: str) -> str:
    o = {"grant_type": "refresh_token", "refresh_token": rfsh_token}
    k = base64.b64encode(bytes(f"{client_id}:{client_secret}", "utf-8")).decode()
    h = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {k}",
    }
    baseurl = "https://accounts.spotify.com/api/token"
    resp = httpx.post(baseurl, data=o, headers=h)
    # print(resp.status_code)
    # print(resp)
    assert resp.status_code == 200
    resp = resp.json()
    # print(resp)
    if "refresh_token" in resp:
        SetRefreshToken(resp["refresh_token"])
    return resp["access_token"]


def SetRefreshToken(newwRefreshToken: str):
    set_key("./ENV/spotify", "refresh_token", newwRefreshToken)


def GetTopTracks(
    access_token: str,
    time_range: Literal["long_term", "medium_term", "short_term"] = "short_term",
    limit: int = 2,
    offset: int = 0,
):
    tracks_endpoint = "https://api.spotify.com/v1/me/top/tracks"
    o = {"type": "tracks", "time_range": time_range, "limit": limit, "offset": offset}
    head = {"Authorization": f"Bearer {access_token}"}
    resp = httpx.get(tracks_endpoint, params=o, headers=head)
    resp = resp.json()
    ret_val = []
    for i in resp["items"]:
        ret_val.append(
            {
                "name": f"{i['name']} by {i['artists'][0]['name']}",
                "link": f"{i['external_urls']['spotify']}",
            }
        )
    return ret_val


load_dotenv("./ENV/spotify")
env_client_id = os.getenv("client_id")
env_client_secret = os.getenv("client_secret")
env_user_auth_secret = os.getenv("user_auth_secret")


def GetSharables():
    assert env_client_id
    assert env_client_secret

    user_auth = GetUserAuthSecret()
    access_token = RequestAccessToken(env_client_id, env_client_secret, user_auth)
    return GetTopTracks(access_token, limit=3)


if __name__ == "__main__":
    load_dotenv("./ENV/spotify")
    env_client_id = os.getenv("client_id")
    env_client_secret = os.getenv("client_secret")
    assert env_client_id
    assert env_client_secret
    env_user_auth_secret = os.getenv("user_auth_secret")

    user_auth = GetUserAuthSecret()
    access_token = RequestAccessToken(env_client_id, env_client_secret, user_auth)
    retVal = GetTopTracks(access_token)
    print(retVal)
