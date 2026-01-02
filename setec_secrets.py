import base64
import os

import httpx

server_root = os.getenv("SETEC_SERVER")
assert server_root, "SETEC_SERVER env variable is not set"
client = httpx.Client()
client.headers = {"Sec-X-Tailscale-No-Browsers": "setec"}


def GetVendorSecret(vendor, key) -> str:
    resp = client.request(
        "POST", f"{server_root}/api/get", json={"Name": f"vendor/{vendor}/{key}"}
    )
    assert resp.status_code == 200
    encoded_val = resp.json().get("Value")
    return base64.b64decode(encoded_val).decode("ascii")


def SetVendorSecret(vendor: str, key: str, new_val: str) -> str:
    resp = client.request(
        "POST",
        f"{server_root}/api/get",
        json={"Name": f"vendor/{vendor}/{key}", "Value": new_val},
    )
    print(resp.status_code)
    assert resp.status_code == 200
    return resp.content.decode("ascii")
