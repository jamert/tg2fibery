#!/usr/bin/env python
import configparser
from typing import List
from urllib.parse import urljoin
from uuid import uuid4

import click
import requests
from attr import define


@define
class TelegramUpdate:
    update_id: int
    content: str  # message->text

    @classmethod
    def from_api_response(cls, value: list) -> List["TelegramUpdate"]:
        return [
            cls(u["update_id"], u["message"]["text"]) for u in value if "message" in u
        ]


@define
class Telegram:
    netloc: str
    token: str

    def fetch_updates(self) -> List[TelegramUpdate]:
        response = requests.get(
            url=f"{self.netloc}/bot{self.token}/getUpdates?limit=1",
            headers={
                "Content-Type": "application/json",
            },
        )
        return TelegramUpdate.from_api_response(response.json()["result"])


@define
class Fibery:
    netloc: str
    token: str

    def create_new_material_from_telegram_update(self, msg: TelegramUpdate) -> None:
        # create new Material
        response = requests.post(
            url=urljoin(self.netloc, "/api/commands"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Token {self.token}",
            },
            json=[
                {
                    "command": "fibery.entity/create",
                    "args": {
                        "type": "Knowledge Management/Material",
                        "entity": {"fibery/id": str(uuid4())},
                    },
                }
            ],
        )
        # print(response.json())
        material_id = response.json()[0]["result"]["fibery/id"]
        # get document secret
        response = requests.post(
            url=urljoin(self.netloc, "/api/commands"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Token {self.token}",
            },
            json=[
                {
                    "command": "fibery.entity/query",
                    "args": {
                        "query": {
                            "q/from": "Knowledge Management/Material",
                            "q/select": [
                                "fibery/id",
                                {
                                    "Knowledge Management/Praise": [
                                        "Collaboration~Documents/secret"
                                    ]
                                },
                            ],
                            "q/where": ["=", ["fibery/id"], "$id"],
                            "q/limit": 1,
                        },
                        "params": {"$id": material_id},
                    },
                }
            ],
        )
        # print(response.json())
        secret = response.json()[0]["result"][0]["Knowledge Management/Praise"][
            "Collaboration~Documents/secret"
        ]
        # update Praise
        response = requests.put(
            url=urljoin(self.netloc, f"/api/documents/{secret}?format=md"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Token {self.token}",
            },
            json={"content": msg.content},
        )
        # print(response.status_code)


class Config:
    def __init__(self, filename: str) -> None:
        self.parser = configparser.ConfigParser()
        self.parser.read(filename)

    def secrets(self, section: str) -> dict:
        return dict(self.parser[section])


@click.command
@click.option(
    "--secret", type=click.Path(exists=True, dir_okay=False), default="secrets.ini"
)
def main(secret: str) -> None:
    config = Config(secret)
    updates = Telegram(**config.secrets("telegram")).fetch_updates()
    fibery = Fibery(**config.secrets("fibery"))
    for update in updates:
        # print(update)
        fibery.create_new_material_from_telegram_update(update)


if __name__ == "__main__":
    main()
