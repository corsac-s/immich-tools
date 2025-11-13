#! /usr/bin/python3

import configparser
import datetime
import os
import requests
from urllib.parse import urljoin
from webdav3.client import Client

def load_config():
    """Load Immich configuration from immich.ini or environment variables."""
    config = configparser.ConfigParser()
    ini_path = os.path.join(os.path.dirname(__file__), "immich.ini")

    if not os.path.exists(ini_path):
        raise FileNotFoundError(f"Config file not found: {ini_path}")

    config.read(ini_path)

    IMMICH_URL = config.get("immich", "url", fallback=os.environ.get("IMMICH_URL", "http://localhost:2283"))
    API_KEY = config.get("immich", "api_key", fallback=os.environ.get("IMMICH_API_KEY"))

    options = {}
    options["webdav_hostname"] = config.get("nextcloud", "hostname", fallback=os.environ.get("NEXTCLOUD_URL", "https://nextcloud.app/remote.php/dav/photos/<user>/albums/"))
    options["webdav_login"] = config.get("nextcloud", "login", fallback=os.environ.get("NEXTCLOUD_LOGIN", "<user>"))
    options["webdav_password"] = config.get("nextcloud", "password", fallback=os.environ.get("NEXTCLOUD_PASSWORD", "password"))

    if not API_KEY or len(options) == 0:
        sys.exit("Error: Configuration not set. Use immich.ini or environment variable.")

    return IMMICH_URL, API_KEY, options

def get_albums(IMMICH_URL, API_KEY):
    """ Get albums from Immich"""
    endpoint = urljoin(IMMICH_URL, "api/albums")
    HEADERS = {
        "Accept": "application/json",
        "x-api-key": API_KEY,
    }
    resp = requests.get(endpoint, headers=HEADERS)
    resp.raise_for_status()
    json = resp.json()
    return json

def create_album_im(IMMICH_URL, API_KEY, name):
    """ Create album in Immich"""
    endpoint = urljoin(IMMICH_URL, "api/albums")
    HEADERS = {
        "Accept": "application/json",
        "x-api-key": API_KEY,
    }
    payload = { "albumName": name, }
    resp = requests.post(endpoint, headers=HEADERS, json=payload)
    resp.raise_for_status()
    json = resp.json()
    return json

def get_album_im(IMMICH_URL, API_KEY, album):
    endpoint = urljoin(IMMICH_URL, "api/albums/%s" % album)
    HEADERS = {
        "Accept": "application/json",
        "x-api-key": API_KEY,
    }
    resp = requests.get(endpoint, headers=HEADERS)
    resp.raise_for_status()
    json = resp.json()
    return json


def add_assets_to_album(IMMICH_URL, API_KEY, assets, album):
    """ Add an asset to an album in Immich"""
    endpoint = urljoin(IMMICH_URL, "api/albums/%s/assets" % album["id"])
    HEADERS = {
        "Accept": "application/json",
        "x-api-key": API_KEY,
    }
    payload = { "ids": assets, }
    resp = requests.put(endpoint, headers=HEADERS, json=payload)
    resp.raise_for_status()
    json = resp.json()
    return json

def get_asset(IMMICH_URL, API_KEY, name, time):
    """Fetch asset from Immich API."""
    endpoint = urljoin(IMMICH_URL, "api/search/metadata")
    HEADERS = {
        "Accept": "application/json",
        "x-api-key": API_KEY,
    }
    # Get a 2 seconds window between the modified time
    before = time + datetime.timedelta(seconds=1)
    after  = time - datetime.timedelta(seconds=1)
    payload = {
            "originalFileName": name,
            "takenAfter": after.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "takenBefore": before.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            }
    resp = requests.post(endpoint, headers=HEADERS, json=payload)
    resp.raise_for_status()
    json = resp.json()
    if json["assets"]["count"] == 0:
        # no result: retry with a larger window
        before = time + datetime.timedelta(weeks=3)
        after  = time - datetime.timedelta(weeks=3)
        payload = {
                "originalFileName": name,
                "takenAfter": after.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "takenBefore": before.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                }
        resp = requests.post(endpoint, headers=HEADERS, json=payload)
        resp.raise_for_status()
        json = resp.json()
        #if json["assets"]["count"] == 0: print("%s (%s)" % (payload, time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")))
    return json

if __name__ == "__main__":
    IMMICH_URL, IMMICH_API_KEY, options = load_config()
    client = Client(options)
    
    albums_nc = client.list()
    albums_im = get_albums(IMMICH_URL, IMMICH_API_KEY)
    exit
    
    for album in albums_nc[1:]:
        album_nc = album[:-1]
        album_im = next((item for item in albums_im if item['albumName'] == album_nc), None)
        if not album_im:
            print(" No match found, creating album (%s)" % album_nc)
            album_im = create_album_im(IMMICH_URL, IMMICH_API_KEY, album_nc)

        photos = client.list(album, get_info=True)
        print("%2d/%d: %s (%d)" % (albums_nc.index(album), len(albums_nc[1:]), album_nc, len(photos[1:])))

        ids = []
        for photo in photos[1:]:
            id_nc, name = os.path.basename(photo["path"]).split("-", 1)
            time = datetime.datetime.strptime(photo["modified"], "%a, %d %b %Y %H:%M:%S %Z")
            assets = get_asset(IMMICH_URL, IMMICH_API_KEY, name, time)["assets"]
            # nothing found, maybe we don't really have it (shared asset in Nextcloud?)
            if assets["count"] == 0:
                print(" No match found for %s - %s" % (album_nc, name))
            else:
                # if one or more assets, identify the non duplicate one
                #id = assets["items"][0]["duplicateId"] or assets["items"][0]["id"]
                id = assets["items"][0]["id"]
                ids.append(id)

        # add assets to the album
        ret = add_assets_to_album(IMMICH_URL, IMMICH_API_KEY, ids, album_im)
        res = [result for result in ret if result["success"] == False and result["error"] != "duplicate"]
        if len(res): print(res)
