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
            # TODO: tests on different messages
            cls(u["update_id"], u["message"].get("caption") or u["message"]["text"])
            for u in value
            if "message" in u
        ]


@define
class Telegram:
    netloc: str
    token: str

    def fetch_updates(self, limit: int = 1) -> List[TelegramUpdate]:
        response = requests.get(
            url=f"{self.netloc}/bot{self.token}/getUpdates?limit={limit}",
            headers={
                "Content-Type": "application/json",
            },
        )
        return TelegramUpdate.from_api_response(response.json()["result"])


@define
class Fibery:
    netloc: str
    token: str

    @property
    def headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.token}",
        }

    def create_new_material_from_telegram_update(self, msg: TelegramUpdate) -> None:
        # check if we don't have Sync ID corresponding to update_id
        response = requests.post(
            url=urljoin(self.netloc, "/api/commands"),
            headers=self.headers,
            json=[
                {
                    "command": "fibery.entity/query",
                    "args": {
                        "query": {
                            "q/from": "Knowledge Management/Material",
                            "q/select": ["fibery/id"],
                            "q/where": [
                                "=",
                                ["Knowledge Management/Sync ID"],
                                "$id",
                            ],
                            "q/limit": 1,
                        },
                        "params": {"$id": f"tg:{msg.update_id}"},
                    },
                }
            ],
        )
        # print(response.json())
        if len(response.json()[0]["result"]) > 0:
            return

        # create new Material
        response = requests.post(
            url=urljoin(self.netloc, "/api/commands"),
            headers=self.headers,
            json=[
                {
                    "command": "fibery.entity/create",
                    "args": {
                        "type": "Knowledge Management/Material",
                        "entity": {
                            "fibery/id": str(uuid4()),
                            "Knowledge Management/Sync ID": f"tg:{msg.update_id}",
                        },
                    },
                }
            ],
        )
        # print(response.json())
        material_id = response.json()[0]["result"]["fibery/id"]
        # get document secret
        response = requests.post(
            url=urljoin(self.netloc, "/api/commands"),
            headers=self.headers,
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
            headers=self.headers,
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
@click.option("-n", type=click.INT, default=1)
def main(secret: str, n: int) -> None:
    config = Config(secret)
    updates = Telegram(**config.secrets("telegram")).fetch_updates(limit=n)
    fibery = Fibery(**config.secrets("fibery"))
    for update in updates:
        print(update.update_id)
        fibery.create_new_material_from_telegram_update(update)


if __name__ == "__main__":
    main()
