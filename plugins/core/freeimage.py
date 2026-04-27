import os

import requests
from dotenv import load_dotenv


FREEIMAGE_API_URL = "https://freeimage.host/api/1/upload"


class FreeimageHost:
    def __init__(self, client=None):
        self.client = client

    def upload(self, path, title=None, description=None):
        load_dotenv(".env", override=True)
        if not os.path.isfile(path):
            raise FileNotFoundError(path)

        api_key = os.getenv("FREEIMAGE_API_KEY") or None
        if not api_key:
            raise RuntimeError("FREEIMAGE_API_KEY is not configured in .env")

        payload = {
            "key": api_key,
            "action": "upload",
            "format": "json",
        }
        if title:
            payload["title"] = title
        if description:
            payload["description"] = description

        with open(path, "rb") as fp:
            response = requests.post(
                FREEIMAGE_API_URL,
                data=payload,
                files={"source": fp},
                timeout=60,
            )
        response.raise_for_status()
        data = response.json()
        if data.get("status_code") != 200:
            raise RuntimeError(data)
        return data


class freeimage(FreeimageHost):
    pass
