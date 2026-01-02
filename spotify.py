import base64
import os
import urllib.parse
from typing import Literal

import httpx

# from dotenv import dotenv_values, load_dotenv, set_key
from setec_secrets import GetVendorSecret, SetVendorSecret


def GetUserAuthSecret():
    if not env_user_auth_secret:
        o = {
            "client_id": env_client_id,
            "response_type": "code",
            "scope": "user-top-read",
            "redirect_uri": "http://127.0.0.1:3000",
        }
        baseurl = "https://accounts.spotify.com/authorize?"
        print("Please go to the below URL to obtain user-top-read scope grant.")
        print(baseurl + urllib.parse.urlencode(o))
        assert False
    return env_user_auth_secret


def RequestAccessToken(client_id: str, client_secret: str, auth_code: str) -> str:
    return RefreshAccessToken(
        GetVendorSecret("spotify", "refresh_token"), client_id, client_secret
    )


def RefreshAccessToken(refresh_token: str, client_id: str, client_secret: str) -> str:
    o = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    k = base64.b64encode(bytes(f"{client_id}:{client_secret}", "utf-8")).decode()
    h = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {k}",
    }
    baseurl = "https://accounts.spotify.com/api/token"
    resp = httpx.post(baseurl, data=o, headers=h)
    print(resp.status_code)
    print(resp.content)
    assert resp.status_code == 200
    resp = resp.json()
    if "refresh_token" in resp:
        SetRefreshToken(resp["refresh_token"])
    return resp["access_token"]


def SetRefreshToken(newRefreshToken: str):
    print("New refresh token from Spotify")
    SetVendorSecret("spotify", "refresh_token", newRefreshToken)


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


env_client_id = GetVendorSecret("spotify", "client_id")
env_client_secret = GetVendorSecret("spotify", "client_secret")
env_user_auth_secret = GetVendorSecret("spotify", "user_auth_secret")
assert env_client_id
assert env_client_secret
assert env_user_auth_secret


def GetSharables():
    access_token = RequestAccessToken(
        env_client_id, env_client_secret, env_user_auth_secret
    )
    return GetTopTracks(access_token, limit=3)


if __name__ == "__main__":
    access_token = RequestAccessToken(
        env_client_id, env_client_secret, env_user_auth_secret
    )
    retVal = GetTopTracks(access_token)
    print(retVal)
